# MossRouter MCP — Plan (x402 Phase 2a MVP)

**Goal:** Planera, designa och bereda "MossRouter MCP" — en billable MCP-server (LemonCake-style x402 Phase 2-förlängning) som wrappar MossRouter Phase 1 och exponerar 5 kostnads-tier-routes som betalbara MCP-tools. Plus multi-tenant API keys med spend caps.

**Date:** 2026-06-22  
**Owner:** Moss (via plan + Telegram approval)  
**Status:** Phase 2a COMPLETE. Phase 2b EXECUTED — MCP /mcp Streamable + Redis + Langfuse + CDP implemented. 25+ tests target. See addendum + verification.

---

## Research Findings (cached 2026-06-22T22:22:07Z — TTL 48h)

### x402 + MCP (LemonCake + civicteam patterns)
- LemonCake (examples/lemoncake-mcp-server/): Express + custom x402 paywall, per-tool pricing via route-specific middleware, SKIP_PAYMENT bypass, free tier in-mem per wallet, 5 tools, bash+curl test script (9/9), PAYMENT-REQUIRED + header proof-of-concept. Parity target.
- @x402/express (official): `paymentMiddleware(routePriceMap, resourceServer)` where routePriceMap e.g. `{ "POST /mcp/tools/moss_nano": { accepts: [{ scheme: "exact", price: "$0.001", network: "eip155:84532", payTo }], ... } }`. Handles 402, verification via facilitator, settlement.
- Reference billable MCP server: civicteam/x402-mcp + x402-foundation servers/mcp use `McpServer` + `StreamableHTTPServerTransport` + `@x402/express` (single-route or advanced).
- Per-tool pricing: dominant pattern (map keys per route/tool). Per-tier flat-fee for MossRouter (not per-token) — avoids settlement-before-tokens problem.
- Facilitators: `https://x402.org/facilitator` (testnet, no auth) or CDP `https://api.cdp.coinbase.com/platform/v2/x402` (prod, KYT, 1000 tx free/mo).
- Headers: `PAYMENT-REQUIRED` (b64 challenge), `PAYMENT-SIGNATURE` (client), `X-PAYMENT*`.
- Free tier + bypass: critical for not breaking existing users. `MOSS_MOCK=1` or `moss_test_*` keys.
- MCP transport recommendation: HTTP/StreamableHTTP for LemonCake parity + Claude Desktop compatibility. Use convenience routes for curl testing.

### Multi-tenant + MossRouter Phase 1
- MossRouter (examples/moss-router/): port 4022, OpenAI-compatible `/v1/chat/completions`, `X-Moss-Tier: nano|eco|standard|premium|flagship`, response headers `X-Moss-Cost-USD`, `X-Moss-Tier`, `X-Moss-Model`, `X-Moss-Provider`, `X-Moss-Cache`, body `moss: {costUsd, ...}`. Full `MOSS_MOCK=1` support + 20+ passing tests (bash+curl).
- Proxy pattern: forward `X-Moss-Tier` + `X-Moss-Tenant`. Cost pass-through.
- In-memory semantic cache + failover already in Phase 1; no need to duplicate in wrapper (Phase 2b adds Redis).
- Subprocess spawn: recommended for isolation (independent deploys, no shared module state). Health poll `/health`.

### Spend/tenant/API keys
- Keys: `moss_live_xxx` (prod) / `moss_test_xxx` (test/free). Prefix fast-lookup. Store SHA-256 of key (never raw in logs/DB).
- Isolation: per-tenant counters (daily/monthly spend USD, req/min), namespaced even for cache (already done upstream).
- Enforcement: before upstream call (fail fast with 429/402).
- MVP storage: in-memory `Map` + optional periodic JSON flush. (Phase 2b: Redis).

### Observability (deferred)
- Phase 2a: structured JSON logs (already in MossRouter `structuredLog`).
- Phase 2b: Langfuse v5 `startActiveObservation`, per-request `moss.tier`, `moss.cost_usd`, `moss.cache_hit`, `moss.tenant_id`.

### Failure modes (design against)
- Facilitator outage → graceful: serve free tier / test keys, log, exponential backoff.
- MossRouter child crash → restart or 503, health fails.
- Stampede → not in scope (upstream cache handles).
- Tenant abuse → rate + spend cap before LLM proxy.
- Settlement fail → 402 retry.

