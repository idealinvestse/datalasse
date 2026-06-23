#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

export RESEARCH_DIR="$TMP/research"
export WORKSPACE_DIR="$TMP/workspace"
mkdir -p "$WORKSPACE_DIR" "$RESEARCH_DIR/runs" "$RESEARCH_DIR/plans"

STATUS_CMD="$ROOT_DIR/research-status"
chmod +x "$STATUS_CMD"

now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat > "$RESEARCH_DIR/goals.jsonl" <<EOF
{"id":"g-20260618-001","question":"Active goal one","status":"active","priority":3,"tags":[],"created_at":"$now","updated_at":"$now","notes":[],"total_steps":3,"answered_steps":1,"cost_so_far":0.05,"runs":[],"plan_path":"$RESEARCH_DIR/plans/g-20260618-001.md"}
{"id":"g-20260618-002","question":"Done goal two","status":"done","priority":2,"tags":[],"created_at":"$now","updated_at":"$now","notes":[],"total_steps":0,"answered_steps":0,"cost_so_far":0.12,"runs":[],"plan_path":"$RESEARCH_DIR/plans/g-20260618-002.md"}
EOF

printf '%s\n' "{\"timestamp\":\"$now\",\"run_id\":\"2026-06-18T12-00-00\",\"goal_id\":\"g-20260618-001\",\"question\":\"Active goal one\",\"cost\":0.05,\"latency_s\":42,\"stages_run\":5,\"sources_found\":8,\"verification_count\":3,\"status\":\"ok\"}" \
  > "$RESEARCH_DIR/metrics.jsonl"

touch "$RESEARCH_DIR/goals.jsonl" "$RESEARCH_DIR/metrics.jsonl"

# Default mode
out=$("$STATUS_CMD" 2>/dev/null)
if [ -f "$RESEARCH_DIR/status.json" ] && [ -f "$WORKSPACE_DIR/STATUS_RESEARCH.md" ]; then
  echo "PASS default writes status.json and STATUS_RESEARCH.md"
else
  echo "FAIL default files missing"; exit 1
fi

if echo "$out" | grep -q "Research Status"; then
  echo "PASS default prints markdown"
else
  echo "FAIL default output"; exit 1
fi

active=$(jq -r '.active_goals' "$RESEARCH_DIR/status.json")
if [ "$active" = "1" ]; then
  echo "PASS active_goals count"
else
  echo "FAIL active_goals=$active"; exit 1
fi

# --json mode
json_out=$("$STATUS_CMD" --json 2>/dev/null)
for key in generated_at active_goals done_goals total_runs_week health goals recent_runs; do
  if echo "$json_out" | jq -e ".$key" >/dev/null; then
    :
  else
    echo "FAIL --json missing key: $key"; exit 1
  fi
done
echo "PASS --json schema keys"

# --quiet mode
quiet_out=$("$STATUS_CMD" --quiet 2>/dev/null)
if [ -z "$quiet_out" ] && [ -f "$RESEARCH_DIR/status.json" ]; then
  echo "PASS --quiet no stdout"
else
  echo "FAIL --quiet output: '$quiet_out'"; exit 1
fi

echo "All research-status tests passed"
exit 0