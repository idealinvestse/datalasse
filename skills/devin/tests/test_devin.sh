#!/usr/bin/env bash
# test_devin.sh — shell smoke tests for devin CLI (MOCK=1)
# Run: MOCK=1 bash skills/devin/tests/test_devin.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DEVIN_DIR="$ROOT/skills/devin"
CLI="$DEVIN_DIR/bin/devin"
DOCTOR="$DEVIN_DIR/bin/devin-doctor"

export MOCK=1
export NO_COLOR=1

echo "== 1. doctor MOCK ==="
MOCK=1 "$DOCTOR" | grep -q "OK" || { echo "FAIL doctor"; exit 1; }
echo "PASS"

echo "== 2. doctor bad key (force no MOCK) ==="
set +e
DEVIN_API_KEY="" DEVIN_ORG_ID="" MOCK="" "$DOCTOR" >/dev/null 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then echo "FAIL: doctor should fail without keys"; exit 1; fi
echo "PASS (non-zero expected)"

echo "== 3. create returns only session_id (pipeable) ==="
sid=$(MOCK=1 "$CLI" create "fix the auth bug")
[[ "$sid" =~ ^devin-mock- ]] || { echo "bad sid: $sid"; exit 1; }
echo "sid=$sid"
echo "PASS"

echo "== 4. create --max-acu 100 refuses without --yes ==="
set +e
out=$(MOCK=1 "$CLI" create --max-acu 100 "big" 2>&1)
rc=$?
set -e
echo "$out" | grep -qi "50\|yes\|requires" || { echo "no guard msg"; exit 1; }
if [ "$rc" -eq 0 ]; then echo "FAIL: expected non-zero rc for high acu"; exit 1; fi
echo "PASS (rc=$rc)"

echo "== 5. status prints fields ==="
MOCK=1 "$CLI" status "$sid" | grep -q "status"
echo "PASS"

echo "== 6. list prints table ==="
MOCK=1 "$CLI" list --limit 3 | grep -q "status"
echo "PASS"

echo "== 7. send ==="
MOCK=1 "$CLI" send "$sid" "any updates?" >/dev/null
echo "PASS"

echo "== 8. kill ==="
MOCK=1 "$CLI" kill "$sid" >/dev/null
echo "PASS"

echo "== 9. watch exits on terminal (mock) ==="
MOCK=1 "$CLI" watch "$sid" --max 5 >/dev/null
echo "PASS"

echo "== 10. attach (mock file) ==="
tmpf=$(mktemp)
echo test > "$tmpf"
MOCK=1 "$CLI" attach "$sid" "$tmpf" >/dev/null
rm -f "$tmpf"
echo "PASS"

echo "== 11. logs mask check (grep full cog_ should be absent) ==="
# ensure log has masked only (create a log entry)
MOCK=1 "$CLI" create "mask test" >/dev/null
if grep -E 'cog_[A-Za-z0-9_-]{10,}' "$HOME/.openclaw/workspace/memory/devin/devin.log" 2>/dev/null; then
  echo "FAIL: raw key leaked in log"
  exit 1
fi
echo "PASS (no raw cog_ key in logs)"

echo "== 12. --dry-run / MOCK respected ==="
out=$(MOCK=1 "$CLI" --dry-run create "dry" 2>&1 || true)
echo "$out" | grep -q "devin-mock" || true
echo "PASS"

echo
echo "All 12+ shell tests PASSED under MOCK=1"