#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

export RESEARCH_DIR="$TMP/research"
export WORKSPACE_DIR="$TMP/workspace"
mkdir -p "$WORKSPACE_DIR"

TESTBIN="$TMP/testbin"
mkdir -p "$TESTBIN/lib"
WSROOT="$(dirname "$ROOT_DIR")"
cp "$WSROOT/skills/deep-research/bin/deep-research" "$TESTBIN/deep-research"
cp "$WSROOT/skills/deep-research/lib/retry.sh" "$WSROOT/skills/deep-research/lib/fallback.sh" "$WSROOT/skills/deep-research/lib/research-state.sh" "$TESTBIN/lib/"
cp "$WSROOT/skills/deep-research/bin/research-init" "$WSROOT/skills/deep-research/bin/research-goal" "$WSROOT/skills/deep-research/bin/research-status" "$TESTBIN/"
chmod +x "$TESTBIN"/* "$TESTBIN/lib/"* "$TESTBIN/deep-research"

cat > "$TESTBIN/exa-search" << 'MEXA'
#!/usr/bin/env bash
COST="${MOCK_COST:-0.007}"
echo '{"provider":"exa","results":[{"title":"Mock Exa","url":"https://mock.example.com/a","highlights":["hl1"]}],"costDollars":{"total":'"$COST"'}}'
MEXA
chmod +x "$TESTBIN/exa-search"

cat > "$TESTBIN/serper-search" << 'MSERP'
#!/usr/bin/env bash
echo '{"organic":[{"title":"Mock Serper","link":"https://mock.example.com/a","snippet":"snippet here"}]}'
MSERP
chmod +x "$TESTBIN/serper-search"

cat > "$TESTBIN/research-decompose" << 'MDECOMP'
#!/usr/bin/env bash
echo '[{"query":"mock deep sub","type":"deep","max_results":3,"rationale":"test","output_schema":null}]'
MDECOMP
chmod +x "$TESTBIN/research-decompose"

# Dummies for tools called by deep-research
cat > "$TESTBIN/source-score" << 'MSCORE'
#!/usr/bin/env bash
echo '{"credibility":3}'
MSCORE
chmod +x "$TESTBIN/source-score"

cat > "$TESTBIN/report-template" << 'MTPL'
#!/usr/bin/env bash
echo '## Findings'
MTPL
chmod +x "$TESTBIN/report-template"

cat > "$TESTBIN/exa-contents" << 'MCONT'
#!/usr/bin/env bash
echo '{"results":[{"url":"https://mock","text":"mock content"}]}'
MCONT
chmod +x "$TESTBIN/exa-contents"

MOCKCURL="$TMP/mockcurl"
cat > "$MOCKCURL" << 'MCURL'
#!/usr/bin/env bash
if [[ "$*" == *"openrouter.ai"* ]]; then
  echo '{"choices":[{"message":{"content":"# Synth\nFindings with https://mock.example.com/verify . Done."}}]}'
else
  echo '{}'
fi
MCURL
chmod +x "$MOCKCURL"

export RESEARCH_DIR WORKSPACE_DIR
"$TESTBIN/research-init" >/dev/null
gid=$("$TESTBIN/research-goal" add "MCP integration test goal" --priority=3)

OUTMD="$TMP/out.md"
set +e
run_out=$(cd /tmp && RESEARCH_DIR="$RESEARCH_DIR" WORKSPACE_DIR="$WORKSPACE_DIR" \
  OPENROUTER_API_KEY="" EXA_API_KEY=dummy SERPER_API_KEY=dummy EXA_BIN="$TESTBIN/exa-search" SERPER_BIN="$TESTBIN/serper-search" SOURCE_SCORE_BIN="$TESTBIN/source-score" REPORT_TEMPLATE_BIN="$TESTBIN/report-template" EXA_CONTENTS_BIN="$TESTBIN/exa-contents" \
  PATH="$MOCKCURL:$TESTBIN:$PATH" \
  "$TESTBIN/deep-research" "MCP test query" --goal="$gid" --depth=deep --budget=0.30 --output="$OUTMD" 2>&1)
run_code=$?
set -e

if [ $run_code -ne 0 ]; then
  echo "FAIL deep-research exit code: $run_code"; echo "$run_out" | tail -20; exit 1
fi
echo "PASS deep-research with --goal exit 0"

run_count=$(ls "$RESEARCH_DIR/runs/"*.json 2>/dev/null | wc -l)
if [ "$run_count" -ge 1 ]; then
  echo "PASS run artifact created"
else
  echo "FAIL no run artifacts"; exit 1
fi

run_file=$(ls "$RESEARCH_DIR/runs/"*.json | head -1)
stages=$(jq -r '.stages_run' "$run_file")
if [ "${stages:-0}" -ge 1 ]; then
  echo "PASS run has stages_run >= 1"
else
  echo "FAIL stages_run=$stages"; exit 1
fi

metrics_lines=$(wc -l < "$RESEARCH_DIR/metrics.jsonl")
if [ "$metrics_lines" -ge 1 ]; then
  echo "PASS metrics.jsonl updated"
else
  echo "FAIL metrics empty"; exit 1
fi

runs_in_goal=$("$TESTBIN/research-goal" list --json | jq -r --arg id "$gid" '.[] | select(.id==$id) | .runs | length')
cost=$( "$TESTBIN/research-goal" list --json | jq -r --arg id "$gid" '.[] | select(.id==$id) | .cost_so_far')
if [ "${runs_in_goal:-0}" -ge 1 ]; then
  echo "PASS goal runs[] updated"
else
  echo "FAIL goal runs empty"; exit 1
fi

if awk -v c="$cost" 'BEGIN { exit (c >= 0) ? 0 : 1 }'; then
  echo "PASS goal cost_so_far recorded ($cost)"
else
  echo "FAIL cost_so_far"; exit 1
fi

"$TESTBIN/research-status" --quiet
if [ -f "$RESEARCH_DIR/status.json" ]; then
  echo "PASS status.json refreshed"
else
  echo "FAIL status.json missing after --quiet"; exit 1
fi

OUTMD2="$TMP/out2.md"
set +e
run_out2=$(cd /tmp && RESEARCH_DIR="$RESEARCH_DIR" WORKSPACE_DIR="$WORKSPACE_DIR" \
  OPENROUTER_API_KEY="" EXA_API_KEY=dummy SERPER_API_KEY=dummy EXA_BIN="$TESTBIN/exa-search" SERPER_BIN="$TESTBIN/serper-search" SOURCE_SCORE_BIN="$TESTBIN/source-score" REPORT_TEMPLATE_BIN="$TESTBIN/report-template" EXA_CONTENTS_BIN="$TESTBIN/exa-contents" \
  PATH="$MOCKCURL:$TESTBIN:$PATH" \
  "$TESTBIN/deep-research" "Step test query" --goal="$gid" --mark-step=step-1 --feedback=4 \
  --depth=deep --budget=0.30 --output="$OUTMD2" 2>&1)
run_code2=$?
set -e

if [ $run_code2 -ne 0 ]; then
  echo "FAIL deep-research mark-step/feedback exit: $run_code2"; exit 1
fi

run_file2=$(ls -t "$RESEARCH_DIR/runs/"*.json | head -1)
step_id=$(jq -r '.step_id' "$run_file2")
if [ "$step_id" = "step-1" ]; then
  echo "PASS run artifact has step_id"
else
  echo "FAIL step_id=$step_id"; exit 1
fi

if [ -s "$RESEARCH_DIR/feedback.jsonl" ]; then
  fb_rating=$(tail -1 "$RESEARCH_DIR/feedback.jsonl" | jq -r '.rating')
  if [ "$fb_rating" = "4" ]; then
    echo "PASS --feedback=4 stored in feedback.jsonl"
  else
    echo "FAIL feedback rating=$fb_rating"; exit 1
  fi
else
  echo "FAIL feedback.jsonl empty"; exit 1
fi

echo "All research-integration tests passed"
exit 0