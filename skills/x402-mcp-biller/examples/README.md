# x402 MCP Biller — Examples

This directory contains concrete, runnable examples for wrapping MCP servers with x402 micropayment billing (USDC on Base).

## Quick Start (Testnet Only)

**No secrets or mainnet deployment required.**

1. Use Base Sepolia testnet (`eip155:84532`)
2. Use Coinbase CDP facilitator (testnet endpoint)
3. Price examples: `"$0.001"` or `"$0.01"` per tool call
4. Free tier guidance: 50–100 calls/day before paywall

## Files

- `mcp-server-billable.js` — Minimal billable MCP server skeleton (Node.js + @x402/express)
- `config.example.json` — Middleware configuration template
- `README.md` — This file

**Flagship concrete example**: See the sibling `examples/lemoncake-mcp-server/` (at workspace root) for the full LemonCake MVP:
- 5 real tools with pricing ($0.001–$0.005)
- Free tier tracking stub (100/day)
- Working 402 challenge + bypass mode
- Verification script + Swedish/EU focus (redovisning, GDPR, SKILL.md validator)
- Clear test instructions

## How to Run Locally (Testnet)

```bash
cd skills/x402-mcp-biller/examples
npm install @modelcontextprotocol/sdk @x402/express @x402/core @x402/evm express zod

node mcp-server-billable.js
```

Test 402:

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"example_tool","arguments":{"name":"Alice"}}}'
```

## LemonCake MVP (recommended starting point)

```bash
cd examples/lemoncake-mcp-server
npm install
SKIP_PAYMENT=1 npm start          # test tools without payments
# or
npm start                         # enforcing mode → 402 challenges
./test-mcp-x402.sh
```

## Production Notes

- Switch to Base mainnet (`eip155:8453`) + real USDC when ready
- Use `payTo` address you control (via CDP or wallet)
- Log all 402 challenges and settlement receipts
- Offer generous free tier for discovery

**Last updated:** 2026-06-22 (LemonCake MVP added + generic skeleton fixed)
**Linked from:** Top-level plan.md (LemonCake x402 play) + projects/mossfund/plan-lemoncake-x402-mvp.md