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
if [[ "$*" == *"openrouter.ai/api/v1/chat/completions"* ]]; then
  # Return content that contains a JSON array (decomp handles markdown strip)
  echo '{"choices":[{"message":{"content":"[{\"query\":\"foo bar\",\"type\":\"deep\",\"max_results\":4,\"rationale\":\"test subq\",\"output_schema\":null}]"}}]}'
else
  echo '{}'
fi
MOCKCURL
chmod +x "$MOCKDIR/curl"

# missing arg
set +e
out=$(OPENROUTER_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$ROOT_DIR/research-decompose" 2>&1); code=$?
set -e
if [ $code -eq 1 ] && echo "$out" | grep -qi "Usage"; then
  echo "PASS missing"
else
  echo "FAIL missing: $code $out"; exit 1
fi

# happy basic
set +e
out=$(OPENROUTER_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$ROOT_DIR/research-decompose" "test question" 2>&1); code=$?
set -e
if [ $code -eq 0 ] && echo "$out" | jq -e 'type == "array" and length >= 1 and .[0].type and .[0].query' >/dev/null; then
  echo "PASS happy"
else
  echo "FAIL happy: $code out=$out"; exit 1
fi

# --num , --raw
set +e
out=$(OPENROUTER_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$ROOT_DIR/research-decompose" "q" --num=2 --raw 2>&1); code=$?
set -e
if [ $code -eq 0 ] && echo "$out" | grep -q 'foo bar'; then
  echo "PASS num+raw"
else
  echo "FAIL num+raw"; exit 1
fi

# jq array shape
set +e
out=$(OPENROUTER_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$ROOT_DIR/research-decompose" "q2" 2>&1); code=$?
set -e
if [ $code -eq 0 ] && echo "$out" | jq -e 'type == "array"' >/dev/null; then
  echo "PASS json array"
else
  echo "FAIL json array"; exit 1
fi

echo "All research-decompose tests passed"
exit 0
