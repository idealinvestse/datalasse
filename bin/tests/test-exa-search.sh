#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

MOCKDIR="$TMP/bin"
mkdir -p "$MOCKDIR"

cat > "$MOCKDIR/curl" << 'MOCKCURL'
#!/usr/bin/env bash
# Mock curl for exa-search tests
if [[ "$*" == *"api.exa.ai/search"* ]]; then
  if [ "${MOCK_EXA_ERROR:-0}" = "1" ] || [[ "$*" == *"badkey"* ]]; then
    echo '{"error": "Invalid API key"}'
  else
    echo '{"results":[{"title":"Mock Title","url":"https://example.com","highlights":["mock hl"],"score":0.95}],"costDollars":{"total":0.007}}'
  fi
else
  echo '{}'
fi
MOCKCURL
chmod +x "$MOCKDIR/curl"

# Copy target + strip PATH reset so mock curl wins
TESTBIN="$TMP/tbin"
mkdir -p "$TESTBIN"
cp "$ROOT_DIR/exa-search" "$TESTBIN/exa-search"
sed -i '/^export PATH=.*local/d; /^export PATH=.*usr/d' "$TESTBIN/exa-search" || true
chmod +x "$TESTBIN/exa-search"

# 1. missing args
set +e
out=$(EXA_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$TESTBIN/exa-search" 2>&1); code=$?
set -e
if [ $code -eq 1 ] && echo "$out" | grep -q "Usage"; then
  echo "PASS missing args"
else
  echo "FAIL missing args: code=$code out=$out"; exit 1
fi

# 2. no key
# HOME=$TMP prevents exa-search from sourcing real secrets.env as fallback
set +e
out=$(EXA_API_KEY= HOME="$TMP" PATH="$MOCKDIR:$PATH" "$TESTBIN/exa-search" "q" 2>&1); code=$?
set -e
if [ $code -eq 1 ] && echo "$out" | grep -q "EXA_API_KEY not set"; then
  echo "PASS no key"
else
  echo "FAIL no key: code=$code out=$out"; exit 1
fi

# 3. invalid key -> api error path
set +e
out=$(MOCK_EXA_ERROR=1 EXA_API_KEY=badkey HOME="$TMP" PATH="$MOCKDIR:$PATH" "$TESTBIN/exa-search" "q" 2>&1); code=$?
set -e
if [ $code -eq 2 ] && echo "$out" | grep -q "Exa API error\|Exa /search error"; then
  echo "PASS invalid key error"
else
  echo "FAIL invalid key: code=$code out=$out"; exit 1
fi

# 4. happy path (with --json so we can validate schema)
# Note: exa-search --json outputs .results array (not the full response with costDollars)
set +e
out=$(EXA_API_KEY=dummy HOME="$TMP" PATH="$MOCKDIR:$PATH" "$TESTBIN/exa-search" "test query" --count=3 --json 2>&1); code=$?
set -e
if [ $code -eq 0 ] && echo "$out" | jq -e '.[0].url and .[0].title' >/dev/null 2>&1; then
  echo "PASS happy"
else
  echo "FAIL happy: code=$code out=$out"; exit 1
fi

# 5. --json and --type=keyword parse (at least runs)
# Note: exa-search has no --pretty (output is markdown by default, --json for compact)
set +e
out=$(EXA_API_KEY=dummy HOME="$TMP" PATH="$MOCKDIR:$PATH" "$TESTBIN/exa-search" "q2" --json --type=keyword 2>&1); code=$?
set -e
if [ $code -eq 0 ] && echo "$out" | jq -e . >/dev/null 2>&1; then
  echo "PASS pretty+type"
else
  echo "FAIL pretty+type: code=$code out=$out"; exit 1
fi

# 6. compact markdown valid (default format, just check exit code)
set +e
out=$(EXA_API_KEY=dummy HOME="$TMP" PATH="$MOCKDIR:$PATH" "$TESTBIN/exa-search" "q3" 2>&1); code=$?
set -e
if [ $code -eq 0 ]; then
  echo "PASS compact markdown"
else
  echo "FAIL compact markdown: code=$code out=$out"; exit 1
fi

echo "All exa-search tests passed"
exit 0