**Sources (research + local):** 
- User-provided cached research (CDP docs, x402.org, civicteam/x402-mcp, langfuse, redis etc.)
- Local: `../lemoncake-mcp-server/{server.js,README.md,test-mcp-x402.sh,package.json,config.example.json}`
- Local: `../moss-router/{server.js,lib/*,README.md,test-moss-router.sh,plan.md,config.example.json}`
- skills/x402-mcp-biller/{SKILL.md,examples/mcp-server-billable.js,README.md,config.example.json}
- Web results (x402 express patterns, MCP server examples).

**Citations used in plan:** inline where specific external patterns/docs referenced.

---

## Context
- **Phase 1 (klar, 20+ tester):** HTTP server port 4022, OpenAI-kompatibel, 5 providers (OpenAI/Anthropic/Google/OpenRouter/Groq), 5 tiers (nano/eco/standard/premium/flagship), CLI + lib/router+pricing+cache+providers+utils, `MOSS_MOCK=1`, cost headers, semantic cache, failover.
- **Sister (x402 Phase 1, 9/9 tester):** `examples/lemoncake-mcp-server/` — Express + x402 (custom paywall), 5 priced tools, free tier, SKIP_PAYMENT, bash+curl tests, config.example, README tables + checklist.
- **Workdir:** examples/moss-router-mcp (ny tom katalog, green field).
- **Zone:** green (nytt projekt, ingen påverkan på Phase 1 eller lemoncake dirs).
- **Inspiration:** civicteam/x402-mcp, @x402/express + core/evm, LemonCake patterns (exact parity på test/docs/mock/curl), MossRouter Phase 1.
- **Requester:** telegram (Alabama, 438805461).
- **Orchestrator:** plan → Telegram summary + "ja/kör/ok" → execute.

**Out of scope (strict):** 
- Ändringar i examples/moss-router/ eller lemoncake-mcp-server/
- Persistent Redis (Phase 2b)
- Langfuse / full OTel (Phase 2b)
- pgvector
- Real mainnet CDP wallet setup / production keys
- Deprecated providers/models
- Faktiska API-nycklar (alltid MOSS_MOCK=1 + bypass för tester)

---

## Requirements (Phase 2a MVP — detta levererar planen)

### Kärnfunktionalitet
1. **Billable MCP server** — Express + `@x402/express` (paymentMiddleware + resourceServer) som wrappar MossRouter HTTP API. LemonCake-parity på struktur.
2. **5 prisade MCP-tools** (en per tier, flat-fee):
   - `moss_nano` — $0.001 (X-Moss-Tier: nano)
   - `moss_eco` — $0.003 (X-Moss-Tier: eco)
   - `moss_standard` — $0.008 (X-Moss-Tier: standard)
   - `moss_premium` — $0.020 (X-Moss-Tier: premium)
   - `moss_flagship` — $0.050 (X-Moss-Tier: flagship)
3. **Multi-tenant API keys**:
   - Format: `moss_live_...` (live/paid) / `moss_test_...` (test/free)
   - SHA-256 hash för storage/lookup (aldrig raw keys i logs)
   - Per-tenant: spend caps (daily + monthly USD), rate limit (req/min)
4. **Free-tier bypass**:
   - `MOSS_MOCK=1` → alla anrop fria (full test)
   - `moss_test_*` keys → 100 free calls/dag (in-mem)
   - Paid/live paths kräver giltig x402 `PAYMENT-SIGNATURE` (eller header)
5. **Tier redirect + proxy**: tool-anrop → `POST http://localhost:4022/v1/chat/completions` med `X-Moss-Tier` + `X-Moss-Tenant` + tenant-id. Proxy body (messages/prompt).
6. **Cost pass-through**: returnera `X-Moss-Cost-USD` (från MossRouter) + `moss` metadata + eventuell marginal-notering.
7. **Wallet/facilitator config**: `PAY_TO`, `NETWORK` (default eip155:84532), `FACILITATOR_URL` (x402.org eller CDP). Enkel validering.
8. **Spend/rate tracking**: per-tenant counters (in-mem Map för 2a).
9. **10+ tester** (bash + curl, ingen riktig facilitator):
   - Server + child start + health (MossRouter OK <5s)
   - 5 tools return correct stub (MOCK)
   - 402 utan payment
   - Mock payment verification (header accepted)
   - Tenant isolation (A key != B key)
   - Spend cap enforcement (cap 10 calls → 11:e = 429)
   - Rate limit enforcement
   - Free-tier bypass (moss_test_* + MOCK)
   - Cost header propagation (`X-Moss-Cost-USD`)
   - Wallet/config validation
   - Mock facilitator + full test script pass

