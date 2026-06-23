#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

MOCKDIR="$TMP/bin"
mkdir -p "$MOCKDIR"
CAPTURE="$TMP/calls.log"
touch "$CAPTURE"
export CAPTURE

cat > "$MOCKDIR/curl" << 'MOCKCURL'
#!/usr/bin/env bash
CAPTURE="${CAPTURE:-/tmp/calls.log}"
echo "SERPER_CALL: $*" >> "$CAPTURE" 2>/dev/null || true
if [[ "$*" == *"google.serper.dev"* ]]; then
  if [ "${MOCK_SERPER_ERROR:-0}" = "1" ]; then
    echo '{"message": "Invalid API key"}'
  else
    echo '{"organic":[{"title":"S1","link":"https://s1.com","snippet":"snip"}],"searchParameters":{"q":"q"}}'
  fi
else
  echo '{}'
fi
MOCKCURL
chmod +x "$MOCKDIR/curl"

# Copy target + strip PATH reset so mock curl wins
TESTBIN="$TMP/tbin"
mkdir -p "$TESTBIN"
cp "$ROOT_DIR/serper-search" "$TESTBIN/serper-search"
sed -i '/^export PATH=.*local/d; /^export PATH=.*usr/d' "$TESTBIN/serper-search" || true
chmod +x "$TESTBIN/serper-search"

# 1. missing
set +e
out=$(SERPER_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$TESTBIN/serper-search" 2>&1); code=$?
set -e
if [ $code -eq 1 ] && echo "$out" | grep -qi "no query\|Usage"; then
  echo "PASS missing"
else
  echo "FAIL missing: $code $out"; exit 1
fi

# 2. invalid key -> .message path
set +e
out=$(MOCK_SERPER_ERROR=1 SERPER_API_KEY=bad PATH="$MOCKDIR:$PATH" "$TESTBIN/serper-search" "q" 2>&1); code=$?
set -e
if [ $code -ne 0 ] && echo "$out" | grep -q "Serper API error\|message"; then
  echo "PASS invalid key"
else
  echo "FAIL invalid key: $code $out"; exit 1
fi

# 3. endpoint matrix (assert by capture log containing constructed path)
for t in news images scholar; do
  : > "$CAPTURE"
  set +e
  out=$(SERPER_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$TESTBIN/serper-search" "q" --type="$t" 2>&1); code=$?
  set -e
  if [ $code -eq 0 ] && grep -q "google.serper.dev/$t" "$CAPTURE"; then
    echo "PASS type=$t"
  else
    echo "FAIL type=$t code=$code cap=$(cat $CAPTURE) out=$out"; exit 1
  fi
done

# 4. happy
set +e
out=$(SERPER_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$TESTBIN/serper-search" "happy q" 2>&1); code=$?
set -e
if [ $code -eq 0 ] && echo "$out" | jq -e '.organic[0].link' >/dev/null; then
  echo "PASS happy"
else
  echo "FAIL happy"; exit 1
fi

# 5. pretty vs compact
set +e
outp=$(SERPER_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$TESTBIN/serper-search" "p" --pretty 2>&1); codep=$?
outc=$(SERPER_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$TESTBIN/serper-search" "c" 2>&1); codec=$?
set -e
if [ $codep -eq 0 ] && [ $codec -eq 0 ] && echo "$outp" | jq -e . >/dev/null && echo "$outc" | jq -e . >/dev/null; then
  # pretty has more whitespace typically
  echo "PASS pretty/compact"
else
  echo "FAIL pretty"; exit 1
fi

echo "All serper-search tests passed"
exit 0
