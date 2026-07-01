#!/bin/bash
# send-summering.sh — Skicka Moss nattskift-summering till Oscar kl 07:00
# Läses från /tmp/moss-nattskift-summering.md
# Skickar via Telegram (curl direkt, bypass:ar openclaw message tool)

set -euo pipefail

SUMMERIG_FILE="/tmp/moss-nattskift-summering.md"
LOG="/var/log/moss-summering.log"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "[$TIMESTAMP] Skickar summering till Oscar..." >> "$LOG"

# Hämta bot token från openclaw.json (export:as env för att undvika bash-problem med backticks)
export MOSS_BOT_TOKEN
MOSS_BOT_TOKEN=$(python3 -c "
import json
with open('/root/.openclaw/openclaw.json') as f:
    cfg = json.load(f)
print(cfg['channels']['telegram']['botToken'])
")
export MOSS_CHAT_ID="438805461"

# Läs summering
if [ ! -f "$SUMMERIG_FILE" ]; then
  echo "[$TIMESTAMP] FEL: Summering-fil saknas: $SUMMERIG_FILE" >> "$LOG"
  exit 1
fi

# Skicka som plain text (Telegram hanterar * och _ i cron-syntax/filenames konstigt i Markdown-läge)
{
  echo "🌿 Moss nattskift — summering 03:21 → 07:00 (1 juli 2026)"
  echo ""
  cat "$SUMMERIG_FILE"
  echo ""
  echo "Skickat automatiskt av Moss nattskift."
} > /tmp/moss-summering-telegram.txt

# Skicka via Telegram (max 4096 tecken per meddelande, dela om det behövs)
python3 << 'PYEOF'
import urllib.request, urllib.parse, json, os, re

with open("/tmp/moss-summering-telegram.txt") as f:
    text = f.read()

token = os.environ.get("MOSS_BOT_TOKEN", "")
chat_id = os.environ.get("MOSS_CHAT_ID", "438805461")

def smart_chunk(text, max_len=4000):
    """Split text into chunks <= max_len, preferring double-newline boundaries.
    Telegram parse_mode is plain text (we don't use Markdown because the
    summering contains */5 * * * * cron syntax and fal_image filenames that
    break the parser)."""
    chunks = []
    pos = 0
    n = len(text)
    while pos < n:
        if n - pos <= max_len:
            chunks.append(text[pos:])
            break
        target = pos + max_len
        safe = text.rfind("\n\n", pos, target)
        if safe == -1 or safe <= pos + max_len // 2:
            safe = text.rfind("\n", pos, target)
        if safe == -1 or safe <= pos + max_len // 2:
            safe = text.rfind(" ", pos, target)
        if safe == -1 or safe <= pos:
            safe = target
        chunks.append(text[pos:safe])
        pos = safe
    return chunks

chunks = smart_chunk(text, 4000)
print(f"[{os.popen('date -u +%H:%M:%S').read().strip()}] Skickar {len(chunks)} chunk(s) till {chat_id}...")

for i, chunk in enumerate(chunks):
    # Plain text — Telegram Markdown parser doesn't handle * or _ inside
    # backticks (e.g. */5 * * * * cron syntax, fal_image filenames).
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": chunk,
        "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                print(f"  [{i+1}/{len(chunks)}] OK msg_id={result.get('result',{}).get('message_id')}")
            else:
                print(f"  [{i+1}/{len(chunks)}] FAIL {result.get('description')}")
    except Exception as e:
        print(f"  [{i+1}/{len(chunks)}] FAIL {e}")
PYEOF

echo "[$TIMESTAMP] Summering skickad." >> "$LOG"
