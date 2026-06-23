#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# shellcheck source=../lib/retry.sh
source "$ROOT_DIR/lib/retry.sh"

# Mock: fails N times then succeeds
cat > "$TMP/flaky-cmd" << 'MOCK'
#!/usr/bin/env bash
COUNT_FILE="${COUNT_FILE:?}"
count=$(cat "$COUNT_FILE" 2>/dev/null || echo 0)
count=$((count + 1))
echo "$count" > "$COUNT_FILE"
if [ "$count" -lt 3 ]; then
  echo "transient timeout error" >&2
  exit 28
fi
echo '{"ok":true}'
MOCK
chmod +x "$TMP/flaky-cmd"

COUNT_FILE="$TMP/count"
echo 0 > "$COUNT_FILE"

# Test 1: fails 2x then succeeds
set +e
out=$(COUNT_FILE="$COUNT_FILE" retry_with_backoff 3 1 "$TMP/flaky-cmd" 2>&1)
code=$?
set -e
if [ $code -eq 0 ] && echo "$out" | grep -q '"ok":true' && echo "$out" | grep -q 'retry attempt'; then
  echo "PASS flaky succeeds after retries"
else
  echo "FAIL flaky: code=$code out=$out"; exit 1
fi

# Mock: always transient failure
cat > "$TMP/always-fail" << 'MOCK2'
#!/usr/bin/env bash
echo "503 service unavailable" >&2
exit 2
MOCK2
chmod +x "$TMP/always-fail"

# Test 2: always transient -> 3 attempts
set +e
start=$SECONDS
out=$(retry_with_backoff 3 1 "$TMP/always-fail" 2>&1)
code=$?
elapsed=$((SECONDS - start))
set -e
if [ $code -eq 1 ] && echo "$out" | grep -q 'retry attempt 1/3' && echo "$out" | grep -q 'retry attempt 2/3'; then
  echo "PASS always-fail exits 1 after 3 attempts"
else
  echo "FAIL always-fail: code=$code out=$out"; exit 1
fi
if [ "$elapsed" -ge 3 ]; then
  echo "PASS timing >= 3s (elapsed=${elapsed}s)"
else
  echo "FAIL timing: elapsed=${elapsed}s expected >=3"; exit 1
fi

# Mock: permanent 401
cat > "$TMP/permanent-fail" << 'MOCK3'
#!/usr/bin/env bash
echo "401 unauthorized invalid api key" >&2
exit 2
MOCK3
chmod +x "$TMP/permanent-fail"

# Test 3: permanent -> no retry
set +e
out=$(retry_with_backoff 3 1 "$TMP/permanent-fail" 2>&1)
code=$?
set -e
if [ $code -eq 2 ] && ! echo "$out" | grep -q 'retrying in'; then
  echo "PASS permanent fails without retry"
else
  echo "FAIL permanent: code=$code out=$out"; exit 1
fi

echo "All retry tests passed"
exit 0