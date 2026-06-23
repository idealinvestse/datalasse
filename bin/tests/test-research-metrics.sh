#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

export RESEARCH_DIR="$TMP/research"
export WORKSPACE_DIR="$TMP/workspace"
mkdir -p "$WORKSPACE_DIR"

METRICS="$ROOT_DIR/research-metrics"
INIT="$ROOT_DIR/research-init"
chmod +x "$METRICS" "$INIT"
"$INIT" >/dev/null

now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
old=$(date -u -d "10 days ago" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-10d +%Y-%m-%dT%H:%M:%SZ)

cat > "$RESEARCH_DIR/metrics.jsonl" <<EOF
{"timestamp":"$now","run_id":"r1","goal_id":"g-a","question":"q1","cost":0.10,"latency_s":40,"stages_run":4,"sources_found":10,"status":"ok"}
{"timestamp":"$now","run_id":"r2","goal_id":"g-a","question":"q2","cost":0.05,"latency_s":30,"stages_run":5,"sources_found":8,"status":"ok"}
{"timestamp":"$now","run_id":"r3","goal_id":"g-b","question":"q3","cost":0.20,"latency_s":60,"stages_run":4,"sources_found":12,"status":"failed"}
{"timestamp":"$now","run_id":"r4","goal_id":"g-b","question":"q4","cost":0.08,"latency_s":25,"stages_run":3,"sources_found":6,"status":"ok"}
{"timestamp":"$old","run_id":"r5","goal_id":"g-c","question":"old","cost":1.00,"latency_s":100,"stages_run":6,"sources_found":20,"status":"ok"}
EOF

cat > "$RESEARCH_DIR/feedback.jsonl" <<EOF
{"run_id":"r1","goal_id":"g-a","rating":4,"comment":"ok","provider":"exa","ts":"$now"}
{"run_id":"r2","goal_id":"g-a","rating":5,"comment":"great","provider":"exa","ts":"$now"}
EOF

"$METRICS" >/dev/null
if [ -f "$RESEARCH_DIR/metrics-weekly.md" ] && grep -q "## Summary" "$RESEARCH_DIR/metrics-weekly.md"; then
  echo "PASS metrics-weekly.md created with Summary"
else
  echo "FAIL metrics-weekly.md"; exit 1
fi

json=$("$METRICS" --json)
total_runs=$(echo "$json" | jq -r '.total_runs')
total_cost=$(echo "$json" | jq -r '.total_cost')
success_rate=$(echo "$json" | jq -r '.success_rate')

if [ "$total_runs" -eq 4 ]; then
  echo "PASS total_runs=4 (excludes old)"
else
  echo "FAIL total_runs=$total_runs"; exit 1
fi

exp_cost=$(python3 -c 'print(0.10+0.05+0.20+0.08)')
if awk -v a="$total_cost" -v b="$exp_cost" 'BEGIN { exit (a == b) ? 0 : 1 }'; then
  echo "PASS total_cost correct"
else
  echo "FAIL total_cost=$total_cost expected $exp_cost"; exit 1
fi

if awk -v s="$success_rate" 'BEGIN { exit (s == 0.75) ? 0 : 1 }'; then
  echo "PASS success_rate=0.75"
else
  echo "FAIL success_rate=$success_rate"; exit 1
fi

json24=$("$METRICS" --period=24h --json)
runs24=$(echo "$json24" | jq -r '.total_runs')
if [ "$runs24" -eq 4 ]; then
  echo "PASS --period=24h includes recent only"
else
  echo "FAIL period 24h runs=$runs24"; exit 1
fi

trend_len=$(echo "$json" | jq '.cost_trend | length')
if [ "$trend_len" -ge 1 ]; then
  echo "PASS cost trend has date buckets"
else
  echo "FAIL cost trend empty"; exit 1
fi

echo "All research-metrics tests passed"
exit 0