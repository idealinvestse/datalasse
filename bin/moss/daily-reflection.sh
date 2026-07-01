#!/bin/bash
# daily-reflection.sh — Moss self-reflection tool
#
# Reads recent memory files, identifies patterns, undigested decisions,
# and suggests MEMORY.md updates. Uses the internal LLM router for the
# synthesis pass.
#
# Use cases:
#   - End-of-day review: what did I actually accomplish?
#   - Pattern detection: which problems keep recurring?
#   - Memory hygiene: what's in daily files that should graduate to MEMORY.md?
#   - Self-improvement: what could I do better tomorrow?
#
# Default: dry-run (prints suggestions, doesn't modify anything).
# Use --apply to write the suggestions to memory/YYYY-MM-DD-reflection.md
# (never auto-modifies MEMORY.md — that's a manual review step).

set -euo pipefail

DAYS=3
MODEL=""
APPLY=0
JSON=0
GROUP="subagent-research-quick"
WORKSPACE="${WORKSPACE:-$HOME/.openclaw/workspace}"
MEMORY_DIR="$WORKSPACE/memory"
TODAY=$(date -u +%Y-%m-%d)
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

usage() {
  cat <<EOF
Usage: $0 [--days N] [--apply] [--model MODEL] [--json]

Options:
  --days N         Look back N days (default: 3)
  --apply          Write reflection to memory/YYYY-MM-DD-reflection.md
  --model MODEL    Override LLM model (uses group=$GROUP default)
  --json           Output as JSON instead of Markdown
  --help           Show this help

Reflection writes to: memory/\$TODAY-reflection.md
Uses llm-call group: $GROUP (free-first, ~\$0.002 budget)
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --days) DAYS="$2"; shift 2 ;;
    --apply) APPLY=1; shift ;;
    --model) MODEL="$2"; shift 2 ;;
    --json) JSON=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

# Collect recent memory files
FILES=$(find "$MEMORY_DIR" -maxdepth 1 -name "2026-*.md" -mtime -"$DAYS" 2>/dev/null | sort)
if [ -z "$FILES" ]; then
  echo "No memory files found in last $DAYS days in $MEMORY_DIR" >&2
  exit 1
fi

echo "🪞 Moss daily reflection — looking back $DAYS days" >&2
echo "📁 Files: $(echo "$FILES" | wc -l) memory files" >&2

# Build context: concatenate recent memory (truncate to fit budget)
CONTEXT=""
TOTAL_BYTES=0
MAX_BYTES=12000  # ~3-4K tokens, well within --max-tokens=2000 budget
for f in $FILES; do
  size=$(stat -c%s "$f")
  if [ $((TOTAL_BYTES + size)) -gt $MAX_BYTES ]; then
    echo "  (truncating — context would exceed $MAX_BYTES bytes)" >&2
    break
  fi
  CONTENT=$(cat "$f")
  CONTEXT="$CONTEXT

=== $f ===
$CONTENT"
  TOTAL_BYTES=$((TOTAL_BYTES + size))
done

# Build the reflection prompt
PROMPT="You are Moss reflecting on your own recent work. Analyze these recent memory files and produce a structured reflection.

$CONTEXT

===

Produce a reflection with these sections (use Markdown, in Swedish since the files are in Swedish):

## 🪞 Mönster jag ser
- Patterns, recurring problems, or themes that show up repeatedly
- Be specific: cite dates/files where patterns appear

## 🔴 Odigerade beslut
- Decisions or commitments made but with no follow-up recorded
- Things I said I'd do but didn't (check git log + cron jobs + plan updates)

## 🧠 Lessons att graduera till MEMORY.md
- Specific facts/lessons from daily files that should go into long-term memory
- Format each as: '### [topic]' + 1-2 sentence summary

## 🌱 Vad jag kan göra bättre imorgon
- Concrete, actionable improvements based on patterns observed
- 2-3 items max, each specific enough to actually do

## ⚠️ Varningar / risker
- Anything that looks like a future problem brewing
- Technical debt accumulating
- Decisions that look wrong in hindsight

Be honest, not flattering. If today was mediocre, say so. Use concise bullets, not paragraphs. Total length: 400-700 words."

# Call the LLM router
RAW_JSON="/tmp/moss-reflection-$TODAY-raw.json"
RESULT_FILE="/tmp/moss-reflection-$TODAY.md"
echo "🤖 Calling llm-call (group=$GROUP)..." >&2
cd "$WORKSPACE"

if [ -n "$MODEL" ]; then
  bin/llm-call --group="$GROUP" --prompt="$PROMPT" --max-tokens=2500 --temperature=0.3 --model="$MODEL" --json > "$RAW_JSON" 2>/tmp/moss-reflection-err
else
  bin/llm-call --group="$GROUP" --prompt="$PROMPT" --max-tokens=2500 --temperature=0.3 --json > "$RAW_JSON" 2>/tmp/moss-reflection-err
fi

# Parse the response
if [ ! -s "$RAW_JSON" ]; then
  echo "❌ LLM call failed:" >&2
  cat /tmp/moss-reflection-err >&2
  exit 1
fi

# Extract the assistant content + cost from the JSON response
REFLECTION=$(python3 -c "
import json
with open('$RAW_JSON') as f:
    data = json.load(f)
content = data.get('response', data.get('content', ''))
if not content and 'choices' in data:
    content = data['choices'][0].get('message', {}).get('content', '')
print(content)
")
COST=$(python3 -c "
import json
try:
    with open('$RAW_JSON') as f:
        data = json.load(f)
    print(data.get('meta', {}).get('cost_usd', '?'))
except: print('?')
")
MODEL_USED=$(python3 -c "
import json
try:
    with open('$RAW_JSON') as f:
        data = json.load(f)
    print(data.get('meta', {}).get('model', '?'))
except: print('?')
")
TIER=$(python3 -c "
import json
try:
    with open('$RAW_JSON') as f:
        data = json.load(f)
    print(data.get('meta', {}).get('tier_index', '?'))
except: print('?')
")
echo "💰 Cost: \$$COST  •  Model: $MODEL_USED  •  Tier: $TIER" >&2

# Prepend metadata
{
  echo "# 🪞 Moss daily reflection — $TODAY"
  echo ""
  echo "_Generated: $TIMESTAMP  •  Days reviewed: $DAYS  •  Files: $(echo "$FILES" | wc -l)_"
  echo ""
  echo "$REFLECTION"
} > "$RESULT_FILE.tmp"
mv "$RESULT_FILE.tmp" "$RESULT_FILE"

# Cost reporting already done above (from raw JSON)

# Output
if [ "$JSON" -eq 1 ]; then
  python3 -c "
import json
with open('$RESULT_FILE') as f:
    print(json.dumps({'date': '$TODAY', 'files_reviewed': $(echo "$FILES" | wc -l), 'reflection': f.read()}, ensure_ascii=False, indent=2))
"
else
  cat "$RESULT_FILE"
fi

# Optionally save to memory/
if [ "$APPLY" -eq 1 ]; then
  OUT="$MEMORY_DIR/$TODAY-reflection.md"
  cp "$RESULT_FILE" "$OUT"
  echo "" >&2
  echo "✅ Reflection saved to: $OUT" >&2
  echo "📝 Note: this does NOT auto-update MEMORY.md — review the reflection and add manually" >&2
else
  echo "" >&2
  echo "💡 Dry run. Use --apply to save to memory/$TODAY-reflection.md" >&2
fi
