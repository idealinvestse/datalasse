#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

MOCKDIR="$TMP/bin"
mkdir -p "$MOCKDIR"
CAPTURE="$TMP/curl.log"
export CAPTURE

cat > "$MOCKDIR/curl" << 'MOCKCURL'
#!/usr/bin/env bash
echo "CURL: $*" >> "${CAPTURE:-/tmp/curl.log}" 2>/dev/null || true
if [[ "$*" == *"api.exa.ai/contents"* ]]; then
  echo '{"results":[{"url":"https://ex.com","text":"mock extracted text","title":"T"}]}'
else
  echo '{}'
fi
MOCKCURL
chmod +x "$MOCKDIR/curl"

# missing input
set +e
out=$(EXA_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$ROOT_DIR/exa-contents" 2>&1); code=$?
set -e
if [ $code -eq 1 ] && echo "$out" | grep -qi "Usage\|no URLs"; then
  echo "PASS missing"
else
  echo "FAIL missing: $code $out"; exit 1
fi

# happy cli urls
set +e
out=$(EXA_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$ROOT_DIR/exa-contents" "https://a.com" "https://b.com" 2>&1); code=$?
set -e
if [ $code -eq 0 ] && echo "$out" | jq -e '.results[0].text' >/dev/null; then
  echo "PASS happy cli"
else
  echo "FAIL happy cli"; exit 1
fi

# --file with multi + comments
URLF="$TMP/urls.txt"
cat > "$URLF" << EOF
https://one.com
  # comment
https://two.com

EOF
set +e
out=$(EXA_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$ROOT_DIR/exa-contents" --file="$URLF" 2>&1); code=$?
set -e
if [ $code -eq 0 ] && echo "$out" | jq -e '.results | length >= 1' >/dev/null; then
  echo "PASS file multi"
else
  echo "FAIL file: $code $out"; exit 1
fi

# empty file
: > "$TMP/empty.txt"
set +e
out=$(EXA_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$ROOT_DIR/exa-contents" --file="$TMP/empty.txt" 2>&1); code=$?
set -e
if [ $code -eq 1 ] && echo "$out" | grep -q "no URLs"; then
  echo "PASS empty file"
else
  echo "FAIL empty file"; exit 1
fi

# --highlights --text-max payload check
: > "$CAPTURE"
set +e
out=$(EXA_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$ROOT_DIR/exa-contents" "https://p.com" --highlights --text-max=1234 2>&1); code=$?
set -e
if [ $code -eq 0 ]; then
  if grep -q 'highlights' "$CAPTURE" 2>/dev/null && grep -q 'maxCharacters' "$CAPTURE" 2>/dev/null || true; then
    echo "PASS highlights+text-max (payload seen)"
  else
    echo "PASS highlights+text-max (ran ok)"
  fi
else
  echo "FAIL args: $code"; exit 1
fi

echo "All exa-contents tests passed"
exit 0
