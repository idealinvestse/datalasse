#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

export RESEARCH_DIR="$TMP/research"
export WORKSPACE_DIR="$TMP/workspace"
mkdir -p "$WORKSPACE_DIR" "$RESEARCH_DIR/runs"

PRI="$ROOT_DIR/research-prioritize"
INIT="$ROOT_DIR/research-init"
chmod +x "$PRI" "$INIT"
"$INIT" >/dev/null

now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
yesterday=$(date -u -d "2 days ago" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-2d +%Y-%m-%dT%H:%M:%SZ)

# Goal A: high priority, recent, cheap, high rating
# Goal B: low priority, old, expensive, low rating
# Goal C: medium
cat > "$RESEARCH_DIR/goals.jsonl" <<EOF
{"id":"g-20260618-001","question":"High priority recent goal","status":"active","priority":5,"tags":[],"created_at":"$yesterday","updated_at":"$now","notes":[],"total_steps":3,"answered_steps":1,"cost_so_far":0.02,"runs":["run-a"],"plan_path":"$RESEARCH_DIR/plans/g-001.md"}
{"id":"g-20260618-002","question":"Low priority old expensive goal","status":"active","priority":1,"tags":[],"created_at":"$yesterday","updated_at":"$yesterday","notes":[],"total_steps":0,"answered_steps":0,"cost_so_far":2.50,"runs":["run-b"],"plan_path":"$RESEARCH_DIR/plans/g-002.md"}
{"id":"g-20260618-003","question":"Medium balanced goal","status":"active","priority":3,"tags":[],"created_at":"$now","updated_at":"$now","notes":[],"total_steps":0,"answered_steps":0,"cost_so_far":0.50,"runs":[],"plan_path":"$RESEARCH_DIR/plans/g-003.md"}
EOF

jq -n --arg ts "$now" '{run_id:"run-a",goal_id:"g-20260618-001",question:"q",cost:0.02,timestamp:$ts,failed:false,workdir:""}' \
  > "$RESEARCH_DIR/runs/run-a.json"
jq -n --arg ts "$yesterday" '{run_id:"run-b",goal_id:"g-20260618-002",question:"q",cost:2.5,timestamp:$ts,failed:false,workdir:""}' \
  > "$RESEARCH_DIR/runs/run-b.json"

cat > "$RESEARCH_DIR/feedback.jsonl" <<EOF
{"run_id":"run-a","goal_id":"g-20260618-001","rating":5,"comment":"","provider":"exa","ts":"$now"}
{"run_id":"run-b","goal_id":"g-20260618-002","rating":1,"comment":"","provider":"exa","ts":"$yesterday"}
EOF

"$PRI" >/dev/null
if [ -f "$RESEARCH_DIR/prioritization.json" ]; then
  echo "PASS prioritization.json created"
else
  echo "FAIL prioritization.json missing"; exit 1
fi

top_id=$(jq -r '.rankings[0].goal_id' "$RESEARCH_DIR/prioritization.json")
if [ "$top_id" = "g-20260618-001" ]; then
  echo "PASS high-value goal ranks first"
else
  echo "FAIL expected g-20260618-001 first, got $top_id"; exit 1
fi

json=$("$PRI" --json)
if echo "$json" | jq -e '.rankings[0].components.priority' >/dev/null; then
  echo "PASS --json has components"
else
  echo "FAIL --json components"; exit 1
fi

top_custom=$("$PRI" --weights=0.1,0.1,0.1,0.7 --json | jq -r '.rankings[0].goal_id')
# feedback-heavy weights should still rank 001 first (rating 5 vs 1)
if [ "$top_custom" = "g-20260618-001" ]; then
  echo "PASS custom weights accepted"
else
  echo "FAIL custom weights top=$top_custom"; exit 1
fi

"$PRI" --apply >/dev/null
new_pri=$(jq -r --arg id g-20260618-001 '.rankings[] | select(.goal_id==$id) | .new_priority' "$RESEARCH_DIR/prioritization.json")
applied=$(grep 'g-20260618-001' "$RESEARCH_DIR/goals.jsonl" | jq -r '.priority')
if [ "$applied" = "$new_pri" ]; then
  echo "PASS --apply updates goals.jsonl"
else
  echo "FAIL apply: expected $new_pri got $applied"; exit 1
fi

# Empty active goals
echo '{"id":"g-x","question":"done","status":"done","priority":3,"tags":[],"created_at":"'"$now"'","updated_at":"'"$now"'","notes":[],"total_steps":0,"answered_steps":0,"cost_so_far":0,"runs":[],"plan_path":""}' \
  > "$RESEARCH_DIR/goals.jsonl"
count=$("$PRI" --json | jq '.rankings | length')
if [ "$count" -eq 0 ]; then
  echo "PASS empty active goals"
else
  echo "FAIL expected 0 rankings got $count"; exit 1
fi

echo "All research-prioritize tests passed"
exit 0