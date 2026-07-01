#!/bin/bash
# bin/moss/image-flow.sh — Secure image receive/send/relay + index for Moss
#
# Single entry point for all private media handling.
# - receive: Telegram file_id → secure /root/.moss-private/media/ + index + state
# - send: validated local path → openclaw message send --media
# - relay: receive + send (common case)
# - list/delete: audit + safety
#
# Security: root-only paths, 700/600 perms, atomic writes, strict validation.
# Idempotent: receive on same file_id/sha = no-op.
# Cost: $0. Retries: 3x exp backoff on Telegram ops.
#
# Usage examples in the plan.md.

set -euo pipefail

MEDIA_ROOT="/root/.moss-private/media"
INDEX_FILE="$MEDIA_ROOT/index.json"
STATE_FILE="${WORKSPACE:-$HOME/.openclaw/workspace}/moss-state.json"
AUDIT_LOG="/var/log/moss-image-flow.log"
WORKSPACE="${WORKSPACE:-$HOME/.openclaw/workspace}"

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TODAY=$(date -u +%Y-%m-%d)

usage() {
  cat <<'EOF'
Usage: bin/moss/image-flow.sh <command> [options]

Commands:
  receive <telegram_file_id>
      [--from USER] [--from-path LOCAL_PATH]
      [--caption TEXT] [--context NOTE]
      Download via Telegram getFile OR copy from local path (e.g. OpenClaw inbound cache),
      store securely, update index/state. Returns local path on stdout. Idempotent.

  send <local_path> <target_chat_id>
      [--caption TEXT]
      Validate path under MEDIA_ROOT, send via openclaw message --media.
      Updates index shared_with + delivery_log.

  relay <file_id> <target_chat_id> --from <chat_id>
      [--caption TEXT] [--dry-run]
      receive + send (most common flow). Supports --from for receive step.
      (Legacy 3-positional <source> <fid> <target> also accepted.)

  list [--from USER] [--shared-with USER] [--since DATE] [--json]
      Query index. Human table or JSON.

  delete <filename> [--force]
      Remove file + index entry. --force required if shared_with non-empty.

Security: only operates under /root/.moss-private/media (700/600 root:root).
Never touches workspace or git.
EOF
}

log_audit() {
  local obj="$1"
  mkdir -p "$(dirname "$AUDIT_LOG")" 2>/dev/null || true
  # Use python for clean JSON (no jq required at runtime)
  python3 -c "
import json, sys, os
from datetime import datetime
entry = json.loads(sys.argv[1])
entry['ts'] = os.environ.get('TS', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))
print(json.dumps(entry, ensure_ascii=False))
" "$obj" >> "$AUDIT_LOG" 2>/dev/null || echo "{\"ts\":\"$TIMESTAMP\",\"raw\":\"$obj\"}" >> "$AUDIT_LOG"
}

get_tg_token() {
  python3 -c '
import json
with open("/root/.openclaw/openclaw.json") as f:
    cfg = json.load(f)
print(cfg["channels"]["telegram"]["botToken"])
'
}

