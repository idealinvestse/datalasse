#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

TESTBIN="$TMP/testbin"
mkdir -p "$TESTBIN/lib"
WSROOT="$(dirname "$ROOT_DIR")"
cp "$WSROOT/skills/deep-research/lib/retry.sh" "$WSROOT/skills/deep-research/lib/fallback.sh" "$TESTBIN/lib/"
cp "$WSROOT/skills/deep-research/bin/cache-research" "$TESTBIN/"
chmod +x "$TESTBIN/cache-research"

cat > "$TESTBIN/exa-search" << 'MEXA'
#!/usr/bin/env bash
echo '{"results":[{"title":"Cached Exa","url":"https://cache.example.com","highlights":["hl"]}],"costDollars":{"total":0.005}}'
MEXA
chmod +x "$TESTBIN/exa-search"

cat > "$TESTBIN/serper-search" << 'MSERP'
#!/usr/bin/env bash
echo '{"organic":[{"title":"Serper","link":"https://s.com","snippet":"s"}]}'
MSERP
chmod +x "$TESTBIN/serper-search"

CACHE_DB="$TMP/test-cache.sqlite"
export CACHE_DB
export EXA_BIN="$TESTBIN/exa-search"
export SERPER_BIN="$TESTBIN/serper-search"

CACHE_CMD="$TESTBIN/cache-research"

# Test 1: write + read (TTL=60s)
set +e
out1=$("$CACHE_CMD" "cache test query" --ttl=60s --type=auto --num=5 2>"$TMP/err1.log")
code1=$?
out2=$("$CACHE_CMD" "cache test query" --ttl=60s --type=auto --num=5 2>"$TMP/err2.log")
code2=$?
set -e

if [ $code1 -eq 0 ] && [ $code2 -eq 0 ] && echo "$out1" | jq -e '.results[0].url' >/dev/null; then
  echo "PASS write returns valid json"
else
  echo "FAIL write: $code1 $out1"; exit 1
fi

if grep -q 'CACHE_HIT=1' "$TMP/err2.log" && [ "$out1" = "$out2" ]; then
  echo "PASS cache hit on second read"
else
  echo "FAIL cache hit: err2=$(cat $TMP/err2.log) out1_len=${#out1} out2_len=${#out2}"; exit 1
fi

# Test 2: expire (TTL=1s)
set +e
"$CACHE_CMD" "expire query" --ttl=1s > /dev/null 2>"$TMP/err3.log"
sleep 2
out4=$("$CACHE_CMD" "expire query" --ttl=1s 2>"$TMP/err4.log")
code4=$?
set -e

if ! grep -q 'CACHE_HIT=1' "$TMP/err4.log"; then
  echo "PASS expired entry is cache miss"
else
  echo "FAIL expire: err4=$(cat $TMP/err4.log)"; exit 1
fi

# Test 3: --stats
set +e
stats=$("$CACHE_CMD" --stats 2>&1)
set -e
if echo "$stats" | grep -q 'Cache entries:' && echo "$stats" | grep -q 'Hit rate:'; then
  echo "PASS --stats output"
else
  echo "FAIL --stats: $stats"; exit 1
fi

# Test 4: --clear
set +e
"$CACHE_CMD" "expire query" --ttl=1s > /dev/null 2>/dev/null
sleep 2
"$CACHE_CMD" --clear 2>"$TMP/clear.log"
set -e
if grep -q 'Purged' "$TMP/clear.log"; then
  echo "PASS --clear purges expired"
else
  echo "FAIL --clear: $(cat $TMP/clear.log)"; exit 1
fi

echo "All cache tests passed"
exit 0