### Nice-to-have (2b, defer)
- Full Streamable + McpServer registration (single /mcp + tools/call)
- Persistent Redis spend + cache
- Langfuse

### Specifika designval (beslutade i plan)
- **MossRouter relation:** Subprocess spawn (port 4022) + health poll. Rekommendation i prompt + isolation + zero shared state.
- **MCP transport:** LemonCake-style custom Express routes (`/mcp/tools/:name`) + `@x402/express` paywall per route för enkel curl + per-price. (Full SDK /mcp kan läggas parallellt i 2b.)
- **Facilitator:** Konfigurerbar (default `https://x402.org/facilitator` för test). CDP stödjs via env.
- **Spend storage:** In-memory Map + (valfritt) flush till `spend.json`. Phase 2b → Redis.
- **Test framework:** Exact LemonCake + MossRouter stil: bash + curl + color + PASS/FAIL + bg server + pkill cleanup. 10+ explicit checks.
- **Per-tier prices:** Flat (inte per-token) — matchar research + x402 request-time model.
- **Key vs x402:** API keys = tenant/auth + spend/rate. x402 = payment rail för live calls.

---

## Architecture

```
Client (curl / Claude MCP / agent)
  ↓  Authorization: Bearer moss_test_xxx   OR   X-Moss-Api-Key
  ↓  (optional X-Payer-Wallet)
POST /mcp/tools/moss_nano   (or /eco etc)
  ↓  Tenant parse + rate/spend check (fail fast 429)
  ↓  @x402/express paymentMiddleware (or SKIP / test-free bypass)
  ↓  (402 challenge if needed)
  ↓  Proxy: fetch localhost:4022/v1/chat/completions
             + X-Moss-Tier: nano
             + X-Moss-Tenant: <tenant-from-key>
  ↓  MossRouter (subprocess, MOSS_MOCK or real)
  ↓  Response + headers (X-Moss-Cost-USD etc)
  ↑  Add billed metadata, return
```

**Components:**
- `server.js`: Express, spawn child, tenant/spend/rate, 5 routes + paywall, proxy, health, info.
- Child: `node <moss-router>/server.js` (env PORT=4022, MOSS_MOCK propagated).
- No changes to upstream moss-router.

**Startup sequence:**
1. Read config / env
2. Spawn moss-router child (inherit MOSS_MOCK etc)
3. Poll http://127.0.0.1:4022/health (max 5-8s)
4. Setup Express + middleware + routes
5. Listen (default 4023)

**Graceful shutdown:** kill child on SIGTERM etc.

---

## Proposed File Structure (project root)

```
examples/moss-router-mcp/
├── package.json
├── server.js                 # Huvudfil (likt lemoncake + spawn + multi-tenant)
├── config.example.json
├── README.md
├── test-moss-mcp-x402.sh     # 12+ tester, bash+curl, exakt stil
├── .gitignore                # node_modules, spend.json, *.log
└── plan.md                   # Denna fil (och i execute: uppdaterad status)
```

(Valfritt i 2b: `lib/tenant.js`, `lib/spend.js` etc för extra clean.)

---

## Dependencies (package.json)

```json
{
  "name": "moss-router-mcp",
  "version": "0.1.0",
  "type": "module",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "start:bypass": "SKIP_PAYMENT=1 MOSS_MOCK=1 node server.js",
    "test": "bash test-moss-mcp-x402.sh",
    "test:mock": "MOSS_MOCK=1 SKIP_PAYMENT=1 bash test-moss-mcp-x402.sh"
  },
  "engines": { "node": ">=18" },
  "dependencies": {
    "express": "^4.21.0",
    "@x402/express": "^latest-compatible",
    "@x402/core": "^latest-compatible",
    "@x402/evm": "^latest-compatible"
  },
  "license": "MIT",
  "keywords": ["mcp", "x402", "moss-router", "billable", "tiers", "multi-tenant"]
}
```

**Install in execute:** `npm install`

(Exakt versions: pin via npm in run; research recommends latest from x402-foundation as of June 2026.)

---

## Config (config.example.json + env)

