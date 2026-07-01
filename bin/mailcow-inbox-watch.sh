#!/bin/bash
#
# mailcow-inbox-watch.sh — Monitor oscar@intelliserve.se INBOX
# Skickar Telegram-notis till Alabama när nytt mail kommer in
#
# Körs var 5:e minut via cron (se `crontab -l`)
# Använder imaplib + standardbiblioteket (ingen extern dep)
# State sparas i /root/.openclaw/workspace/memory/mailcow-inbox-state.json

set -euo pipefail

# === Config ===
MAILCOW_HOST="mail.intelliserve.se"
MAILCOW_USER="oscar@intelliserve.se"
MAILCOW_PASS="Klant6kalle"
TELEGRAM_CHAT="438805461"
STATE_FILE="/root/.openclaw/workspace/memory/mailcow-inbox-state.json"
TMP_NEW="/tmp/mailcow-inbox-new-$$.json"

# Telegram bot-token (samma som datalasse_bot, från /root/.openclaw/openclaw.json)
TELEGRAM_BOT_TOKEN=$(python3 -c "import json; print(json.load(open('/root/.openclaw/openclaw.json'))['channels']['telegram']['botToken'])" 2>/dev/null)

# === Funktioner ===
log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"; }

# Lista mail i INBOX (returnerar JSON med id, from, subject, date, message_id)
list_inbox() {
    python3 <<PYEOF
import imaplib, email, json, sys
from email.header import decode_header
from email.utils import parsedate_to_datetime

host, user, pw = "$MAILCOW_HOST", "$MAILCOW_USER", "$MAILCOW_PASS"
M = imaplib.IMAP4_SSL(host, 993)
M.login(user, pw)
M.select("INBOX")
typ, data = M.search(None, "ALL")
ids = data[0].split()
out = []
for mid in ids:
    typ, msg_data = M.fetch(mid, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])
    
    def decode(h):
        if not h: return ""
        return " ".join(
            b.decode(c or "utf-8", errors="replace") if isinstance(b, bytes) else b
            for b, c in decode_header(h)
        )
    
    out.append({
        "uid": mid.decode() if isinstance(mid, bytes) else mid,
        "message_id": msg.get("Message-ID", "").strip("<>"),
        "from": decode(msg.get("From", "")),
        "to": decode(msg.get("To", "")),
        "subject": decode(msg.get("Subject", "")),
        "date": msg.get("Date", ""),
    })
M.close()
M.logout()
print(json.dumps(out, indent=2, ensure_ascii=False))
PYEOF
}

# Skicka Telegram-notis via Telegram HTTP API (direkt)
notify() {
    local subject="$1" from="$2" date="$3"
    local text="📧 *Nytt mail till $MAILCOW_USER*

*Från:* $from
*Ämne:* $subject
*Datum:* $date"
    
    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
        log "  TELEGRAM_BOT_TOKEN ej satt — skippar notis"
        return 1
    fi
    
    # Telegram API kräver URL-encoded text
    local response
    response=$(curl -s --max-time 10 "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        --data-urlencode "chat_id=${TELEGRAM_CHAT}" \
        --data-urlencode "text=${text}" \
        --data-urlencode "parse_mode=Markdown" 2>&1)
    
    if echo "$response" | grep -q '"ok":true'; then
        log "  ✅ Notis skickad till Telegram"
    else
        log "  ❌ Telegram API-fel: $(echo "$response" | head -c 200)"
    fi
}

# === Huvudlogik ===
log "Kollar INBOX för $MAILCOW_USER..."

# Hämta nuvarande INBOX
list_inbox > "$TMP_NEW"

# Ladda state (UIDs vi redan sett)
if [ -f "$STATE_FILE" ]; then
    seen_uids=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(' '.join(d.get('seen_uids', [])))" 2>/dev/null || echo "")
else
    seen_uids=""
fi

# Hitta nya mail (som inte finns i seen_uids)
new_count=0
while IFS= read -r line; do
    [ -z "$line" ] && continue
    uid=$(echo "$line" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(d.get('uid',''))" 2>/dev/null || echo "")
    [ -z "$uid" ] && continue
    if [[ " $seen_uids " != *" $uid "* ]]; then
        from=$(echo "$line" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(d.get('from',''))" 2>/dev/null)
        subject=$(echo "$line" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(d.get('subject',''))" 2>/dev/null)
        date=$(echo "$line" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(d.get('date',''))" 2>/dev/null)
        log "  NYTT: $uid — $from — $subject"
        notify "$subject" "$from" "$date"
        new_count=$((new_count + 1))
    fi
done < <(python3 -c "import json; d=json.load(open('$TMP_NEW')); [print(json.dumps(m)) for m in d]")

# Uppdatera state
python3 <<PYEOF
import json
old = {"seen_uids": []}
if "$STATE_FILE" and __import__('os').path.exists("$STATE_FILE"):
    old = json.load(open("$STATE_FILE"))
new = json.load(open("$TMP_NEW"))
old_uids = set(old.get("seen_uids", []))
new_uids = set(m["uid"] for m in new)
all_uids = list(old_uids | new_uids)
state = {"seen_uids": all_uids, "last_check": __import__('datetime').datetime.now().isoformat()}
json.dump(state, open("$STATE_FILE", "w"), indent=2)
PYEOF

rm -f "$TMP_NEW"

if [ $new_count -gt 0 ]; then
    log "Klart. $new_count nya mail notifierade."
else
    log "Klart. Inga nya mail."
fi
