#!/bin/bash
# weekly-retrospective.sh — Weekly self-improvement pass
#
# Runs the daily-reflection logic over 7 days of memory, then:
#  1. Saves reflection to memory/YYYY-MM-DD-retrospective.md
#  2. Updates moss-state.json's recent_decisions + open_loops
#  3. Posts a short summary to Oscar (weekly digest)
#
# Cron: 0 6 * * 0  (Sundays 06:00 UTC = 08:00 GMT+2)
# Log:  /var/log/moss-weekly-retrospective.log

set -euo pipefail

WORKSPACE="${WORKSPACE:-$HOME/.openclaw/workspace}"
STATE_FILE="$WORKSPACE/moss-state.json"
LOG="/var/log/moss-weekly-retrospective.log"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TODAY=$(date -u +%Y-%m-%d)
WEEK_AGO=$(date -u -d "7 days ago" +%Y-%m-%d 2>/dev/null || date -u -v-7d +%Y-%m-%d)

echo "[$TIMESTAMP] Starting weekly retrospective (looking back 7 days)..." >> "$LOG"

cd "$WORKSPACE"

# 1. Run reflection over 7 days
echo "[$TIMESTAMP] Running daily-reflection.sh --days 7..." >> "$LOG"
bin/moss/daily-reflection.sh --days 7 --apply 2>>"$LOG" > /tmp/moss-weekly-refl-$TODAY.md

if [ ! -s /tmp/moss-weekly-refl-$TODAY.md ]; then
  echo "[$TIMESTAMP] ❌ Reflection failed, aborting" >> "$LOG"
  exit 1
fi

# 2. Save as retrospective (with week-of annotation)
RETRO_FILE="$WORKSPACE/memory/$TODAY-retrospective.md"
{
  echo "# 📊 Moss weekly retrospective — week of $WEEK_AGO"
  echo ""
  echo "_Generated: $TIMESTAMP_"
  echo ""
  cat /tmp/moss-weekly-refl-$TODAY.md
} > "$RETRO_FILE"
echo "[$TIMESTAMP] ✅ Saved to $RETRO_FILE" >> "$LOG"

# 3. Update moss-state.json (atomic write)
if [ -f "$STATE_FILE" ]; then
  python3 << PYEOF
import json
from pathlib import Path

state_path = Path("$STATE_FILE")
state = json.loads(state_path.read_text())

# Update timestamp
state["last_updated"] = "$TIMESTAMP"

# Add a new decision record
reflection_path = Path("$RETRO_FILE")
reflection_size = reflection_path.stat().st_size
state["recent_decisions"].insert(0, {
    "ts": "$TIMESTAMP",
    "decision": "Ran weekly retrospective over 7 days of memory",
    "rationale": f"Auto-scheduled M2 self-improvement task. Reflection: {reflection_size} bytes.",
    "scope": "memory/$TODAY-retrospective.md"
})

# Trim recent_decisions to last 10
state["recent_decisions"] = state["recent_decisions"][:10]

# Atomic write
state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False))
print("✅ moss-state.json updated")
PYEOF
fi

# 4. Extract a short summary for Oscar (first ~500 chars of the reflection)
SUMMARY=$(head -c 500 "$RETRO_FILE")
SUMMARY_FULL_LEN=$(wc -c < "$RETRO_FILE")

# 5. Send to Oscar via curl (NOT openclaw message — 10s timeout)
echo "[$TIMESTAMP] Sending weekly digest to Oscar..." >> "$LOG"
python3 << PYEOF
import json, os
with open("$WORKSPACE/openclaw.json") as f:
    cfg = json.load(f)
token = cfg["channels"]["telegram"]["botToken"]
chat_id = "438805461"

text = f"""🌿 *Moss weekly retrospective* (week of $WEEK_AGO)

_Auto-generated $TIMESTAMP. Full report: $RETRO_FILE ($SUMMARY_FULL_LEN bytes)_

{SUMMARY}

📊 Full report + suggested MEMORY.md updates: $RETRO_FILE
🔄 moss-state.json updated."""

import urllib.request, urllib.parse
data = urllib.parse.urlencode({
    "chat_id": chat_id,
    "text": text[:4000],  # Telegram limit
}).encode()
req = urllib.request.Request(
    f"https://api.telegram.org/bot{token}/sendMessage",
    data=data, method="POST"
)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
        if result.get("ok"):
            print(f"  ✅ Sent (msg_id={result['result']['message_id']})")
        else:
            print(f"  ❌ {result.get('description')}")
except Exception as e:
    print(f"  ❌ {e}")
PYEOF

echo "[$TIMESTAMP] Weekly retrospective complete" >> "$LOG"
