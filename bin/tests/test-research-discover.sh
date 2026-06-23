#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

export RESEARCH_DIR="$TMP/research"
export WORKSPACE_DIR="$TMP/workspace"
mkdir -p "$WORKSPACE_DIR/projects/mossfund" "$RESEARCH_DIR"

DISC="$ROOT_DIR/research-discover"
INIT="$ROOT_DIR/research-init"
GOAL="$ROOT_DIR/research-goal"
chmod +x "$DISC" "$INIT" "$GOAL"
"$INIT" >/dev/null

SOURCE="$WORKSPACE_DIR/projects/mossfund/source.md"
cat > "$SOURCE" <<'EOF'
# Test Status

## Open questions
- What is the conversion rate for MCP servers in the agent economy?
- TBD: pricing benchmarks for x402 micropayments

## Gaps
- Unknown revenue model for utility APIs

## Other
- Exa status is unclear with limited info on restoration timeline
- TODO research competitor landscape for Telegram bots
EOF

# Existing goal that should filter one candidate
echo '{"id":"g-1","question":"What is the conversion rate for MCP servers","status":"active","priority":3,"tags":[],"created_at":"2026-06-18T00:00:00Z","updated_at":"2026-06-18T00:00:00Z","notes":[],"total_steps":0,"answered_steps":0,"cost_so_far":0,"runs":[],"plan_path":""}' \
  > "$RESEARCH_DIR/goals.jsonl"

json=$("$DISC" --source="$SOURCE" --json)
count=$(echo "$json" | jq '.candidates | length')
if [ "$count" -ge 1 ]; then
  echo "PASS candidates extracted ($count)"
else
  echo "FAIL no candidates"; exit 1
fi

# Filtered: MCP conversion question should not appear (substring match)
if echo "$json" | jq -r '.candidates[].question' | grep -qi "conversion rate for MCP"; then
  echo "FAIL duplicate MCP question not filtered"
  exit 1
else
  echo "PASS existing goal filtered by substring"
fi

top_conf=$(echo "$json" | jq -r '.candidates[0].confidence')
second_conf=$(echo "$json" | jq -r '.candidates[1].confidence // 0')
if awk -v a="$top_conf" -v b="$second_conf" 'BEGIN { exit (a >= b) ? 0 : 1 }'; then
  echo "PASS confidence ordering"
else
  echo "FAIL confidence order"; exit 1
fi

"$DISC" --source="$SOURCE" --apply >/dev/null
if grep -q 'auto-discovered' "$RESEARCH_DIR/goals.jsonl"; then
  echo "PASS --apply adds auto-discovered goals"
else
  echo "FAIL --apply"; cat "$RESEARCH_DIR/goals.jsonl"; exit 1
fi

echo "All research-discover tests passed"
exit 0