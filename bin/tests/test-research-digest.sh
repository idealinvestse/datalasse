#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

export RESEARCH_DIR="$TMP/research"
export WORKSPACE_DIR="$TMP/workspace"
mkdir -p "$WORKSPACE_DIR/bin" "$RESEARCH_DIR/runs"

# Mock openclaw
mkdir -p "$TMP/bin"
cat > "$TMP/bin/openclaw" <<'EOF'
#!/usr/bin/env bash
echo "$*" >> "${OPENCLAW_LOG:-/tmp/openclaw.log}"
EOF
chmod +x "$TMP/bin/openclaw"
export OPENCLAW_LOG="$TMP/openclaw.log"
export PATH="$TMP/bin:$PATH"

DIGEST="$ROOT_DIR/research-digest"
INIT="$ROOT_DIR/research-init"
chmod +x "$DIGEST" "$INIT"
"$INIT" >/dev/null

now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
test_date="2026-06-19"

cat > "$RESEARCH_DIR/goals.jsonl" <<EOF
{"id":"g-20260618-001","question":"Active digest test goal","status":"active","priority":4,"tags":[],"created_at":"$now","updated_at":"$now","notes":[],"total_steps":3,"answered_steps":1,"cost_so_far":0.15,"runs":["run-d1"],"plan_path":""}
EOF

jq -n --arg ts "$now" \
  '{run_id:"run-d1",goal_id:"g-20260618-001",question:"What are x402 payment trends?",cost:0.15,summary:"Micropayments growing via agent economy",timestamp:$ts,failed:false,workdir:""}' \
  > "$RESEARCH_DIR/runs/run-d1.json"

jq -n --arg ts "$now" \
  '{generated_at:$ts,active_goals:1,done_goals:0,cache_hit_rate:0.12,health:{exa:"down",serper:"ok"},goals:[]}' \
  > "$RESEARCH_DIR/status.json"

md=$("$DIGEST" --date="$test_date")
for section in "Top insights" "Goal progress" "Suggested next steps" "Health" "Upcoming"; do
  if echo "$md" | grep -q "## $section"; then
    echo "PASS section: $section"
  else
    echo "FAIL missing section: $section"; echo "$md"; exit 1
  fi
done

digest_file="$RESEARCH_DIR/digest-${test_date}.md"
if [ -f "$digest_file" ]; then
  echo "PASS digest file written"
else
  echo "FAIL digest file missing"; exit 1
fi

json=$("$DIGEST" --date="$test_date" --json)
for field in top_insights goal_progress suggested_next_steps health upcoming; do
  if echo "$json" | jq -e ".$field" >/dev/null; then
    echo "PASS json field: $field"
  else
    echo "FAIL json missing $field"; exit 1
  fi
done

"$DIGEST" --date="$test_date" --telegram >/dev/null
if [ -f "$OPENCLAW_LOG" ] && grep -q "telegram" "$OPENCLAW_LOG" && grep -q "438805461" "$OPENCLAW_LOG"; then
  echo "PASS --telegram mock delivery"
else
  echo "FAIL telegram mock"; cat "$OPENCLAW_LOG" 2>/dev/null; exit 1
fi

words=$(echo "$md" | wc -w | tr -d ' ')
if [ "$words" -ge 50 ] && [ "$words" -le 500 ]; then
  echo "PASS word count in range ($words)"
else
  echo "FAIL word count=$words"; exit 1
fi

echo "All research-digest tests passed"
exit 0