#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

export RESEARCH_DIR="$TMP/research"
export WORKSPACE_DIR="$TMP/workspace"
mkdir -p "$WORKSPACE_DIR"

INIT="$ROOT_DIR/research-init"
GOAL="$ROOT_DIR/research-goal"
WATCH="$ROOT_DIR/research-watch"
chmod +x "$INIT" "$GOAL" "$WATCH"

"$INIT" >/dev/null
gid=$("$GOAL" add "Watch test goal" --priority=2)
"$GOAL" plan "$gid"

out=$("$WATCH" --all 2>&1)
if echo "$out" | grep -q "Found 3 pending"; then
  echo "PASS --all lists 3 pending steps"
else
  echo "FAIL --all pending count"; echo "$out"; exit 1
fi

MOCK_DR="$TMP/mock-deep-research"
cat > "$MOCK_DR" << 'MDR'
#!/usr/bin/env bash
set -euo pipefail
GOAL=""
STEP=""
QUERY=""
OUT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --goal=*) GOAL="${1#*=}" ;;
    --mark-step=*) STEP="${1#*=}" ;;
    --output=*) OUT="${1#*=}" ;;
    --*) ;;
    *) QUERY="$1" ;;
  esac
  shift
done
echo "MOCK_CALL goal=$GOAL step=$STEP query=$QUERY" >> "${MOCK_LOG:-/dev/null}"
RUN_ID=$(date -u +%Y-%m-%dT%H-%M-%S)
source "${MOCK_STATE_LIB:?}"
research_ensure_dirs
ARTIFACT=$(jq -n \
  --arg run_id "$RUN_ID" --arg goal_id "$GOAL" --arg query "$QUERY" --arg step_id "$STEP" \
  --argjson stages 4 --argjson cost 0.07 --argjson sources 12 \
  --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{run_id:$run_id,goal_id:$goal_id,question:$query,step_id:$step_id,stages_run:$stages,cost:$cost,sources_found:$sources,timestamp:$ts,failed:false,duration_s:10,workdir:""}')
record_run_for_goal "$GOAL" "$RUN_ID" "$ARTIFACT"
goals_update_field "$GOAL" '.answered_steps += 1'
echo "ok" > "$OUT"
MDR
chmod +x "$MOCK_DR"

export MOCK_LOG="$TMP/mock.log"
export MOCK_STATE_LIB="$ROOT_DIR/lib/research-state.sh"
export RESEARCH_DIR WORKSPACE_DIR DEEP_RESEARCH_BIN="$MOCK_DR"

"$WATCH" --all >/dev/null
if [ ! -f "$MOCK_LOG" ]; then
  echo "PASS --all dry-run does not invoke deep-research"
else
  echo "FAIL dry-run invoked mock"; cat "$MOCK_LOG"; exit 1
fi

: > "$MOCK_LOG"
"$WATCH" --all --exec >/dev/null
calls=$(wc -l < "$MOCK_LOG")
if [ "$calls" -eq 3 ]; then
  echo "PASS --exec invokes mock 3 times"
else
  echo "FAIL --exec call count: $calls"; cat "$MOCK_LOG"; exit 1
fi

if grep -q "mark-step=step-1" <(tr ' ' '\n' < "$MOCK_LOG") || grep -q "step=step-1" "$MOCK_LOG"; then
  echo "PASS mock received step-1"
else
  echo "FAIL mock missing step-1"; cat "$MOCK_LOG"; exit 1
fi

# Reset and test completed step exclusion
rm -f "$MOCK_LOG"
"$INIT" --reset >/dev/null
gid=$("$GOAL" add "Watch exclude test" --priority=2)
"$GOAL" plan "$gid"
RUN_ID="2026-06-18T10-00-00"
jq -n \
  --arg run_id "$RUN_ID" --arg goal_id "$gid" --arg step_id "step-1" \
  --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{run_id:$run_id,goal_id:$goal_id,step_id:$step_id,stages_run:4,cost:0.05,sources_found:5,timestamp:$ts,failed:false,duration_s:5,question:"done",workdir:""}' \
  > "$RESEARCH_DIR/runs/${RUN_ID}.json"

: > "$MOCK_LOG"
"$WATCH" --all --exec >/dev/null
calls=$(wc -l < "$MOCK_LOG")
if [ "$calls" -eq 2 ]; then
  echo "PASS completed step-1 excluded (2 invocations)"
else
  echo "FAIL exclusion call count: $calls"; exit 1
fi

# --due skip future
"$INIT" --reset >/dev/null
gid=$("$GOAL" add "Due skip test" --priority=2)
"$GOAL" plan "$gid"
future=$(date -u -d "+5 hours" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v+5H +%Y-%m-%dT%H:%M:%SZ)
jq -n --arg gid "$gid" --arg nr "$future" \
  '{($gid): {
    "step-1": {"next_run": $nr, "last_attempt": null, "last_status": null},
    "step-2": {"next_run": $nr, "last_attempt": null, "last_status": null},
    "step-3": {"next_run": $nr, "last_attempt": null, "last_status": null}
  }}' \
  > "$RESEARCH_DIR/watch-state.json"