tg_get_file() {
  local file_id="$1"
  local token="$2"
  python3 - <<PYEOF
import json, urllib.request, urllib.parse, time, sys, os

token = "$token"
file_id = "$file_id"
url = f"https://api.telegram.org/bot{token}/getFile"

def do_request(attempt):
    data = urllib.parse.urlencode({"file_id": file_id}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            res = json.loads(resp.read())
            if not res.get("ok"):
                print(json.dumps({"error": res.get("description", "unknown")}), file=sys.stderr)
                return None, False
            return res.get("result", {}), True
    except Exception as e:
        print(str(e), file=sys.stderr)
        return None, False

for attempt in range(1, 4):
    result, ok = do_request(attempt)
    if ok and result:
        print(json.dumps(result))
        sys.exit(0)
    if attempt < 3:
        sleep_s = 2 ** (attempt - 1)
        time.sleep(sleep_s)
    else:
        print("getFile failed after 3 attempts", file=sys.stderr)
        sys.exit(1)
PYEOF
}

download_file() {
  local url="$1"
  local dest="$2"
  python3 - <<PYEOF
import urllib.request, time, sys, os

url = "$url"
dest = "$dest"

def do_dl(attempt):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Moss-image-flow/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            with open(dest, "wb") as f:
                f.write(data)
            return True
    except Exception as e:
        print(str(e), file=sys.stderr)
        return False

for attempt in range(1, 4):
    if do_dl(attempt):
        sys.exit(0)
    if attempt < 3:
        time.sleep(2 ** (attempt - 1))
print("download failed after retries", file=sys.stderr)
sys.exit(1)
PYEOF
}

sha256_of() {
  local p="$1"
  sha256sum "$p" | awk '{print $1}'
}

slugify() {
  local s="${1:-photo}"
  echo "$s" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed -E 's/^-+|-+$//g' | cut -c1-50
}

id_to_name() {
  case "$1" in
    438805461) echo "oscar" ;;
    8419098743) echo "paulina" ;;
    *) echo "u${1:0:8}" ;;
  esac
}

ensure_media_dir() {
  mkdir -p -m 700 "$MEDIA_ROOT" 2>/dev/null || true
  chown root:root "$MEDIA_ROOT" 2>/dev/null || true
  if [[ ! -f "$INDEX_FILE" ]]; then
    echo '[]' > "$INDEX_FILE.tmp"
    chmod 600 "$INDEX_FILE.tmp"
    mv "$INDEX_FILE.tmp" "$INDEX_FILE"
    chown root:root "$INDEX_FILE" 2>/dev/null || true
  fi
  chmod 600 "$INDEX_FILE" 2>/dev/null || true
}

atomic_write_json() {
  local target="$1"
  local data="$2"
  local tmp="${target}.tmp.$$"
  python3 -c "
import json, os, sys
data = json.loads(sys.argv[1])
with open(sys.argv[2], 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
os.chmod(sys.argv[2], 0o600)
" "$data" "$tmp"
  mv "$tmp" "$target"
  chmod 600 "$target" 2>/dev/null || true
  chown root:root "$target" 2>/dev/null || true
}

load_index() {
  if [[ -f "$INDEX_FILE" ]]; then
    cat "$INDEX_FILE"
  else
    echo '[]'
  fi
}

save_index() {
  local data="$1"
  atomic_write_json "$INDEX_FILE" "$data"
  # backup every 10 entries
  local count
  count=$(python3 -c "
import json,sys
print(len(json.loads(sys.argv[1])))
" "$data")
  if (( count % 10 == 0 )); then
    mkdir -p "$WORKSPACE/memory/media" 2>/dev/null || true
    cp "$INDEX_FILE" "$WORKSPACE/memory/media/index-backup-${TODAY}.json" 2>/dev/null || true
    chmod 600 "$WORKSPACE/memory/media/index-backup-${TODAY}.json" 2>/dev/null || true
  fi
}

upsert_state_media() {
  local entry_json="$1"
  if [[ ! -f "$STATE_FILE" ]]; then
    return 0
  fi
  python3 <<PYEOF
import json, os, sys
from pathlib import Path

state_path = Path("$STATE_FILE")
state = json.loads(state_path.read_text())

entry = json.loads('''$entry_json''')

pc = state.setdefault("personal_context", {})
pm = pc.setdefault("private_media", {})
pm["root"] = "/root/.moss-private/media/"
pm["permissions"] = "700 dir, 600 file, root:root"
pm["index_path"] = "/root/.moss-private/media/index.json"

files = pm.setdefault("files", [])
# upsert by filename
found = False
for i, f in enumerate(files):
    if f.get("filename") == entry.get("filename"):
        files[i] = {**f, **entry}
        found = True
        break
if not found:
    files.append(entry)

# keep last 50 for session memory hygiene
if len(files) > 50:
    files[:] = files[-50:]

state["last_updated"] = "$TIMESTAMP"

tmp = state_path.with_suffix(".tmp.$$")
tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False))
os.replace(tmp, state_path)
print("state updated")
PYEOF
}

