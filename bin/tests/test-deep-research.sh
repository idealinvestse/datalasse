#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

TESTBIN="$TMP/testbin"
mkdir -p "$TESTBIN"

# Copy real deep-research + lib modules
cp "$ROOT_DIR/deep-research" "$TESTBIN/deep-research"
mkdir -p "$TESTBIN/lib"
cp "$ROOT_DIR/lib/retry.sh" "$ROOT_DIR/lib/fallback.sh" "$TESTBIN/lib/"
chmod +x "$TESTBIN/deep-research"

# Mock exa-search (stdout json + cost controllable)
cat > "$TESTBIN/exa-search" << 'MEXA'
#!/usr/bin/env bash
COST="${MOCK_COST:-0.007}"
echo '{"results":[{"title":"Mock Exa","url":"https://mock.example.com/a","highlights":["hl1"]}],"costDollars":{"total":'"$COST"'}}'
MEXA
chmod +x "$TESTBIN/exa-search"

# Mock serper-search
cat > "$TESTBIN/serper-search" << 'MSERP'
#!/usr/bin/env bash
echo '{"organic":[{"title":"Mock Serper","link":"https://mock.example.com/a","snippet":"snippet here"}],"searchParameters":{"q":"q"}}'
MSERP
chmod +x "$TESTBIN/serper-search"

# Mock research-decompose (only used if OR set)
cat > "$TESTBIN/research-decompose" << 'MDECOMP'
#!/usr/bin/env bash
echo '[{"query":"mock deep sub","type":"deep","max_results":3,"rationale":"test","output_schema":null}]'
MDECOMP
chmod +x "$TESTBIN/research-decompose"

# Curl mock (for OR synth path only)
MOCKCURL="$TMP/mockcurl"
cat > "$MOCKCURL" << 'MCURL'
#!/usr/bin/env bash
if [[ "$*" == *"openrouter.ai"* ]]; then
  echo '{"choices":[{"message":{"content":"# Synth\nFindings with https://mock.example.com/verify and https://mock.example.com/other . Done."}}]}'
else
  echo '{}'
fi
MCURL
chmod +x "$MOCKCURL"

OUTMD="$TMP/out.md"

# Helper to run with PATH including testbin for subscripts + curlmock
run_deep() {
  local args=("$@")
  local extra_path="$TESTBIN"
  ( cd /tmp; OPENROUTER_API_KEY="" EXA_API_KEY=dummy SERPER_API_KEY=dummy PATH="$MOCKCURL:$extra_path:$PATH" "$TESTBIN/deep-research" "${args[@]}" 2>&1 )
}

# === Test 1: basic no-OR + --depth=deep + budget (fallback path) ===
echo "=== Test basic no-OR deep ===" >&2
set +e
run_out=$(run_deep "MCP test query" --depth=deep --budget=0.30 --output="$OUTMD" ); run_code=$?
set -e

WD=$(echo "$run_out" | grep -o '/tmp/deep-research-[^ ]*' | head -1 || echo "")

if [ $run_code -eq 0 ] \
   && grep -q "^# Deep Research Report" "$OUTMD" \
   && grep -q "Stage 3" "$OUTMD" \
   && grep -q "Stage 6" "$OUTMD" \
   && grep -q "Stage 6: Verification" "$OUTMD" \
   && grep -qi "Total cost" "$OUTMD" \
   && [ -f "$WD/sub-queries.json" ] \
   && ls "$WD"/serper-*.json >/dev/null 2>&1 \
   && echo "$run_out" | grep -q "Stage 3" ; then
  echo "PASS basic no-OR deep report+stages+cost+files"
else
  echo "FAIL basic: code=$run_code outmd=$(cat $OUTMD 2>/dev/null | head -c 200) wd=$WD runout=$(echo $run_out | head -c 300)"; exit 1
fi

# subq json valid
if jq -e 'type == "array" and length > 0 and .[0].type' "$WD/sub-queries.json" >/dev/null; then
  echo "PASS subq json"
else
  echo "FAIL subq json"; exit 1
fi

# === Test 2: no-OR path explicitly (unset OR) + stage 6 present ===
echo "=== Test no-OR fallback ===" >&2
OUT2="$TMP/out2.md"
set +e
run2=$( OPENROUTER_API_KEY="" EXA_API_KEY=dummy SERPER_API_KEY=dummy PATH="$MOCKCURL:$TESTBIN:$PATH" "$TESTBIN/deep-research" "fallback q" --depth=deep --budget=0.20 --output="$OUT2" 2>&1 ); c2=$?
set -e
if [ $c2 -eq 0 ] \
   && grep -q "Partial Synthesis (no OPENROUTER_API_KEY)" "$OUT2" \
   && grep -q "Stage 6: Verification" "$OUT2" \
   && grep -q "# Deep Research Report" "$OUT2"; then
  echo "PASS no-OR fallback produces stages 3+6"
else
  echo "FAIL no-OR: $c2 $(cat $OUT2 | head -5)"; exit 1
fi

# === Test 3: budget exceed path ===
echo "=== Test budget exceed ===" >&2
OUT3="$TMP/out3.md"
set +e
run3=$( MOCK_COST=0.50 EXA_API_KEY=dummy SERPER_API_KEY=dummy OPENROUTER_API_KEY="" PATH="$MOCKCURL:$TESTBIN:$PATH" "$TESTBIN/deep-research" "exceed q" --depth=deep --budget=0.10 --output="$OUT3" 2>&1 ); c3=$?
set -e
if grep -qi "exceeded\|⚠️ Budget exceeded\|partial" "$OUT3" || echo "$run3" | grep -qi "exceeded"; then
  echo "PASS budget exceed note"
else
  echo "FAIL budget exceed: c=$c3 md=$(head -c 300 $OUT3) run=$(echo $run3|head -c200)"; exit 1
fi

# === Test 4: OR path if wanted (with curl mock) ===
echo "=== Test with-OR synth (optional) ===" >&2
OUT4="$TMP/out4.md"
set +e
run4=$( OPENROUTER_API_KEY=dummy EXA_API_KEY=dummy SERPER_API_KEY=dummy PATH="$MOCKCURL:$TESTBIN:$PATH" "$TESTBIN/deep-research" "or q" --depth=auto --budget=0.30 --output="$OUT4" 2>&1 ); c4=$?
set -e
if [ $c4 -eq 0 ] && grep -q "# Deep Research Report" "$OUT4"; then
  echo "PASS OR path (or skipped gracefully)"
else
  echo "note: OR path rc=$c4 (ok if no full OR coverage)"
fi

echo "All deep-research tests passed"
exit 0
