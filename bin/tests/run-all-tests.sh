#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
FAIL=0
for t in test-*.sh; do
  echo "=== RUN $t ==="
  if bash "$t"; then
    echo "✅ PASS $t"
  else
    echo "❌ FAIL $t"
    FAIL=1
  fi
done
[ $FAIL -eq 0 ] && echo "All tests passed" || { echo "Some tests failed"; exit 1; }
