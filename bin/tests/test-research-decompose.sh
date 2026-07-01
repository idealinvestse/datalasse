#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

MOCKDIR="$TMP/bin"
mkdir -p "$MOCKDIR"

cat > "$MOCKDIR/llm-call" << 'MOCKLLM'
#!/usr/bin/env bash
# Mock for research-decompose test (returns .content with JSON array)
echo '{"content": "[{\"query\":\"foo bar\",\"type\":\"deep\",\"max_results\":4,\"rationale\":\"test subq\",\"output_schema\":null}]" }'
MOCKLLM
chmod +x "$MOCKDIR/llm-call"

# Setup a cwd dir with ./bin/llm-call so that decompose's "bin/llm-call" relative resolves to mock
MOCKCWD="$TMP/mockcwd"
mkdir -p "$MOCKCWD/bin"
cp "$MOCKDIR/llm-call" "$MOCKCWD/bin/llm-call"
chmod +x "$MOCKCWD/bin/llm-call"

# missing arg
set +e
out=$(cd "$MOCKCWD" && OPENROUTER_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$ROOT_DIR/research-decompose" 2>&1); code=$?
set -e
if [ $code -eq 1 ] && echo "$out" | grep -qi "Usage"; then
  echo "PASS missing"
else
  echo "FAIL missing: $code $out"; exit 1
fi

# happy basic
set +e
out=$(cd "$MOCKCWD" && OPENROUTER_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$ROOT_DIR/research-decompose" "test question" 2>&1); code=$?
set -e
if [ $code -eq 0 ] && echo "$out" | jq -e 'type == "array" and length >= 1 and .[0].type and .[0].query' >/dev/null; then
  echo "PASS happy"
else
  echo "FAIL happy: $code out=$out"; exit 1
fi

# --num , --raw
set +e
out=$(cd "$MOCKCWD" && OPENROUTER_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$ROOT_DIR/research-decompose" "q" --num=2 --raw 2>&1); code=$?
set -e
if [ $code -eq 0 ] && echo "$out" | grep -q 'foo bar'; then
  echo "PASS num+raw"
else
  echo "FAIL num+raw"; exit 1
fi

# jq array shape
set +e
out=$(cd "$MOCKCWD" && OPENROUTER_API_KEY=dummy PATH="$MOCKDIR:$PATH" "$ROOT_DIR/research-decompose" "q2" 2>&1); code=$?
set -e
if [ $code -eq 0 ] && echo "$out" | jq -e 'type == "array"' >/dev/null; then
  echo "PASS json array"
else
  echo "FAIL json array"; exit 1
fi

echo "All research-decompose tests passed"
exit 0
