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
chmod +x "$INIT" "$GOAL"

"$INIT" >/dev/null

# Add first goal
id1=$("$GOAL" add "What is the future of x402 payments?" --priority=3 --tags=payments,ai)
if [[ "$id1" =~ ^g-[0-9]{8}-[0-9]{3}$ ]]; then
  echo "PASS add returns valid id: $id1"
else
  echo "FAIL add id format: $id1"; exit 1
fi

lines=$(wc -l < "$RESEARCH_DIR/goals.jsonl")
if [ "$lines" -eq 1 ]; then
  echo "PASS goals.jsonl has 1 line"
else
  echo "FAIL goals line count: $lines"; exit 1
fi

id2=$("$GOAL" add "Second goal question" --priority=2)
num2=${id2##*-}
if [ "$num2" = "002" ]; then
  echo "PASS second id increments: $id2"
else
  echo "FAIL id increment: expected 002 got $num2"; exit 1
fi

active_count=$("$GOAL" list --json | jq 'length')
if [ "$active_count" -eq 2 ]; then
  echo "PASS list --json active count"
else
  echo "FAIL list --json count: $active_count"; exit 1
fi

list_out=$("$GOAL" list)
if echo "$list_out" | grep -q "$id1"; then
  echo "PASS list pretty print"
else
  echo "FAIL list pretty"; exit 1
fi

if "$GOAL" show "$id1" 2>/dev/null | jq -e '.question' >/dev/null; then
  echo "PASS show prints goal json"
else
  echo "FAIL show"; exit 1
fi

"$GOAL" update "$id1" --priority=5 --status=paused
pri=$("$GOAL" list --all --json | jq -r --arg id "$id1" '.[] | select(.id==$id) | .priority')
st=$("$GOAL" list --all --json | jq -r --arg id "$id1" '.[] | select(.id==$id) | .status')
if [ "$pri" = "5" ] && [ "$st" = "paused" ]; then
  echo "PASS update priority and status"
else
  echo "FAIL update: pri=$pri st=$st"; exit 1
fi

# Restore active so list filter test below is meaningful
"$GOAL" update "$id1" --status=active >/dev/null

"$GOAL" done "$id2" --notes="completed in test"
done_st=$("$GOAL" list --all --json | jq -r --arg id "$id2" '.[] | select(.id==$id) | .status')
if [ "$done_st" = "done" ]; then
  echo "PASS done marks complete"
else
  echo "FAIL done: $done_st"; exit 1
fi

active_after=$("$GOAL" list --json | jq 'length')
if [ "$active_after" -eq 1 ]; then
  echo "PASS list filters done goals"
else
  echo "FAIL active filter after done: $active_after"; exit 1
fi

"$GOAL" plan "$id1"
plan_file="$RESEARCH_DIR/plans/${id1}.md"
steps=$("$GOAL" show "$id1" 2>/dev/null | jq -r '.total_steps')
if [ -f "$plan_file" ] && [ "$steps" = "3" ]; then
  echo "PASS plan stub creates file and total_steps=3"
else
  echo "FAIL plan: file=$plan_file steps=$steps"; exit 1
fi

echo "All research-goal tests passed"
exit 0