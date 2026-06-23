#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

TESTBIN="$TMP/testbin"
mkdir -p "$TESTBIN/lib"
cp "$ROOT_DIR/lib/retry.sh" "$ROOT_DIR/lib/fallback.sh" "$TESTBIN/lib/"

SERPER_LOG="$TMP/serper-calls.log"
touch "$SERPER_LOG"

# Mock exa-search: fails with 401 when MOCK_EXA_FAIL=1
cat > "$TESTBIN/exa-search" << 'MEXA'
#!/usr/bin/env bash
if [ "${MOCK_EXA_FAIL:-0}" = "1" ] || [ "${EXA_API_KEY:-}" = "invalid" ]; then
  echo '{"error":"401 unauthorized invalid api key"}' >&2
  exit 2
fi
echo '{"results":[{"title":"Exa Result","url":"https://exa.example.com","highlights":["hl"]}],"costDollars":{"total":0.007}}'
MEXA
chmod +x "$TESTBIN/exa-search"

# Mock serper-search: logs calls
cat > "$TESTBIN/serper-search" << MSERP
#!/usr/bin/env bash
echo "CALLED" >> "$SERPER_LOG"
echo '{"organic":[{"title":"Serper Result","link":"https://serper.example.com","snippet":"snippet text"}]}'
MSERP
chmod +x "$TESTBIN/serper-search"

OUT="$TMP/out.json"
export EXA_BIN="$TESTBIN/exa-search"
export SERPER_BIN="$TESTBIN/serper-search"

# shellcheck source=../lib/fallback.sh
source "$TESTBIN/lib/fallback.sh"

# Test 1: Exa succeeds (ensure valid key for this case)
: > "$SERPER_LOG"
unset MOCK_EXA_FAIL
EXA_API_KEY="valid-test-key"
export EXA_API_KEY
if search_with_fallback "test query" auto 5 "$OUT"; then
  prov=$(jq -r '.provider' "$OUT")
  url=$(jq -r '.results[0].url' "$OUT")
  if [ "$prov" = "exa" ] && [ "$url" = "https://exa.example.com" ] && [ ! -s "$SERPER_LOG" ]; then
    echo "PASS exa success no serper call"
  else
    echo "FAIL exa success: prov=$prov url=$url serper_log=$(cat $SERPER_LOG)"; exit 1
  fi
else
  echo "FAIL exa success call failed"; exit 1
fi

# Test 2: Exa fails -> Serper fallback
: > "$SERPER_LOG"
MOCK_EXA_FAIL=1
export MOCK_EXA_FAIL
if search_with_fallback "fallback query" deep 5 "$OUT" 2>"$TMP/fb.log"; then
  prov=$(jq -r '.provider' "$OUT")
  url=$(jq -r '.results[0].url' "$OUT")
  if [ "$prov" = "serper" ] && [ "$url" = "https://serper.example.com" ] && grep -q CALLED "$SERPER_LOG"; then
    echo "PASS exa fail serper fallback"
  else
    echo "FAIL fallback: prov=$prov url=$url log=$(cat $SERPER_LOG)"; exit 1
  fi
  if grep -q 'falling back to Serper' "$TMP/fb.log"; then
    echo "PASS fallback logged to stderr"
  else
    echo "FAIL fallback log missing"; exit 1
  fi
else
  echo "FAIL fallback call"; exit 1
fi

# Test 3: invalid EXA_API_KEY env (also matches verification: EXA_API_KEY=invalid bin/tests/test-fallback.sh)
: > "$SERPER_LOG"
unset MOCK_EXA_FAIL
EXA_API_KEY="invalid"
export EXA_API_KEY
if search_with_fallback "invalid key query" auto 5 "$OUT"; then
  prov=$(jq -r '.provider' "$OUT")
  if [ "$prov" = "serper" ] && grep -q CALLED "$SERPER_LOG"; then
    echo "PASS invalid EXA_API_KEY uses serper"
  else
    echo "FAIL invalid key: prov=$prov"; exit 1
  fi
else
  echo "FAIL invalid key fallback"; exit 1
fi

echo "All fallback tests passed"
exit 0