```json
{
  "port": 4023,
  "mossRouter": {
    "port": 4022,
    "command": "node",
    "script": "../moss-router/server.js",
    "healthUrl": "http://127.0.0.1:4022/health"
  },
  "x402": {
    "network": "eip155:84532",
    "payTo": "0x000000000000000000000000000000000000dEaD",
    "facilitatorUrl": "https://x402.org/facilitator"
  },
  "freeTier": {
    "callsPerDay": 100
  },
  "tenant": {
    "defaultSpendCapDaily": 5.00,
    "defaultSpendCapMonthly": 50.00,
    "rateLimitPerMin": 60
  },
  "pricing": {
    "nano": 0.001,
    "eco": 0.003,
    "standard": 0.008,
    "premium": 0.020,
    "flagship": 0.050
  }
}
```

**Env overrides (priority):**
- `PORT`, `MOSS_ROUTER_PORT`
- `SKIP_PAYMENT=1`
- `MOSS_MOCK=1`
- `PAY_TO`, `NETWORK`, `FACILITATOR_URL`
- `FREE_TIER_DAILY`

Sample keys (hardcoded i dev + dokumenterat): `moss_test_demo123...`, `moss_live_demo456...` (hash for storage demo).

---

## Core Implementation Notes (executable in execute phase)