out=$("$WATCH" --due 2>&1)
if echo "$out" | grep -q "No pending"; then
  echo "PASS --due skips future next_run"
else
  echo "FAIL --due should skip future"; echo "$out"; exit 1
fi

# --due include overdue
"$INIT" --reset >/dev/null
gid=$("$GOAL" add "Due overdue test" --priority=2)
"$GOAL" plan "$gid"
past=$(date -u -d "-1 hour" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-1H +%Y-%m-%dT%H:%M:%SZ)
jq -n --arg gid "$gid" --arg nr "$past" \
  '{($gid): {"step-1": {"next_run": $nr, "last_attempt": null, "last_status": "failed"}}}' \
  > "$RESEARCH_DIR/watch-state.json"

out=$("$WATCH" --due 2>&1)
if echo "$out" | grep -q "Found 3 pending"; then
  echo "PASS --due includes overdue step-1 (all 3 pending)"
else
  echo "FAIL --due overdue"; echo "$out"; exit 1
fi

# Failure handling
"$INIT" --reset >/dev/null
FAIL_DR="$TMP/fail-deep-research"
cat > "$FAIL_DR" << 'FDR'
#!/usr/bin/env bash
echo "MOCK_FAIL" >> "${MOCK_LOG}"
exit 1
FDR
chmod +x "$FAIL_DR"
export DEEP_RESEARCH_BIN="$FAIL_DR"
"$INIT" --reset >/dev/null
gid=$("$GOAL" add "Fail test" --priority=2)
"$GOAL" plan "$gid"
: > "$MOCK_LOG"
set +e
"$WATCH" --all --exec >/dev/null 2>&1
code=$?
set -e
if [ "$code" -eq 1 ]; then
  echo "PASS watch exits 1 on failures"
else
  echo "FAIL expected exit 1 got $code"; exit 1
fi
if [ -f "$RESEARCH_DIR/watch.log" ] && grep -q "FAIL" "$RESEARCH_DIR/watch.log"; then
  echo "PASS watch.log records failure"
else
  echo "FAIL watch.log missing FAIL"; exit 1
fi

# --goal filter
export DEEP_RESEARCH_BIN="$MOCK_DR"
"$INIT" --reset >/dev/null
g1=$("$GOAL" add "Goal one" --priority=2)
g2=$("$GOAL" add "Goal two" --priority=2)
"$GOAL" plan "$g1"
"$GOAL" plan "$g2"
: > "$MOCK_LOG"
"$WATCH" --goal="$g1" --all --exec >/dev/null
calls=$(wc -l < "$MOCK_LOG")
if [ "$calls" -eq 3 ]; then
  echo "PASS --goal filter runs only target goal"
else
  echo "FAIL --goal filter count: $calls"; exit 1
fi

echo "All research-watch tests passed"
exit 0