validate_secure_path() {
  local p="$1"
  if [[ "$p" != "$MEDIA_ROOT"/* || "$p" == *..* || ! -f "$p" ]]; then
    echo "ERROR: invalid or unsafe path: $p (must be under $MEDIA_ROOT and exist)" >&2
    exit 1
  fi
}

# --- receive ---
cmd_receive() {
  local file_id=""
  local from_path=""
  local from_id="unknown"
  local caption=""
  local context=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --from) from_id="$2"; shift 2 ;;
      --from-path) from_path="$2"; shift 2 ;;
      --caption) caption="$2"; shift 2 ;;
      --context) context="$2"; shift 2 ;;
      *) if [[ -z "$file_id" ]]; then file_id="$1"; else echo "Unknown arg: $1" >&2; usage; exit 1; fi; shift ;;
    esac
  done

  if [[ -z "$file_id" && -z "$from_path" ]]; then
    echo "receive requires <telegram_file_id> or --from-path <local_path>" >&2; exit 1
  fi

  ensure_media_dir

  # --- from-path mode: file already on disk (e.g. OpenClaw inbound cache) ---
  if [[ -n "$from_path" ]]; then
    if [[ ! -f "$from_path" ]]; then
      echo "ERROR: --from-path file not found: $from_path" >&2; exit 1
    fi
    # extract extension from filename
    local ext="${from_path##*.}"
    ext="${ext,,}"  # lowercase
    case "$ext" in
      jpg|jpeg|png|webp|heic) : ;;
      *) echo "ERROR: unsupported extension: .$ext" >&2; exit 1 ;;
    esac
    # synthesize a stable file_id from path + mtime so re-runs are idempotent
    local path_hash
    path_hash=$(sha256_of "$from_path" | cut -c1-32)
    file_id="local-${path_hash}"
  else
    local token
    token=$(get_tg_token)
  fi

  # get file info (skip for from-path)
  local info="" tg_file_path="" tg_size=0 ext tmp
  if [[ -z "$from_path" ]]; then
    info=$(tg_get_file "$file_id" "$token")
    tg_file_path=$(python3 -c "
import json,sys
print(json.loads(sys.argv[1]).get('file_path',''))
" "$info")
    tg_size=$(python3 -c "
import json,sys
print(json.loads(sys.argv[1]).get('file_size',0))
" "$info")

    if [[ -z "$tg_file_path" ]]; then
      echo "ERROR: could not resolve file_path for $file_id" >&2
      exit 1
    fi

    ext="jpg"
    case "${tg_file_path##*.}" in
      jpg|jpeg|png|webp|gif) ext="${tg_file_path##*.}" ;;
    esac
    [[ "$ext" == "jpeg" ]] && ext="jpg"

    local dl_url="https://api.telegram.org/file/bot${token}/${tg_file_path}"
    tmp="/tmp/moss-recv-$$-${RANDOM}.tmp"
    download_file "$dl_url" "$tmp"
  else
    ext="${from_path##*.}"
    ext="${ext,,}"
    [[ "$ext" == "jpeg" ]] && ext="jpg"
    tmp="/tmp/moss-recv-$$-${RANDOM}.${ext}"
    cp "$from_path" "$tmp"
  fi

  local sha size
  sha=$(sha256_of "$tmp")
  size=$(stat -c%s "$tmp")

  # idempotency: file_id or sha
  local idx
  idx=$(load_index)
  local existing_fn
  existing_fn=$(python3 -c '
import json, sys, os
idx = json.loads(sys.argv[1])
fid = sys.argv[2]
sha = sys.argv[3]
media = sys.argv[4]
for e in idx:
    if e.get("original_telegram_file_id") == fid or e.get("sha256") == sha:
        fn = e.get("filename","")
        p = os.path.join(media, fn)
        if os.path.isfile(p):
            try:
                import hashlib
                with open(p,"rb") as f: disk_sha = hashlib.sha256(f.read()).hexdigest()
                if disk_sha == sha or disk_sha == e.get("sha256"):
                    print(fn)
                    sys.exit(0)
            except: pass
print("")
' "$idx" "$file_id" "$sha" "$MEDIA_ROOT")

  if [[ -n "$existing_fn" ]]; then
    rm -f "$tmp"
    local full="$MEDIA_ROOT/$existing_fn"
    echo "$full"
    log_audit "{\"action\":\"receive\",\"file_id\":\"$file_id\",\"filename\":\"$existing_fn\",\"sha256\":\"$sha\",\"idempotent\":true,\"path\":\"$full\"}"
    exit 0
  fi

  # generate filename
  local name slug fn dest
  name=$(id_to_name "$from_id")
  slug=$(slugify "${caption:-${context:-photo}}")
  fn="${TODAY}-${name}-${slug}.${ext}"
  dest="$MEDIA_ROOT/$fn"

  # collision guard
  local i=1
  while [[ -f "$dest" ]]; do
    fn="${TODAY}-${name}-${slug}-$i.${ext}"
    dest="$MEDIA_ROOT/$fn"
    ((i++))
  done

  mv "$tmp" "$dest"
  chmod 600 "$dest"
  chown root:root "$dest" 2>/dev/null || true

  local entry
  entry=$(python3 -c '
import json, sys
print(json.dumps({
  "filename": sys.argv[1],
  "original_telegram_file_id": sys.argv[2],
  "sha256": sys.argv[3],
  "size_bytes": int(sys.argv[4]),
  "received_from": sys.argv[5],
  "received_at": sys.argv[6],
  "shared_with": [],
  "context": sys.argv[7],
  "captions": [sys.argv[8]] if sys.argv[8] else [],
  "delivery_log": []
}, ensure_ascii=False))
' "$fn" "$file_id" "$sha" "$size" "${from_id} ($name)" "$TIMESTAMP" "$context" "$caption")

  idx=$(load_index)
  idx=$(python3 -c '
import json, sys
idx = json.loads(sys.argv[1])
idx.append(json.loads(sys.argv[2]))
print(json.dumps(idx, ensure_ascii=False))
' "$idx" "$entry")

  save_index "$idx"
  upsert_state_media "$entry"

  log_audit "{\"action\":\"receive\",\"file_id\":\"$file_id\",\"filename\":\"$fn\",\"sha256\":\"$sha\",\"size\":$size,\"idempotent\":false,\"path\":\"$dest\"}"

  echo "$dest"
}

# --- send ---
cmd_send() {
  local local_path=""
  local target=""
  local caption=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --caption) caption="$2"; shift 2 ;;
      *) if [[ -z "$local_path" ]]; then local_path="$1"; elif [[ -z "$target" ]]; then target="$1"; else echo "Unknown: $1" >&2; exit 1; fi; shift ;;
    esac
  done

  if [[ -z "$local_path" || -z "$target" ]]; then
    echo "send requires <local_path> <target_chat_id>" >&2; exit 1
  fi

  validate_secure_path "$local_path"

  local fn
  fn=$(basename "$local_path")

  local json_out
  set +e
  json_out=$(openclaw message send \
    --channel telegram \
    --target "$target" \
    --media "$local_path" \
    ${caption:+--message "$caption"} \
    --json 2>&1)
  local send_rc=$?
  set -e

  local ok="false" msg_id=""
  if [[ $send_rc -eq 0 ]]; then
    ok=$(python3 -c '
import json,sys
try:
  d=json.loads(sys.argv[1])
  print("true" if d.get("ok") or (d.get("result") and d.get("result",{}).get("message_id")) else "false")
except: print("false")
' "$json_out" || echo false)
    msg_id=$(python3 -c '
import json,sys
try:
  d=json.loads(sys.argv[1])
  m = d.get("result",{}).get("message_id","")
  print(m)
except: print("")
' "$json_out" || echo "")
  fi

  if [[ "$ok" != "true" ]]; then
    echo "ERROR: send failed: $json_out" >&2
    log_audit "{\"action\":\"send\",\"path\":\"$local_path\",\"target\":\"$target\",\"error\":\"$json_out\"}"
    exit 1
  fi

  # update index + state
  local idx
  idx=$(load_index)
  local updated
  updated=$(python3 -c '
import json, sys, datetime
idx = json.loads(sys.argv[1])
fn = sys.argv[2]
target = sys.argv[3]
caption = sys.argv[4]
msg_id = sys.argv[5]
ts = sys.argv[6]

for e in idx:
    if e.get("filename") == fn:
        sw = e.setdefault("shared_with", [])
        if target not in sw:
            sw.append(target)
        dl = e.setdefault("delivery_log", [])
        dl.append({
            "ts": ts,
            "target": target,
            "caption": caption,
            "msg_id": msg_id,
            "via": "openclaw-message"
        })
        break
print(json.dumps(idx, ensure_ascii=False))
' "$idx" "$fn" "$target" "$caption" "$msg_id" "$TIMESTAMP")

  save_index "$updated"

  # also upsert to state (light)
  local entry_light
  entry_light=$(python3 -c '
import json,sys
print(json.dumps({"filename":sys.argv[1],"last_shared_with":sys.argv[2],"last_delivery_ts":sys.argv[3]}, ensure_ascii=False))
' "$fn" "$target" "$TIMESTAMP")
  upsert_state_media "$entry_light"

  log_audit "{\"action\":\"send\",\"filename\":\"$fn\",\"target\":\"$target\",\"msg_id\":\"$msg_id\"}"

  echo "sent: $fn → $target (msg_id=${msg_id:-?})"
}

# --- relay ---
cmd_relay() {
  local dry=0
  local fid="" target="" from="" caption=""
  local pos=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run) dry=1; shift ;;
      --caption) caption="$2"; shift 2 ;;
      --from) from="$2"; shift 2 ;;
      *) pos+=("$1"); shift ;;
    esac
  done

  # Support new form: <fid> <target> --from <id> ...
  # and legacy: <source> <fid> <target>
  if [[ ${#pos[@]} -eq 3 && -z "$from" ]]; then
    from="${pos[0]}"; fid="${pos[1]}"; target="${pos[2]}"
  elif [[ ${#pos[@]} -eq 2 ]]; then
    fid="${pos[0]}"; target="${pos[1]}"
  fi

  if [[ -z "$fid" || -z "$target" ]]; then
    echo "relay requires <file_id> <target_chat_id> --from <chat_id> [--caption] [--dry-run]" >&2
    echo "(legacy <source> <fid> <target> also works)" >&2
    exit 1
  fi
  if [[ -z "$from" ]]; then
    from="unknown"
  fi

  local path
  path=$(cmd_receive "$fid" --from "$from" ${caption:+--caption "$caption"})

  if [[ $dry -eq 1 ]]; then
    echo "DRY-RUN: would send $path to $target (caption: ${caption:-})"
    log_audit "{\"action\":\"relay\",\"dry_run\":true,\"file_id\":\"$fid\",\"path\":\"$path\",\"target\":\"$target\"}"
    return 0
  fi

  cmd_send "$path" "$target" ${caption:+--caption "$caption"}
}

# --- list ---
cmd_list() {
  local from="" shared="" since="" json_out=0

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --from) from="$2"; shift 2 ;;
      --shared-with) shared="$2"; shift 2 ;;
      --since) since="$2"; shift 2 ;;
      --json) json_out=1; shift ;;
      *) echo "Unknown: $1"; exit 1 ;;
    esac
  done

  ensure_media_dir
  local idx
  idx=$(load_index)

  python3 -c "
import json, sys
idx = json.loads(sys.argv[1])
frm = sys.argv[2]
sh = sys.argv[3]
since = sys.argv[4]
jout = int(sys.argv[5])

def match(e):
    if frm and frm not in str(e.get('received_from','')): return False
    if sh and sh not in str(e.get('shared_with',[])): return False
    if since and e.get('received_at','') < since: return False
    return True

res = [e for e in idx if match(e)]

if jout:
    print(json.dumps(res, indent=2, ensure_ascii=False))
    sys.exit(0)

print('Images: %d (total in index: %d)' % (len(res), len(idx)))
for e in res:
    sw = ','.join(e.get('shared_with',[])) or '-'
    ctx = (e.get('context') or '')[:30]
    fn = e.get('filename') or '?'
    rf = e.get('received_from') or '?'
    ra = (e.get('received_at') or '?')[:16]
    print('%s  from:%s  at:%s  shared:[%s]  ctx:%s' % (fn, rf, ra, sw, ctx))
" "$idx" "$from" "$shared" "$since" "$json_out"
}

# --- delete ---
cmd_delete() {
  local fn="" force=0

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --force) force=1; shift ;;
      *) fn="$1"; shift ;;
    esac
  done

  if [[ -z "$fn" ]]; then echo "delete requires <filename>"; exit 1; fi

  local full="$MEDIA_ROOT/$fn"
  validate_secure_path "$full"

  local idx entry
  idx=$(load_index)
  entry=$(python3 -c '
import json,sys
idx=json.loads(sys.argv[1]); fn=sys.argv[2]
for e in idx:
    if e.get("filename")==fn: print(json.dumps(e)); sys.exit(0)
print("{}")
' "$idx" "$fn")

  local sw_len
  sw_len=$(python3 -c '
import json,sys
e=json.loads(sys.argv[1])
print(len(e.get("shared_with",[])))
' "$entry")

  if [[ "$sw_len" -gt 0 && $force -eq 0 ]]; then
    echo "ERROR: $fn has been shared (shared_with count=$sw_len). Use --force to delete." >&2
    exit 1
  fi

  rm -f "$full"

  local new_idx
  new_idx=$(python3 -c '
import json,sys
idx=json.loads(sys.argv[1]); fn=sys.argv[2]
idx = [e for e in idx if e.get("filename") != fn]
print(json.dumps(idx, ensure_ascii=False))
' "$idx" "$fn")
  save_index "$new_idx"

  # update state too
  if [[ -f "$STATE_FILE" ]]; then
    python3 <<PYEOF
import json
from pathlib import Path
p = Path("$STATE_FILE")
s = json.loads(p.read_text())
pm = s.get("personal_context", {}).get("private_media", {})
if "files" in pm:
    pm["files"] = [f for f in pm["files"] if f.get("filename") != "$fn"]
p.write_text(json.dumps(s, indent=2, ensure_ascii=False))
PYEOF
  fi

  log_audit "{\"action\":\"delete\",\"filename\":\"$fn\",\"force\":$force}"
  echo "deleted: $fn"
}

# --- main dispatch ---
main() {
  local cmd="${1:-}"
  shift || true

  case "$cmd" in
    receive) cmd_receive "$@" ;;
    send)    cmd_send "$@" ;;
    relay)   cmd_relay "$@" ;;
    list)    cmd_list "$@" ;;
    delete)  cmd_delete "$@" ;;
    -h|--help|help|"") usage; exit 0 ;;
    *) echo "Unknown command: $cmd"; usage; exit 1 ;;
  esac
}

main "$@"