### server.js skeleton (high level)
```js
import express from 'express';
import { spawn } from 'node:child_process';
import { randomUUID, createHash } from 'node:crypto';
import { setTimeout as sleep } from 'node:timers/promises';

// config + consts for tiers, prices, payTo, facilitator
// freeTier Map, tenantSpend Map<tenantKeyHash, {daily, monthly, window: []}>

function hashKey(k) { return createHash('sha256').update(k).digest('hex').slice(0,32); }

function getTenantFromReq(req) {
  const h = req.headers['authorization'] || req.headers['x-moss-api-key'] || '';
  const m = h.match(/moss_(live|test)_([a-z0-9]+)/i);
  if (m) return { key: `moss_${m[1]}_${m[2]}`, isTest: m[1]==='test' };
  return { key: 'default', isTest: !!process.env.MOSS_MOCK };
}

async function waitForHealth(url, timeoutMs=5000) { ... poll with fetch ... }

async function startMossRouter() {
  const child = spawn(... , { env: { ...process.env, PORT: '4022', ...(MOCK && {MOSS_MOCK:'1'}) } });
  child.stdout.on('data', d => console.log('[moss]', d.toString().trim()));
  // on exit: log/restart logic (simple for mvp)
  await waitForHealth(HEALTH_URL);
  return child;
}

function buildPriceMap() {
  return {
    'POST /mcp/tools/moss_nano': { accepts: [{scheme:'exact', price:'$0.001', network, payTo}] , ...},
    // repeat for 4 others with correct prices
  };
}

// tenant/rate/spend helpers
function checkRateLimit(tenant) { ... sliding window ... throw 429 if exceed }
function checkSpend(tenant, priceUsd) { ... accumulate + cap check, throw if exceed }
function recordUsage(tenant, priceUsd) { ... }

// routes
app.post('/mcp/tools/:tier', (req,res,next) => {
  const {key, isTest} = getTenantFromReq(req);
  const tier = req.params.tier.replace('moss_','');
  const price = PRICES[tier];
  try { checkRateLimit(key); checkSpend(key, price); } catch(e){ return res.status(e.code||429).json(...) }

  if (SKIP_PAYMENT || (isTest && freeCount < limit)) {
    // bypass, increment free/spend
    return proxyToMoss(req, res, tier, key);
  }
  // else fall to x402 middleware
});

// x402 middleware setup (selective or whole + internal flag)
const paywall = paymentMiddleware( buildPriceMap(), resourceServer );
app.use( (req,res,next) => {
  if (req.path.startsWith('/mcp/tools/')) return paywall(req,res,next);
  next();
});

app.post('/mcp/tools/:tier', (req,res) => {
  // after paywall passed
  proxyToMoss(...)
});

async function proxyToMoss(req, res, tier, tenantKey) {
  const upstream = await fetch(`http://127.0.0.1:4022/v1/chat/completions`, {
    method:'POST',
    headers: {
      'content-type':'application/json',
      'X-Moss-Tier': tier,
      'X-Moss-Tenant': tenantKey
    },
    body: JSON.stringify(req.body)
  });
  const data = await upstream.json();
  // pass headers
  const cost = upstream.headers.get('x-moss-cost-usd');
  if (cost) res.setHeader('X-Moss-Cost-USD', cost);
  res.setHeader('X-Moss-Tier', tier);
  // record actual cost to tenant spend (if not already)
  res.json({ ok:true, tool: `moss_${tier}`, moss: data.moss || {}, ... });
}
```

**Proxy details:** Normalize prompt/messages. Support both `{messages:[...]}` and simple `{prompt}`. Forward all relevant Moss headers back.

**Spend update:** Prefer update *after* successful upstream response (use actual costUsd). Cap is "soft" pre-check + post reconciliation.

---

## Test Script (test-moss-mcp-x402.sh) — 10+ tests

Exact structure from lemoncake + moss-router (color, ok/fail, bg start, pkill, wait health loop).

Key tests (in order):
1. Health + info (MCP banner + 5 tools + pricing)
2. Bypass (SKIP + MOCK): all 5 tools respond ok:true + moss.tier
3. 402 challenge (exhaust free → POST without sig → 402 + PAYMENT-REQUIRED)
4. Mock payment (non-empty PAYMENT-SIGNATURE or X-PAYMENT accepted → 200)
5. Tenant isolation (keyA calls don't affect keyB counters)
6. Spend cap (low cap via env or forced,  N calls → N+1 gives 429 "spend cap")
7. Rate limit (burst > limit → 429)
8. Free bypass with `moss_test_*` key (100 cap sim)
9. Cost pass-through (X-Moss-Cost-USD present and numeric)
10. Wallet/facilitator config validation on start (or /health includes)
11. Child health: MossRouter /tiers or /health reachable
12. (bonus) Full JSON-RPC style if /mcp mounted, or note
13. Cleanup + summary ✅ / ❌

Run: `MOSS_MOCK=1 SKIP_PAYMENT=1 npm test`

Also support direct `./test...` after manual start.

---

## README.md Sketch (must include)

# MossRouter MCP — x402 Billable Tiers (Phase 2a)

**Status:** Phase 2a MVP. Wraps MossRouter. 5 tiered MCP tools. Multi-tenant keys + spend caps. Testnet-first.

## Quick Start
```bash
cd examples/moss-router-mcp
npm install
MOSS_MOCK=1 SKIP_PAYMENT=1 npm start
# other terminal
./test-moss-mcp-x402.sh
```

curl examples for each tier + with/without key.

## Tools & Pricing
| Tool            | Tier       | Price   | Upstream header     |
|-----------------|------------|---------|---------------------|
| moss_nano       | nano       | $0.001  | X-Moss-Tier: nano   |
| moss_eco        | eco        | $0.003  | X-Moss-Tier: eco    |
| moss_standard   | standard   | $0.008  | ...                 |
| moss_premium    | premium    | $0.020  | ...                 |
| moss_flagship   | flagship   | $0.050  | ...                 |

## Tenant Keys
- `moss_test_...` : free tier (100/day)
- `moss_live_...` : requires x402 payment after free
- Generate: `node -e 'console.log("moss_test_" + require("crypto").randomBytes(16).toString("hex"))'`
- Headers: `Authorization: Bearer moss_test_xxx` or `X-Moss-Api-Key`

## x402 (LemonCake parity)
Same 402 flow + headers. Use `SKIP_PAYMENT=1`.

## Config & Env
(Full table)

## Verification Checklist
- [ ] npm install && MOSS_MOCK=1 SKIP_PAYMENT=1 npm start (Moss child health <5s)
- [ ] 5 tools return correct in bypass
- [ ] 402 + mock payment + tenant/spend/rate tests pass via `./test-moss-mcp-x402.sh`
- [ ] Cost headers correct
- [ ] README + config.example present

## Architecture notes + failure handling
## Phase 2b
## References + citations

---

## Verification Checklist (for plan success + execute)

- [x] `npm install` works (after plan → execute)
- [x] MCP server startar + startar MossRouter subprocess (health OK inom 5s)
- [x] `./test-moss-mcp-x402.sh` — minimum 10 tester passerar (MOCK)
- [x] 5 tools return correct (mock mode)
- [x] 402 response utan payment
- [x] Tenant A key isolerad från Tenant B
- [x] Spend cap enforcement (10 calls → 11:e ger 429)
- [x] Free-tier bypass fungerar (moss_test_* + MOCK)
- [x] Cost pass-through correct (`X-Moss-Cost-USD` propagated)
- [x] Mock facilitator verification fungerar
- [x] Rate limit per tenant
- [x] Wallet config validation (start log / health)
- [x] README med quick start, pricing table, tenant setup, test instructions
- [x] LemonCake parity: bash/curl, doc-style, mock mode, structure

Run verification: `MOSS_MOCK=1 SKIP_PAYMENT=1 npm test` + manual curl smoke.

---

## Execution Steps (post-approval)

1. `cd examples/moss-router-mcp`
2. Create files per structure (package, server.js, config, README, test script)
3. `npm install`
4. Implement server.js iteratively (spawn first, then proxy, then paywall/tenant, then tests)
5. Run tests, fix until green
6. Update README + plan.md status
7. (Optional) commit
8. Notify: full checklist green

**Risks / unknowns mitigated in plan:**
- Facilitator versions: pin to research (use x402.org default)
- MCP vs custom routes: LemonCake custom + @x402 for parity wins for curl/tests
- Subprocess cwd/paths: use absolute relative to __dirname or env override
- Fetch in Node: native ok (>=18)

---

## Phase 2b / Future
- Full McpServer + Streamable at `/mcp` (per-skill skeleton) + tool registration with per-tool price via advanced hooks
- Redis for spend + persistent cache coordination
- Langfuse tracing around proxy calls (`startActiveObservation`)
- Real CDP mainnet + payTo rotation
- Consolidated billing + Swish/BankID

---

**Plan complete.** Ready for Telegram summary + "ja/kör/ok" to execute.

**Citations:** Research findings (cached), local lemoncake/moss-router files, skills/x402-mcp-biller, web: CDP quickstart, x402-foundation examples, civicteam/x402-mcp.

All design choices documented with rationale. Executable with clear steps, no ambiguity.

---

## Phase 2b Planning Addendum (2026-06-23)

**Goal (from /plan):** Full MCP `/mcp` Streamable alongside custom routes; Redis-backed spend/rate/free; Langfuse v5 per-request tracing; CDP facilitator (x402.org default, CDP prod-ready, mainnet yellow-flagged).

**Key Research Sources (to cite on Telegram):**
- CDP + x402.org facilitator docs
- https://github.com/civicteam/x402-mcp (makePaymentAwareServerTransport + priceMap per tool)
- https://github.com/x402-foundation/x402
- Langfuse v5 tracing + OTel GenAI semconv
- Redis semantic cache patterns (counters sufficient here)
- Local: lemoncake server.js (MCP route style), skills/x402-mcp-biller/examples/mcp-server-billable.js (real McpServer + Streamable + @x402), current Phase 2a server.js (tenant + spend + proxy + custom paywall)

**Major Deliverables in Execute:**
- package.json: @modelcontextprotocol/sdk, ioredis, zod, 4x langfuse/otel packages
- server.js (additive): McpServer registration of 5 tier tools, POST /mcp handler with Streamable transport (enableJsonResponse:true), payment gate for tools/call using existing price/tenant/x402 logic + real verify/settle path, RedisSpendStore with fallback, conditional Langfuse observation wrapper, CDP auth support, enhanced health.
- Keep every existing route + behavior 100% for 19 tests.
- test-moss-mcp-x402.sh extended to ≥25 assertions total.
- New: .env.example, bin/moss-router-mcp, (opt) Dockerfile + docker-compose.yml
- README + this plan.md updated with Phase 2b details + citations.

**Verification (post-execute):**
- All Phase 2a tests green.
- New MCP JSON-RPC, Redis restart-persist, Langfuse no-op, facilitator paths.
- Manual curl POST /mcp initialize + tools/list + paid call.
- Health reports redis/langfuse states.
- MOSS_MOCK=1 SKIP=1 start + full test matrix passes.
- No mainnet defaults or live CDP calls in tests.

**Plan file for this phase:** session plan.md (full detail) + this addendum.

**Next:** Owner approval on Telegram (Alabama) → execute phase. Do not touch source until then.

**Citations for summary:** user query research block (key e797adbf...) + links listed + local file reads performed during planning (server.js, lemoncake, skill example, @x402/core facilitator classes).

**Execution note (2026-06-23):** Implemented per approved plan. All additive changes. See test output + manual verification for 25+ results.
