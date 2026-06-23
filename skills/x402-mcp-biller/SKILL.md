---
name: "x402-mcp-biller"
description: "Wrap any existing MCP server/tool with x402 micropayment (USDC) billing. Use when you want to monetize an MCP capability per-call or per-token via the x402 prot"
---

# x402 MCP Biller (updated 2026-06-22)

**Status:** Ready for use — examples + wrapper pattern implemented.

Wrap any MCP server with usage-based micropayments (x402/USDC on Base).

**LemonCake MVP (Phase 1)**: Full concrete implementation lives in the workspace-level `examples/lemoncake-mcp-server/`.

## Quick Start (Testnet)

See `examples/README.md` for the generic skeleton.

**Recommended**: Use `examples/lemoncake-mcp-server/` (full LemonCake MVP):
- 5 priced tools (search_web $0.001, get_weather $0.001, redovisning_helper $0.005, validate_skill_md $0.002, gdpr_scan $0.003)
- Free tier: 100 calls/day per payer (in-memory stub + hooks)
- Base Sepolia + CDP facilitator
- 402 challenge + bypass mode + verification script
- Swedish/EU focus + clear disclaimers

Run:

```bash
cd examples/lemoncake-mcp-server
npm install
SKIP_PAYMENT=1 npm start     # bypass for testing tools
# or enforcing:
npm start
./test-mcp-x402.sh
```

- Price per tool: `$0.001` – `$0.005`
- Free tier: 50–100 calls/day recommended
- Network: `eip155:84532` (Base Sepolia)

## Examples

**Generic skeleton**
- `examples/mcp-server-billable.js` — Minimal billable MCP server (Node.js + @x402/express)
- `examples/config.example.json` — Middleware configuration template
- `examples/README.md` — How to run locally (testnet, no secrets)

**Full MVP (use this)**
- `examples/lemoncake-mcp-server/` (at repo root)
  - `server.js` — Complete MCP + x402 with 5 tools
  - `test-mcp-x402.sh` — Verification script (402 + free path + tools)
  - `README.md` + `config.example.json`
  - Zero secrets, runnable immediately

## Verification Checklist (Phase 1)

- [ ] `npm install && SKIP_PAYMENT=1 node server.js` starts cleanly (lemoncake dir)
- [ ] `curl http://localhost:4021/` shows tools + pricing + free tier info
- [ ] Without bypass: POST /mcp without payment header returns HTTP 402 + PAYMENT-REQUIRED
- [ ] With bypass: all 5 tools respond with correct structured content
- [ ] `./test-mcp-x402.sh` completes with ✅ summary (or equivalent manual checks)
- [ ] No secrets, no mainnet addresses, payTo is clearly a placeholder
- [ ] Tool descriptions contain price hints
- [ ] Logs show challenge/settle events when payments flow

## References

- Coinbase CDP x402 quickstart + MCP guide
- Cloudflare Agents SDK + withX402 / paidTool
- x402.org ecosystem + x402-foundation GitHub examples
- Base Sepolia faucet (CDP)
- LemonCake play: `projects/mossfund/plan-lemoncake-x402-mvp.md`

**Last updated:** 2026-06-22 (LemonCake MVP implementation + verification checklist)
