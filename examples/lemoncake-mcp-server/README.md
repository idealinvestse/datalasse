# LemonCake MCP Server — x402 Billable MCP Tools (Phase 1 MVP)

**Status:** Phase 1 MVP — Base Sepolia testnet, no secrets, runnable immediately.

A minimal billable MCP server that exposes 5 tools with per-call pricing via the **x402 protocol** (Coinbase + Cloudflare).

---

## Quick Start

```bash
cd examples/lemoncake-mcp-server
npm install
SKIP_PAYMENT=1 npm start     # bypass for testing tools
# or enforcing:
npm start
./test-mcp-x402.sh            # verification script
```

Then:
```bash
curl http://localhost:4021/
curl http://localhost:4021/mcp/tools
curl -X POST http://localhost:4021/mcp/tools/redovisning_helper \
  -H "Content-Type: application/json" \
  -H "X-Payer-Wallet: 0xMyWallet" \
  -d '{"question":"Vad är moms?"}'
```

---

## Tools (5 priced)

| Tool | Description | Price |
|------|-------------|-------|
| `search_web` | Web search via Serper | $0.001 |
| `get_weather` | Current weather for a city | $0.001 |
| `redovisning_helper` | Swedish SME accounting helper (BAS, moms) | $0.005 |
| `validate_skill_md` | Validate a SKILL.md frontmatter + structure | $0.002 |
| `gdpr_scan` | Lightweight GDPR PII red-flag scan | $0.003 |

---

## Pricing Model

- **Free tier:** 100 calls/day per wallet (in-memory stub; replace with DB in Phase 2)
- **Paid:** per-call after free tier exhausted
- **Network:** `eip155:84532` (Base Sepolia)
- **Pay-to:** placeholder Sepolia address (replace with your own)
- **Bypass:** `SKIP_PAYMENT=1` to disable 402 challenges (testing only)

---

## Endpoints

| Path | Method | Purpose |
|------|--------|---------|
| `/` | GET | Server info + tool listing |
| `/health` | GET | Health check (uptime, bypass mode) |
| `/mcp/tools` | GET | Tool catalog (free — for discovery) |
| `/mcp/tools/:name` | POST | Tool invocation (x402 paywalled) |

---

## x402 402 Challenge

When a wallet exceeds the free tier, the server returns:

```
HTTP/1.1 402 Payment Required
PAYMENT-REQUIRED: <base64-encoded JSON challenge>
Content-Type: application/json

{
  "error": "Payment required",
  "challenge": {
    "x402Version": 2,
    "accepts": [{
      "scheme": "exact",
      "network": "eip155:84532",
      "payTo": "0x...",
      "maxAmountRequired": "5000",   // USDC has 6 decimals → $0.005 = 5000
      "resource": "/mcp/tools/redovisning_helper",
      "description": "..."
    }]
  },
  "freeTierExhausted": true,
  "freeTierDaily": 100
}
```

To complete payment, client re-sends with `PAYMENT-SIGNATURE` header containing the signed EIP-3009 authorization.

**Phase 1 simplification:** any non-empty `PAYMENT-SIGNATURE` header is accepted (proof-of-concept).  
**Phase 2:** verify via Coinbase CDP facilitator.

---

## Architecture

```
MCP Client (Claude Desktop / custom agent)
        ↓ (POST /mcp/tools/:name)
Express server
        ↓ (X-Payer-Wallet tracking)
Free tier check
        ↓ (if exhausted → 402 challenge with PAYMENT-REQUIRED)
        ↓ (if payment header → continue)
Tool handler (5 functions)
        ↓
JSON response
```

---

## Environment Variables

| Var | Default | Description |
|-----|---------|-------------|
| `PORT` | 4021 | HTTP port |
| `SKIP_PAYMENT` | 0 | Set to `1` to disable 402 challenges |
| `PAYTO_ADDRESS` | 0x000…dEaD | Sepolia recipient (replace with your own) |
| `NETWORK` | eip155:84532 | CAIP-2 network ID |
| `FREE_TIER_DAILY` | 100 | Free calls per wallet per day |

---

## Phase 1 vs Phase 2

**Phase 1 (current MVP):**
- ✅ Testnet (Base Sepolia)
- ✅ 5 tools with pricing
- ✅ Free tier tracking (in-memory)
- ✅ 402 challenge + bypass mode
- ✅ Swedish/EU focus (redovisning, GDPR)
- ✅ Zero secrets, runnable immediately

**Phase 2 (future):**
- 🔜 Mainnet + real USDC
- 🔜 BankID/Swish hybrid
- 🔜 Production facilitator (CDP real verification)
- 🔜 Agent.market registration
- 🔜 SIWx sessions for high-frequency workloads
- 🔜 MCPize directory + discoveryricks

---

## Verification Checklist

See `test-mcp-x402.sh` for automated tests.

- [ ] `npm install && SKIP_PAYMENT=1 npm start` starts cleanly
- [ ] `curl http://localhost:4021/` shows tools + pricing + free tier
- [ ] Without bypass: POST without payment header returns HTTP 402
- [ ] With bypass: all 5 tools respond correctly
- [ ] `./test-mcp-x402.sh` completes with ✅ summary
- [ ] No secrets, no mainnet, payTo is placeholder

---

## References

- Coinbase CDP x402 quickstart: https://docs.cdp.coinbase.com/x402/welcome
- Cloudflare Agents SDK: https://developers.cloudflare.com/agents/x402/
- x402.org ecosystem: https://www.x402.org
- Plan: `../../projects/mossfund/plan-lemoncake-x402-mvp.md`
- Synthesis: `../../projects/mossfund/research/parallel/g-20260618-001/synthesis.md`

---

**Built by:** Moss (main session)  
**Last updated:** 2026-06-22 (Phase 1 MVP)