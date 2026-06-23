# MossRouter MCP — x402 Billable Tiers (Phase 2a)

**Status:** Phase 2b. Full MCP `/mcp` Streamable + Redis spend + Langfuse tracing + CDP facilitator (testnet default). Backward compatible with Phase 2a routes. 25+ tests. LemonCake parity.

---

## Quick Start

```bash
cd examples/moss-router-mcp
npm install
MOSS_MOCK=1 SKIP_PAYMENT=1 npm start
# other terminal
./test-moss-mcp-x402.sh
```

Curl examples:

```bash
curl http://localhost:4023/
curl http://localhost:4023/mcp/tools

# Bypass (MOCK)
curl -X POST http://localhost:4023/mcp/tools/moss_nano \
  -H "Content-Type: application/json" \
  -d '{"prompt":"hello nano"}'

# With test key (free tier)
curl -X POST http://localhost:4023/mcp/tools/moss_eco \
  -H "Authorization: Bearer moss_test_demo123" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"eco test"}'

# Paid simulation (mock sig)
curl -X POST http://localhost:4023/mcp/tools/moss_premium \
  -H "Authorization: Bearer moss_live_abc" \
  -H "PAYMENT-SIGNATURE: mock-sig-1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"premium"}'
```

---

## Tools & Pricing (flat per-call)

| Tool            | Tier       | Price   | X-Moss-Tier upstream |
|-----------------|------------|---------|----------------------|
| `moss_nano`     | nano       | $0.001  | nano                 |
| `moss_eco`      | eco        | $0.003  | eco                  |
| `moss_standard` | standard   | $0.008  | standard             |
| `moss_premium`  | premium    | $0.020  | premium              |
| `moss_flagship` | flagship   | $0.050  | flagship             |

All calls proxy to MossRouter on 4022 with `X-Moss-Tier` + `X-Moss-Tenant`.

---

## Multi-tenant API Keys

- `moss_test_...` — free tier (100 calls/day default)
- `moss_live_...` — paid path (x402 required after free)
- Headers: `Authorization: Bearer moss_test_xxx` or `X-Moss-Api-Key: moss_test_xxx`

Generate example:
```bash
node -e 'console.log("moss_test_" + require("crypto").randomBytes(16).toString("hex"))'
```

Per-tenant:
- Daily/monthly USD spend caps (default $5 / $50)
- Rate limit (req/min, default 60)
- Enforcement before proxy + 429 on exceed

SHA-256 hash used internally for storage.

---

## x402 (LemonCake parity)

- `SKIP_PAYMENT=1` disables challenges
- `MOSS_MOCK=1` forces free for all
- 402 response with `PAYMENT-REQUIRED` header (b64 challenge) when exhausted
- Mock: any non-empty `PAYMENT-SIGNATURE` or `X-Payment` header accepted (no real facilitator in MVP)
- Cost: `X-Moss-Cost-USD` from upstream + moss metadata in body

See `config.example.json` for `payTo`, `network`, `facilitatorUrl`.

---

## Config & Environment

See `config.example.json` (loaded on start).

Key env:
- `PORT=4023`
- `MOSS_ROUTER_PORT=4022`
- `SKIP_PAYMENT=1`
- `MOSS_MOCK=1`
- `FREE_TIER_DAILY=100`
- `PAY_TO`, `NETWORK`, `FACILITATOR_URL`

MossRouter is started as child process automatically (health poll < 8s).

---

## Architecture

- Express server (4023)
- Child process: `node ../moss-router/server.js` (4022)
- Per-route paywall on `/mcp/tools/moss_*`
- Tenant key parse + spend/rate before paywall/proxy
- Proxy adds `X-Moss-Tier` + `X-Moss-Tenant`, forwards cost headers

Full details + failure modes in `plan.md`.

---

## Verification Checklist

```bash
MOSS_MOCK=1 SKIP_PAYMENT=1 npm test
# or
MOSS_MOCK=1 SKIP_PAYMENT=1 npm start
./test-moss-mcp-x402.sh
```

Must pass:
- [ ] Server + Moss child healthy <5s
- [ ] All 5 tools return correct in bypass
- [ ] 402 without payment + mock payment header works
- [ ] Tenant isolation, spend cap, rate limit
- [ ] moss_test_* bypass + cost header
- [ ] README, config, npm test clean

See `plan.md` for complete 13+ checks + citations.

---

## Phase 2b (current)

- Full MCP Streamable `POST /mcp` (initialize, tools/list, tools/call) alongside legacy `/mcp/tools/:tier`
- McpServer registration of the 5 tier tools with price metadata
- Redis-backed spend/rate/free (keys with TTLs) + seamless in-mem fallback
- Langfuse v5 tracing (`startActiveObservation`, OTel GenAI + moss.* attrs) — enabled only with keys
- CDP facilitator: default https://x402.org/facilitator (testnet). CDP_API_KEY/SECRET switches to prod endpoint. NETWORK mainnet = yellow (explicit approval required)
- Health reports redis/langfuse/facilitator state
- 25+ tests (old 19 preserved)

## Quick MCP usage (JSON-RPC)
```bash
curl -X POST http://localhost:4023/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}}}'

curl -X POST http://localhost:4023/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"moss_eco","arguments":{"prompt":"hello"}}}'
```

Env: REDIS_URL, LANGFUSE_PUBLIC_KEY+SECRET, CDP_API_KEY+SECRET, NETWORK, PAY_TO.

**Built for Mossfund** — sister to LemonCake.
References: see `plan.md`.
