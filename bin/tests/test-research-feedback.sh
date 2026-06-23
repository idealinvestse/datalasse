#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

export RESEARCH_DIR="$TMP/research"
export WORKSPACE_DIR="$TMP/workspace"
mkdir -p "$WORKSPACE_DIR" "$RESEARCH_DIR/runs"

FB="$ROOT_DIR/research-feedback"
INIT="$ROOT_DIR/research-init"
chmod +x "$FB" "$INIT"
"$INIT" >/dev/null

"$FB" unknown-run-001 --rating=4 --comment="good test"
if [ -s "$RESEARCH_DIR/feedback.jsonl" ]; then
  echo "PASS submit creates feedback.jsonl"
else
  echo "FAIL feedback.jsonl missing"; exit 1
fi

line=$(tail -1 "$RESEARCH_DIR/feedback.jsonl")
if echo "$line" | jq -e '.rating == 4 and .goal_id == "standalone"' >/dev/null; then
  echo "PASS unknown run-id uses standalone goal"
else
  echo "FAIL standalone goal"; echo "$line"; exit 1
fi

gid="g-20260618-099"
RUN_ID="2026-06-18T22-39-15"
jq -n \
  --arg run_id "$RUN_ID" --arg goal_id "$gid" --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{run_id:$run_id,goal_id:$goal_id,question:"q",stages_run:4,cost:0.07,timestamp:$ts,failed:false,workdir:""}' \
  > "$RESEARCH_DIR/runs/${RUN_ID}.json"

"$FB" "$RUN_ID" --rating=5 --comment="excellent"
goal=$(tail -1 "$RESEARCH_DIR/feedback.jsonl" | jq -r '.goal_id')
if [ "$goal" = "$gid" ]; then
  echo "PASS known run-id resolves goal_id"
else
  echo "FAIL goal_id=$goal"; exit 1
fi

list_out=$("$FB" list)
if echo "$list_out" | grep -q "$RUN_ID"; then
  echo "PASS list shows entry"
else
  echo "FAIL list"; echo "$list_out"; exit 1
fi

stats_out=$("$FB" stats)
if echo "$stats_out" | grep -q "$gid"; then
  echo "PASS stats includes goal"
else
  echo "FAIL stats"; echo "$stats_out"; exit 1
fi

set +e
"$FB" bad-run --rating=9 2>/dev/null
bad_code=$?
set -e
if [ "$bad_code" -ne 0 ]; then
  echo "PASS invalid rating rejected"
else
  echo "FAIL invalid rating accepted"; exit 1
fi

echo "All research-feedback tests passed"
exit 0