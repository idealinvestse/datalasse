#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

export RESEARCH_DIR="$TMP/research"
export WORKSPACE_DIR="$TMP/workspace"
mkdir -p "$WORKSPACE_DIR" "$RESEARCH_DIR/runs"

IMPROVE="$ROOT_DIR/research-improve"
INIT="$ROOT_DIR/research-init"
chmod +x "$IMPROVE" "$INIT"
"$INIT" >/dev/null

now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
wd_exa="$TMP/workdir-exa"
wd_fb="$TMP/workdir-fallback"
mkdir -p "$wd_exa" "$wd_fb"

echo '[{"ts":"'"$now"'","event":"search","detail":{"provider":"exa","stage":2}}]' \
  | jq '{total:0.05,budget:0.2,exceeded:false,events:.}' > "$wd_exa/cost-summary.json"
echo '[{"ts":"'"$now"'","event":"fallback","detail":{"provider":"serper","stage":2}},{"ts":"'"$now"'","event":"search","detail":{"provider":"exa","stage":2}}]' \
  | jq '{total:0.08,budget:0.2,exceeded:false,events:.}' > "$wd_fb/cost-summary.json"

jq -n --arg ts "$now" --arg wd "$wd_exa" \
  '{run_id:"r-high-1",goal_id:"g1",question:"what is the market size for MCP servers in the European agent economy today",cost:0.05,timestamp:$ts,workdir:$wd,failed:false}' \
  > "$RESEARCH_DIR/runs/r-high-1.json"
jq -n --arg ts "$now" --arg wd "$wd_exa" \
  '{run_id:"r-high-2",goal_id:"g1",question:"what is the pricing model for agent utilities in the cloud hosting market segment",cost:0.04,timestamp:$ts,workdir:$wd,failed:false}' \
  > "$RESEARCH_DIR/runs/r-high-2.json"
jq -n --arg ts "$now" --arg wd "$wd_fb" \
  '{run_id:"r-low-1",goal_id:"g2",question:"short",cost:0.03,timestamp:$ts,workdir:$wd,failed:false}' \
  > "$RESEARCH_DIR/runs/r-low-1.json"
jq -n --arg ts "$now" --arg wd "$wd_fb" \
  '{run_id:"r-low-2",goal_id:"g2",question:"tiny",cost:0.02,timestamp:$ts,workdir:$wd,failed:false}' \
  > "$RESEARCH_DIR/runs/r-low-2.json"

cat > "$RESEARCH_DIR/feedback.jsonl" <<EOF
{"run_id":"r-high-1","goal_id":"g1","rating":5,"comment":"","provider":"exa","ts":"$now"}
{"run_id":"r-high-2","goal_id":"g1","rating":4,"comment":"","provider":"exa","ts":"$now"}
{"run_id":"r-low-1","goal_id":"g2","rating":2,"comment":"","provider":"exa-fallback","ts":"$now"}
{"run_id":"r-low-2","goal_id":"g2","rating":1,"comment":"","provider":"exa-fallback","ts":"$now"}
EOF

out=$("$IMPROVE")
if echo "$out" | grep -qiE 'Use .+ for .+ type|default'; then
  echo "PASS high-rated pattern suggests default"
else
  echo "FAIL missing default suggestion"; echo "$out"; exit 1
fi

if echo "$out" | grep -qiE 'avoid|refine'; then
  echo "PASS low-rated pattern flagged"
else
  echo "FAIL missing avoid/refine"; echo "$out"; exit 1
fi

json=$("$IMPROVE" --json)
total=$(echo "$json" | jq -r '.global_stats.total_feedback')
if [ "$total" -eq 4 ]; then
  echo "PASS global_stats.total_feedback=4"
else
  echo "FAIL total_feedback=$total"; exit 1
fi

# Empty feedback
> "$RESEARCH_DIR/feedback.jsonl"
empty=$("$IMPROVE" --json)
pat_len=$(echo "$empty" | jq '.patterns | length')
if [ "$pat_len" -eq 0 ]; then
  echo "PASS empty feedback yields no patterns"
else
  echo "FAIL expected 0 patterns"; exit 1
fi

echo "All research-improve tests passed"
exit 0