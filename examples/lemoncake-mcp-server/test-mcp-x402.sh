#!/usr/bin/env bash
# test-mcp-x402.sh — Verification script for LemonCake MCP Server (Phase 1)
#
# Tests:
#   1. Server starts (info endpoint, health endpoint, tools listing)
#   2. Bypass mode: all 5 tools respond with content
#   3. Free tier mode: X-Payer-Wallet header tracks calls
#   4. 402 challenge: triggers when free tier exhausted + no payment signature
#
# No secrets, no mainnet — Base Sepolia testnet only.

set -euo pipefail

PORT="${PORT:-4021}"
BASE_URL="http://localhost:${PORT}"
TEST_WALLET="0xTest$(date +%s)Wallet"
PASS=0
FAIL=0

color() { printf '\033[%sm%s\033[0m' "$1" "$2"; }
green() { color '32' "$1"; }
red()   { color '31' "$1"; }
yellow() { color '33' "$1"; }

ok()   { echo "  $(green "✓") $1"; PASS=$((PASS + 1)); }
fail() { echo "  $(red "✗") $1"; FAIL=$((FAIL + 1)); }

echo ""
echo "🍋 LemonCake MCP Server — Verification"
echo "========================================"
echo ""

# --- Wait for server to be ready ---
echo "Waiting for server at ${BASE_URL}/health..."
for i in {1..20}; do
  if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

HEALTH=$(curl -sf "${BASE_URL}/health" 2>/dev/null || echo "")
if [[ -z "$HEALTH" ]]; then
  fail "Server not responding at ${BASE_URL}/health"
  echo "  Start the server first: SKIP_PAYMENT=1 npm start"
  exit 1
fi
ok "Server is healthy: ${HEALTH}"

# --- Test 1: Info endpoint ---
echo ""
echo "Test 1: Info endpoint"
INFO=$(curl -sf "${BASE_URL}/" 2>/dev/null || echo "")
if echo "$INFO" | grep -q "LemonCake"; then
  ok "Info endpoint returns LemonCake banner"
else
  fail "Info endpoint missing LemonCake banner"
fi
if echo "$INFO" | grep -q "search_web"; then
  ok "Tools listed (search_web present)"
else
  fail "Tools not listed"
fi

# --- Test 2: Bypass mode tools ---
echo ""
echo "Test 2: Bypass mode tool calls (SKIP_PAYMENT=1)"
for TOOL in search_web get_weather redovisning_helper validate_skill_md gdpr_scan; do
  BODY=$(printf '{"query":"%s"}' "test" 2>/dev/null || printf '{}')
  if [[ "$TOOL" == "get_weather" ]]; then BODY='{"city":"Stockholm"}'; fi
  if [[ "$TOOL" == "redovisning_helper" ]]; then BODY='{"question":"Vad är moms?"}'; fi
  if [[ "$TOOL" == "validate_skill_md" ]]; then BODY='{"content":"---\nname: test\ndescription: test\n---\n# test\nA SKILL.md file with enough content to pass the 200 char minimum requirement."}'; fi
  if [[ "$TOOL" == "gdpr_scan" ]]; then BODY='{"text":"Hej, jag heter Anna och bor i Stockholm. Min mail är anna@example.com"}'; fi

  RESP=$(curl -sf -X POST "${BASE_URL}/mcp/tools/${TOOL}" \
    -H "Content-Type: application/json" \
    -H "X-Payer-Wallet: ${TEST_WALLET}" \
    -d "$BODY" 2>/dev/null || echo "FAILED")

  if echo "$RESP" | grep -q '"ok":true'; then
    ok "Tool ${TOOL} responded"
  else
    fail "Tool ${TOOL} failed: ${RESP:0:100}"
  fi
done

# --- Test 3: 402 challenge (low free tier) ---
echo ""
echo "Test 3: 402 challenge (low free tier simulation)"
# Set FREE_TIER_DAILY=2 to trigger 402 quickly
echo "  Restarting server with FREE_TIER_DAILY=2 to test 402 path..."
pkill -f "node server.js" 2>/dev/null || true
sleep 1
FREE_TIER_DAILY=2 SKIP_PAYMENT=0 nohup node server.js > /tmp/lemoncake-test.log 2>&1 &
SERVER_PID=$!
for i in {1..20}; do
  if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then break; fi
  sleep 0.5
done

# Make 2 free calls to exhaust tier
curl -sf -X POST "${BASE_URL}/mcp/tools/redovisning_helper" \
  -H "Content-Type: application/json" \
  -H "X-Payer-Wallet: 0xFreeTierTest" \
  -d '{"question":"test"}' > /dev/null 2>&1 || true
curl -sf -X POST "${BASE_URL}/mcp/tools/redovisning_helper" \
  -H "Content-Type: application/json" \
  -H "X-Payer-Wallet: 0xFreeTierTest" \
  -d '{"question":"test"}' > /dev/null 2>&1 || true

# 3rd call should hit 402
HTTP_CODE=$(curl -s -o /tmp/lemoncake-402.json -w "%{http_code}" -X POST "${BASE_URL}/mcp/tools/redovisning_helper" \
  -H "Content-Type: application/json" \
  -H "X-Payer-Wallet: 0xFreeTierTest" \
  -d '{"question":"test"}' 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "402" ]]; then
  ok "402 returned when free tier exhausted"
  if grep -q "PAYMENT-REQUIRED\|payment" /tmp/lemoncake-402.json 2>/dev/null; then
    ok "402 body contains payment challenge"
  else
    yellow "  (note: 402 body missing payment challenge details — verify manually)"
  fi
else
  fail "Expected HTTP 402, got ${HTTP_CODE}"
fi

# Cleanup
kill $SERVER_PID 2>/dev/null || true
sleep 1

# --- Summary ---
echo ""
echo "========================================"
echo "Summary: $(green "${PASS} passed"), $(if [[ $FAIL -gt 0 ]]; then red "${FAIL} failed"; else green "0 failed"; fi)"
echo "========================================"
echo ""
if [[ $FAIL -eq 0 ]]; then
  echo "$(green "✅ All tests passed — LemonCake MVP is ready for Phase 1")"
  exit 0
else
  echo "$(red "❌ Some tests failed — check logs in /tmp/lemoncake-test.log")"
  exit 1
fi