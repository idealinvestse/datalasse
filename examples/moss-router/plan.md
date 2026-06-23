# MossRouter — Plan (Phase 1 MVP)

**Goal:** Planera, designa och bereda för "MossRouter" — en ultimat, produktionsklar LLM-router med flera kostnadsgrupper (tiers), som kan rullas ut som billable MCP-server (LemonCake-style Phase 2) och/eller HTTP/CLI för mossfund-ekosystemet.

**Date:** 2026-06-22  
**Owner:** Moss (via grok-build)  
**Status:** PLANNING COMPLETE — ready for execute after approval

---

## Research Findings (from cache, TTL 48h)

**Cached at:** 2026-06-22T21:45:34.261451Z

### Quick facts — Per-token pricing (June 2026, $/M tokens input/output)
- **OpenAI**: GPT-4o: $2.50/$10.00; GPT-4.1: $2.00/$8.00 (1M ctx); GPT-4.1 Mini: $0.40/$1.60; GPT-4.1 Nano: $0.10/$0.40; GPT-5.5: $5.00/$30.00; o3: $2.00/$8.00; GPT-5 Nano/Mini: $0.05–0.25 / $0.40–2.00
- **Anthropic**: Claude Opus 4.7/4.8: $5.00/$25.00 (1M); Claude Sonnet 4.6: $3.00/$15.00; Claude Haiku 4.5: $0.80–1.00/$4.00–5.00
- **Google Gemini**: Gemini 2.5 Pro: $1.25/$10.00 (tiered >200K); Gemini 2.5 Flash: $0.30/$2.50; Gemini 2.0 Flash/Flash-Lite: $0.075–0.10 / $0.30–0.40 (1M ctx)
- **Others**: DeepSeek V4 Pro ~$0.44/$0.87; DeepSeek V4 Flash ~$0.09–0.14/$0.18–0.28; Mistral Large ~$2/$6; Grok 4/4.3: $1.25–5.00 / $2.50–15.00 (variant)
- **OpenRouter**: pass-through + 5.5% on prepaid credits
- **Groq Cloud** (LPU inference, 500–1000 T/s, fastest available):
  - `llama-3.1-8b-instant` 560 T/s, $0.05/$0.08, 131K ctx — **cheapest production API**
  - `openai/gpt-oss-20b` 1000 T/s, $0.075/$0.30, 131K ctx — **fastest tier-2 model**
  - `meta-llama/llama-4-scout-17b-16e-instruct` 750 T/s, $0.11/$0.34, 131K ctx
  - `openai/gpt-oss-120b` 500 T/s, $0.15/$0.60 (cached $0.075), 131K ctx — **OpenAI reasoning at Groq speed**
  - `qwen/qwen3-32b` 400 T/s, $0.29/$0.59 — Qwen reasoning
  - `llama-3.3-70b-versatile` 280 T/s, $0.59/$0.79 — flagship open-source, undercuts GPT-4o-mini output
  - `qwen/qwen3.6-27b` 500 T/s, $0.60/$3.00 — premium Qwen
  - Base URL: `https://api.groq.com/openai/v1` — fully OpenAI SDK-compatible (no new dep needed)
  - Env var: `GROQ_API_KEY` (format `gsk_...`)
  - No prompt caching discount, but raw prices already low enough that caching matters less
  - Source: https://console.groq.com/docs/models (last updated 2026-06-21)

**Provider-side caching (90% off cache-hit input):**
- Anthropic prompt caching, OpenAI cached input, Google context caching.

**Router SaaS comparison patterns:**
- LiteLLM (Python): OSS proxy, tier routing, virtual keys, cost tracking.
- Bifrost (Go): drop-in OpenAI-compatible, fastest (~10x Python), semantic routing, MCP support.
- Portkey: cloud+OSS, guardrails, semantic cache, 50+ providers.
- Helicone, OpenRouter (two-layer failover), Not Diamond (cascading +10% quality/-10% cost), Martian (real-time selection 20–97% savings).
- Sources: https://github.com/BerriAI/litellm, https://github.com/maximhq/bifrost, portkey.ai, openrouter.ai/docs, getmaxim.ai, alexcloudstar.com, bestaiweb.ai, truefoundry.com etc.

**Architecture patterns (production-verified 2026):**
- Three-layer: Provider routing + Model routing + Strategy routing.
- Gateway-centric (centralized OpenAI-compatible middleware).
- Task-aware / complexity routing + cascading with confidence escalation.
- Semantic caching as table-stakes (40–60% hit rates at 0.92 threshold, case: $23K → $8.6K/mo).
- OpenRouter two-layer reliability (provider failover default + model fallbacks).
- Sources: alexcloudstar.com/blog/llm-router-model-routing-fallbacks-2026, getmaxim.ai/articles/reduce-llm-cost-and-latency-a-comprehensive-guide-for-2026, birjob.com, callsphere.ai/blog/failure-mode-analysis-production-llm-systems-2026, arxiv.org/html/2411.05276v3

**Failure modes to design against:**
1. Silent response format drift (Kimi fences, Gemini commas) → resilient JSON.
2. Tokenization mismatches (40% variance) → use provider-reported tokens only.
3. Rate limit asymmetry → adaptive per-provider backoff.
4. Cache poisoning → per-tenant namespacing.
5. Silent quality degradation → calibrate tiers + evals (Phase 2).

**EU/Sweden moat:**
- GDPR + EU AI Act + Hetzner EU (Falkenstein/Helsinki) = structural advantage vs all-US (OpenRouter, Portkey, Helicone).
- "The EU sovereign LLM gateway".
- Svensk faktura + BankID/Swish future.
- Nordic language fluency.

**LemonCake integration angle:**
- MossRouter can be upstream LLM for LemonCake tools.
- Expose own MCP endpoints with x402 billable routing (per-token pass-through + margin).
- "pay-per-route" in one x402 tx.
- Sources synthesized from provided Research Findings + internal mossfund reselling research (EU-hosted gateway, 8–15% markup, consolidated invoice play).

**Deprecations:** No Claude 4 Opus/Sonnet (retired ~June 15 2026). Use 4.5/4.6/4.7/4.8 series.

---

## Context

- **Workdir:** /root/.openclaw/workspace/examples/moss-router/ (empty, green field)
- **Zone:** green (new project, zero impact on existing)
- **Related (read-only patterns):**
  - examples/lemoncake-mcp-server/ (sister: Node.js + express, 1-file server.js, bash+curl tests, 9/9 pass, x402 Phase1 on 4021, config.example.json, SKIP_PAYMENT bypass, in-mem state, README with tables + checklist)
  - memory/2026-06-22*.md + MEMORY.md (LemonCake just shipped; Moss Sweden OS + API reselling as core plays)
  - projects/mossfund/ (AI API Reselling + Aggregation research: EU gateway + markup + GDPR moat; top revenue path)
  - skills/grok-build/ + references/prompt-template.md (plan → Telegram approval → execute)
  - skills/x402-mcp-biller/ (future Phase 2 integration path)
  - research/openrouter-models/ + research-cache (model catalog + exact pricing data used here)
- **Inspiration (evaluate, not copy):** LiteLLM, Bifrost (fastest), Portkey, semantic caches (GPTCache/TrueFoundry), Langfuse/OpenLLMetry, provider prompt caching.

**Mossfund positioning:** MossRouter is the technical core for "AI API Reselling + Aggregation as a Service" (EU-hosted gateway, 8–15% markup, consolidated invoice) + future billable MCP layer.

---

## Requirements

### Phase 1 MVP (this plan delivers)
1. Multi-provider abstraction: OpenAI + Anthropic + Google + OpenRouter + Groq (min 5)
2. Cost-tier system: 5 predefined (nano/eco/standard/premium/flagship) + support for custom via config
3. Drop-in OpenAI-compatible HTTP API (change base_url → migrate)
4. CLI: interactive + scriptable (`moss-router chat --tier nano "..."`)
5. In-memory semantic cache: cosine similarity on embeddings (threshold configurable, default 0.92), per-tenant namespacing (X-Moss-Tenant header)
6. Provider failover: auto-retry + fallback providers for same model (simple sequential + backoff)
7. Per-request cost attribution: actual USD using provider-reported tokens + static pricing table
8. Provider-side prompt caching: attempt Anthropic/OpenAI/Google cache hints where applicable (90% discount path)
9. Basic 3-step cascading: nano → standard → premium (configurable, escalate on error)
10. Structured JSON logging (for future observability)

### Phase 2 (mentioned in plan, not impl)
- Redis + pgvector persistent semantic cache
- Langfuse/Helicone-compatible observability endpoint
- MCP server with x402 billing (LemonCake pattern extension)
- Self-tuning from traffic
- Multi-tenant auth + namespaces

### Phase 3 (vision)
- Full confidence-scoring cascade (Not Diamond pattern)
- EU AI Act compliance dashboard
- BankID/Swish self-serve billing
- Agent.market integration + directory registration

### Specific design decisions (resolved in this plan)
- **Language:** Node.js (ES modules) + Express — exact parity with LemonCake (same test style, same stack, fast to extend to MCP x402 Phase 2). Go (Bifrost speed) rejected for ecosystem mismatch. Python (LiteLLM) rejected to avoid duplication and keep Moss-specific EU moat custom logic.
- **Embedding for cache:** OpenAI `text-embedding-3-small` primary (cheap, quality, single SDK). Deterministic mock-embed (hash-based) when MOCK=1 or no key. Future: pluggable.
- **Config format:** JSON (config.example.json + env overrides) — same as LemonCake.
- **Test framework:** bash + curl (`test-moss-router.sh`) — exact LemonCake parity, 0 extra deps, matches verification reqs.
- **Port:** 4022 (sister to LemonCake 4021).
- **Failover strategy:** Simple per-provider retry (max 2) + sequential fallback list in tier. No circuit breaker in MVP (Phase 2). Adaptive backoff stub.
- **OpenAI compat level:** /v1/chat/completions (non-stream MVP; stream Phase 2), /v1/models, extra Moss headers for routing/cost/cache. Special model support: "moss:nano", "moss:eco" etc + X-Moss-Tier header.
- **Cache poisoning defense:** Tenant namespacing + (future) user-id.
- **Mock mode for zero-secret tests:** MOSS_MOCK=1 provides deterministic mock provider + mock embedder. Tests pass with zero real keys.

---

## Out of scope (this plan + Phase 1)

- Real provider API keys in repo (env + mock only)
- Production Hetzner deploy / TLS / systemd
- Auth/tenant system (Phase 2)
- MCP + x402 billing endpoints (Phase 2 — separate plan)
- Streaming support, tool calling full parity, vision
- Using deprecated models (Claude 4 Opus/Sonnet)
- Any edits outside examples/moss-router/
- Full confidence ML cascade, self-tuning, persistent cache
- Observability product (Langfuse clone)

---

## Architecture Overview

**Three-layer routing (per research):**
1. Tier selection (nano...flagship or header/model "moss:xxx")
2. Model + provider selection inside tier (primary → fallbacks)
3. Execution with cache lookup → provider call (with failover + cascade) → cache store + cost calc

**Gateway pattern (centralized, OpenAI drop-in):**
```
Client (HTTP or CLI)
  → MossRouter (port 4022)
    → Semantic Cache (in-mem, cosine 0.92, tenant ns)
    → Tier Router + Cascade logic
    → Provider Abstraction (normalize response + usage)
      ├─ openai (direct or via OR)
      ├─ anthropic (with cache_control hints)
      ├─ google
      └─ openrouter (fallback + extra models)
    → Cost calc (provider tokens * static price) + headers
    → Structured log
```

**Provider interface (internal):**
- `chat({messages, model, temperature?, max_tokens?, system?}) → {content, usage:{prompt_tokens, completion_tokens}, rawModel, provider}`
- Embed for cache: separate `embed(text) → number[]` (1536-d or 128-d mock)
- Support cache hints in request building.

**Cost attribution:** Always use provider-reported `usage` + Moss pricing table (never estimate input tokens client-side). Output in:
- `X-Moss-Cost-USD: "0.000123"`
- `X-Moss-Model: "google/gemini-2.0-flash-lite"`
- `X-Moss-Tier: "nano"`
- `X-Moss-Cache: "hit" | "miss"`
- `X-Moss-Latency-Ms: "87"`
- Body can include `moss: { costUsd, tier, ... }` (opt-in via header)

**Semantic cache key:** `tenant || 'default' + '|' + embed(promptText)` (cosine on full user content concat). Store: {embed, response, usage, costUsd, tier, model, ts}

**Cascade (basic MVP):** Configured order per tier or global. On error from current tier's provider(s), escalate to next tier once. Log "cascade: nano→standard". No confidence scoring (Phase 3).

**Provider failover:** Each tier entry has ordered providers. Try 1, on error/timeout/rate → next, up to maxAttempts. Per-provider simple lastErrorTime for future circuit.

**Provider prompt caching (MVP):**
- Anthropic: if system or first large msg, attach `cache_control: {type: "ephemeral"}`
- OpenAI: note in logs (future header support)
- Google: future context caching API (MVP comment)
- Savings: 90% on repeated prefix (document in README).

**Resilient output:** Strip ```json fences, repair trailing commas for any JSON mode (future).

---

## Tier Definitions (Phase 1 — concrete, based on June 2026 data)

Hardcoded + overridable in config. Prices per 1M tokens (input/output). Always non-deprecated.

- **nano** (ultra-cheap classification, formatting, extraction):
  - Primary: google `gemini-2.0-flash` (or flash-lite) ≈ $0.10 / $0.40
  - Alt via OR: deepseek/deepseek-v4-flash ≈ $0.09–0.14 / $0.18–0.28
  - Fallbacks: openrouter variants

- **eco** (balanced daily driver):
  - google `gemini-2.5-flash` $0.30 / $2.50
  - openai `gpt-4.1-mini` $0.40 / $1.60
  - anthropic `claude-3-5-haiku-20241022` or haiku-4.5 equiv $0.80–1.00 / $4–5

- **standard** (most work):
  - openai `gpt-4.1` $2.00 / $8.00
  - anthropic `claude-sonnet-4.6` $3.00 / $15.00
  - google `gemini-2.5-flash` or grok-4.3 variant

- **premium** (complex reasoning):
  - openai `gpt-4o` or o3 $2.00–2.50 / $8–10
  - anthropic `claude-sonnet-4.6` high
  - gemini-2.5-pro where cost-effective
  - groq `openai/gpt-oss-120b` $0.15/$0.60 — **OpenAI reasoning at Groq speed**

- **flagship** (max quality):
  - openai `gpt-5.5` $5 / $30
  - anthropic `claude-opus-4.8` $5 / $25
  - grok high-end
  - groq `qwen/qwen3.6-27b` $0.60/$3.00 — premium Qwen reasoning

**Groq integration notes:**
- Groq's nano + eco models are *cheaper* AND *10x faster* than equivalent tiers on other providers — natural fit for low-latency workloads
- All Groq models are open-weight (Llama 4, Qwen 3.x, GPT-OSS) — EU AI Act-friendly
- Groq's `gpt-oss-120b` is OpenAI's own open reasoning model — gives premium-tier routing an OpenAI-quality option at ~4x lower cost than GPT-5.5
- 131K context window on all Groq models — competitive with Anthropicartha

Config allows reordering + custom tiers + per-tier price overrides (for margin in future).

Default route strategy: `X-Moss-Tier: eco` or model `moss:eco` or config `defaultTier`.

---

## File Structure (exact)

```
examples/moss-router/
├── package.json
├── server.js                 # Express + main HTTP handlers + boot
├── cli.js                    # CLI entrypoint (chat, models, tiers, etc.)
├── bin/
│   └── moss-router           # #!/usr/bin/env node wrapper (chmod +x)
├── config.example.json
├── README.md
├── test-moss-router.sh       # bash+curl, 10+ tests, MOSS_MOCK=1
├── lib/
│   ├── router.js             # Core: selectTier, route, executeWithFailoverCascade, cost
│   ├── providers.js          # Factory + 5 provider impls: openai/anthropic/google/openrouter/groq
│   ├── cache.js              # In-mem semantic (embed, cosine, lookup/store, ns)
│   ├── pricing.js            # Static tier + model price table + calc (incl Groq)
│   └── utils.js              # json repair, headers, logging, mock embed
└── .env.example (optional)
```

**Providers count: 5** (OpenAI + Anthropic + Google + OpenRouter + Groq).
Groq uses the **same OpenAI SDK** with `base_url: "https://api.groq.com/openai/v1"` — no new dependency.

(Keep total small — single-responsibility files <300 LOC each where possible.)

---

## package.json (proposed)

```json
{
  "name": "moss-router",
  "version": "0.1.0",
  "description": "MossRouter — EU-sovereign multi-tier LLM router (OpenAI compatible) with semantic cache, failover, cost attribution. Phase 1 MVP.",
  "type": "module",
  "main": "server.js",
  "bin": {
    "moss-router": "./bin/moss-router"
  },
  "scripts": {
    "start": "node server.js",
    "start:mock": "MOSS_MOCK=1 node server.js",
    "cli": "node cli.js",
    "test": "bash test-moss-router.sh",
    "test:mock": "MOSS_MOCK=1 bash test-moss-router.sh"
  },
  "engines": { "node": ">=18" },
  "dependencies": {
    "express": "^4.21.0",
    "openai": "^4.52.0",
    "@anthropic-ai/sdk": "^0.27.0",
    "@google/generative-ai": "^0.15.0"
  },
  "devDependencies": {},
  "license": "MIT",
  "keywords": ["llm", "router", "gateway", "openai-compatible", "cost-optimization", "semantic-cache", "eu", "mossfund", "mcp"]
}
```

No extra test runners.

---

## config.example.json (proposed)

```json
{
  "port": 4022,
  "defaultTier": "eco",
  "mock": false,
  "cache": {
    "enabled": true,
    "threshold": 0.92,
    "maxEntries": 2000,
    "ttlSec": 3600
  },
  "cascade": {
    "enabled": true,
    "order": ["nano", "eco", "standard", "premium", "flagship"]
  },
  "failover": {
    "maxRetriesPerProvider": 1,
    "maxTotalAttempts": 3
  },
  "tiers": {
    "nano": {
      "description": "Ultra low cost",
      "models": [
        { "provider": "google", "model": "gemini-2.0-flash", "priceIn": 0.10, "priceOut": 0.40 },
        { "provider": "openrouter", "model": "deepseek/deepseek-v4-flash", "priceIn": 0.12, "priceOut": 0.25 }
      ]
    },
    "eco": { "description": "...", "models": [ ... ] },
    "standard": { "...": "..." },
    "premium": {},
    "flagship": {}
  },
  "providers": {
    "openai": { "apiKeyEnv": "OPENAI_API_KEY", "baseURL": null },
    "anthropic": { "apiKeyEnv": "ANTHROPIC_API_KEY" },
    "google": { "apiKeyEnv": "GOOGLE_API_KEY" },
    "openrouter": { "apiKeyEnv": "OPENROUTER_API_KEY", "baseURL": "https://openrouter.ai/api/v1" }
  },
  "logging": { "structured": true }
}
```

Env overrides for keys + `MOSS_MOCK=1` forces mock path.

---

## Key Internal APIs (for implementer)

**router.js exports (sketch):**
- `async function routeRequest({tier, messages, tenant, ...})`
- `selectProviderForTier(tier)` → {providerName, model, price}
- `async executeWithFailoverAndCascade(...)` 
- `calculateCost(usage, priceTableEntry)`
- `normalizeResponse(raw, provider)`

**providers.js:**
- `createProvider(name, config)` → { chat, embed? }
- impls for each + mockProvider

**cache.js:**
- `async getSimilar(embedding, tenant, threshold)`
- `async store(entry)`
- `cosine(a, b)`
- `async embed(text, provider)` (falls to mock)

**HTTP extras in server.js:**
- Middleware to inject moss headers
- Special model parser: if model starts with "moss:" → tier = that
- X-Moss-Tier header wins
- On cache hit: short-circuit before providers, 0 or tiny latency

---

## CLI Specification

`moss-router` (after npm link or ./bin)

```
moss-router chat --tier nano "Explain EU AI Act in one sentence"
moss-router chat --tier eco --tenant acme-inc "Summarize this: ..."
moss-router chat --interactive
moss-router models --tier eco
moss-router tiers
moss-router route --tier nano --prompt "hello"
moss-router cost-estimate --tier flagship "long prompt..."
```

Output includes cost + model used + cache status. Uses same lib as server.

---

## API Specification (OpenAI compatible + Moss)

Base: `http://localhost:4022/v1`

- `GET /` — info, tiers, version
- `GET /health`
- `GET /v1/models` — list supported moss: tiers + direct models
- `GET /tiers` , `/pricing`
- `POST /v1/chat/completions`
  - Accepts standard OpenAI body (model, messages, temperature, max_tokens, ...)
  - Extra: model can be "moss:nano"
  - Headers: `X-Moss-Tier`, `X-Moss-Tenant`, `X-Moss-Cascade: true`
  - Response: standard + `moss` object + headers listed earlier
- (future) embeddings passthrough

Error shape compatible + extra moss fields.

---

## Test Plan & Verification (map to test-moss-router.sh)

Script style = lemoncake: set -euo, color ok/fail, start server in bg with MOSS_MOCK=1, wait health, count PASS/FAIL, summary, clean pkill.

**Must-cover verification items (from user query):**

- [ ] `npm install && MOSS_MOCK=1 npm start` starts cleanly on 4022 (or PORT)
- [ ] `curl http://localhost:4022/health` + `/` shows tiers + providers (incl Groq)
- [ ] CLI: `./bin/moss-router chat --tier nano "hello"` returns answer from nano-tier model (mock ok)
- [ ] CLI: cascade/escalate test (special prompt that forces nano fail → standard response)
- [ ] CLI: `./bin/moss-router chat --tier eco --speed=fast "..."` prefers Groq model
- [ ] CLI: `./bin/moss-router models --provider groq` lists all Groq models (mock + real)
- [ ] HTTP: `POST /v1/chat/completions` with standard OpenAI payload works (200 + content)
- [ ] HTTP: `model: "moss:nano"` or `X-Moss-Tier: nano` routes to cheapest available (incl Groq `llama-3.1-8b-instant`)
- [ ] HTTP: `model: "moss:premium"` + `X-Moss-Speed: fast` routes to `openai/gpt-oss-120b` (Groq)
- [ ] HTTP: Provider failover — header `X-Moss-Force-Fail: openai` (or mock trigger) → falls back + response ok + log note
- [ ] HTTP: Groq provider failover — header `X-Moss-Force-Fail: groq` → falls back to OpenAI/Anthropic
- [ ] HTTP: Semantic cache hit → sub-100ms (mock) + `X-Moss-Cache: hit` header + identical content
- [ ] Cost attribution: every real response has `X-Moss-Cost-USD` (non-zero for miss) + body moss cost (Groq pricing correct)
- [ ] At least 8–10 automated checks in script (info, cli-nano, cli-cascade, cli-groq, http-standard, http-tier, http-failover, http-groq-failover, http-cache-hit, http-cache-miss-cost, health, structured log sample)
- [ ] `./test-moss-router.sh` exits 0 with "✅ All X passed"
- [ ] `providers.js` exports 5 providers: openai, anthropic, google, openrouter, groq
- [ ] Groq provider uses OpenAI SDK with `base_url: https://api.groq.com/openai/v1` (no new deps)
- [ ] Pricing table includes all 7+ Groq models with correct $/M tokens

Extra in script:
- Two near-identical prompts for cache hit (cosine test)
- Different tenants have isolated caches (no cross-hit)
- Cost header present and numeric
- Server logs contain JSON lines with cost/tier/cache

All tests runnable with zero secrets.

---

## README.md Sketch (structure + key sections)

```md
# MossRouter — Multi-Tier LLM Router (EU Sovereign)

Drop-in OpenAI compatible gateway with cost tiers, semantic cache, failover & per-request USD cost.

## Quick Start
```bash
cd examples/moss-router
npm install
MOSS_MOCK=1 npm start
# Terminal 2:
MOSS_MOCK=1 ./bin/moss-router chat --tier nano "Hello"
MOSS_MOCK=1 ./bin/moss-router chat --tier premium --speed=fast "Explain quantum computing"
curl -X POST http://localhost:4022/v1/chat/completions ...
./test-moss-router.sh
```

## Tiers
Table: nano / eco / standard / premium / flagship with example models + price range (June 2026). Includes Groq models where they win on price or speed (e.g. `llama-3.1-8b-instant` $0.05/$0.08 for nano tier, `openai/gpt-oss-120b` for premium reasoning).

## Providers (5)
- **OpenAI** (gpt-4.1, gpt-5.5, etc.)
- **Anthropic** (claude-opus-4.8, claude-sonnet-4.6, claude-haiku-4.5)
- **Google Gemini** (2.5 Pro/Flash, 2.0 Flash)
- **OpenRouter** (pass-through aggregation, fallback safety net)
- **Groq Cloud** ⚡ (LPU inference, 500–1000 T/s, cheapest + fastest)

## Speed Mode
`X-Moss-Speed: fast` header or `--speed=fast` CLI flag prefers Groq models within the requested tier for latency-sensitive workloads.

## Configuration
config.example.json + env keys + MOCK

## Headers & Extensions
List all X-Moss-* 

## CLI Reference

## HTTP API

## Semantic Cache

## Failover & Cascading

## Comparison
(See full table in plan)

## Phase Roadmap

## Verification
Checklist + `./test...`

References + citations.
```

Include "Built by Mossfund" + LemonCake sister note.

---

## Comparison Table: MossRouter vs OpenRouter / Portkey / LiteLLM

| Aspect                  | MossRouter (Moss)                  | OpenRouter                        | Portkey                          | LiteLLM (BerriAI)               | Groq (direct)                  |
|-------------------------|------------------------------------|-----------------------------------|----------------------------------|---------------------------------|--------------------------------|
| **Hosting**            | Self-hosted (your Hetzner EU)     | US cloud (pass-through)          | Cloud + self OSS                | Self (Python)                  | US cloud (LPU)                |
| **EU / GDPR / AI Act** | Native (Hetzner EU, zero retention default, planned compliance) | No (US)                          | Partial                          | Self-host possible, no built-in EU moat | No (US)                   |
| **Primary pricing**    | Pass-through + planned 8–15% EU markup / future x402 | Provider price + 5.5%            | Subscription + usage             | Self (you pay providers)       | Token-as-you-go (cheap)       |
| **Billing (MCP/x402)** | Phase 2 (LemonCake pattern)       | No                               | No                               | No                             | No                            |
| **Tier system**        | Built-in 5 cost tiers + cascade   | Model lists + fallbacks          | Virtual keys + budgets           | Router + fallbacks             | Model lists                   |
| **Semantic cache**     | In-mem cosine (MVP) + future      | Limited / provider               | Strong (semantic + guardrails)   | Via plugins                    | Limited                       |
| **Speed**              | Node/Express (good)               | Very fast network                | Good                             | Python overhead                | **Fastest (LPU, 500–1000 T/s)** |
| **OSS + MCP ready**    | Yes (Phase 2)                     | API only                         | OSS gateway                      | Strong OSS proxy               | OpenAI-compatible             |
| **Swedish/EU invoice** | Planned (BankID/Swish)            | No                               | No                               | N/A                            | No                            |
| **Moat for EU SMB**    | High (sovereignty + language)     | Low                              | Medium                           | Low                            | Low (US vendor lock)           |
| **Multi-provider**     | **5 providers (Groq included)**   | 100+ via aggregation             | 50+                              | 100+                           | Open-weight only               |

**MossRouter advantage:** EU data residency + future x402 + consolidated Swedish invoice + direct integration with LemonCake MCP + Mossfund ecosystem. Perfect wedge for the researched "AI API Reselling + Aggregation" play (8–15% markup justified by compliance + simplicity).

---

## Phase 2 / Phase 3 Roadmap (in plan for reference)

**Phase 2 (next after MVP success):**
- Persistent cache (Redis + pgvector)
- Observability endpoint (compatible with Langfuse/Helicone event shape)
- MCP server wrapper + x402 per-route / per-token billing (reuse LemonCake patterns)
- Basic multi-tenant (header keys + namespaces)
- Self-tuning (hit-rate, escalate patterns)
- More providers + full streaming + tools

**Phase 3 (vision / grant-aligned):**
- Confidence cascade (Not Diamond style)
- EU AI Act dashboard (transparency logs, human oversight hooks)
- BankID/Swish self-serve + Swedish legal entity billing
- Agent.market registration + discovery
- Production Hetzner HA deploy + EU-only enforcement toggle
- White-label / reseller mode for Moss Sweden OS

---

## Implementation Steps (executable by Grok in execute phase)

1. `cd /root/.openclaw/workspace/examples/moss-router`
2. `npm init -y && npm pkg set type=module ...` (or directly write package.json)
3. Write all files using precise content (server, cli, lib/*, bin wrapper, config, README, test script)
4. `chmod +x bin/moss-router`
5. `npm install`
6. `MOSS_MOCK=1 npm start` (background smoke)
7. Implement/test iteratively until `./test-moss-router.sh` (or `npm test`) passes with ≥10 checks
8. Update README with real quickstart + table
9. Add .env.example + .gitignore (node_modules, .env)
10. Verify all 12 verification checkboxes manually + via script
11. Structured log sample in README
12. (Optional) simple cost attribution test with printed numbers

All steps runnable locally with zero secrets.

---

## Verification Checklist (final — must all pass in execute)

- [ ] `npm install && MOSS_MOCK=1 npm start` works without errors
- [ ] Server starts HTTP on configured port (4022)
- [ ] `./test-moss-router.sh` (MOCK) completes with ≥8–10 tests passed
- [ ] CLI `moss-router chat --tier nano "..."` returns nano-tier response
- [ ] CLI cascade/escalate works
- [ ] CLI `moss-router chat --tier premium --speed=fast` prefers Groq models
- [ ] CLI `moss-router models --provider groq` lists Groq models
- [ ] HTTP OpenAI-format payload succeeds
- [ ] HTTP moss: tier routing works (nano = cheapest)
- [ ] HTTP tier routing includes Groq models per tier
- [ ] HTTP provider failover (simulated fail → fallback) works for Groq + others
- [ ] HTTP semantic cache hit → sub-100ms (mock) + cache-hit header
- [ ] Cost attribution: X-Moss-Cost-USD header + value on responses (incl Groq pricing)
- [ ] README complete (quick start, tiers, config example, comparison table, verification, Groq integration notes)
- [ ] No real keys committed; MOSS_MOCK path complete and documented
- [ ] LemonCake parity achieved (bash/curl, style, docs quality)
- [ ] **Groq integration:** OpenAI SDK with `base_url: https://api.groq.com/openai/v1`, no new deps
- [ ] **Groq models load:** `llama-3.1-8b-instant`, `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `llama-3.3-70b-versatile`

---

## Citations (use in docs & summary)

All from provided Research Findings + internal:
- openai.com/api/pricing, docs.anthropic.com, pricepertoken.com, openrouter.ai/pricing + /docs
- **Groq:** console.groq.com/docs/models, groq.com/pricing, claude5.net/blog/groq-gpt-oss-120b-openai-sdk-base-url-pricing-guide, aipricing.guru/groq-pricing (June 2026)
- github.com/BerriAI/litellm , github.com/maximhq/bifrost
- getmaxim.ai/articles/reduce-llm-cost..., alexcloudstar.com/blog/llm-router-..., bestaiweb.ai/..., truefoundry.com/blog/..., callsphere.ai/blog/failure-mode..., birjob.com/blog/semantic-caching..., arxiv.org/html/2411.05276v3, acethecloud.com/..., morphllm.com/...
- Internal: projects/mossfund research on AI API reselling (EU gateway, markup, GDPR), LemonCake implementation, memory 2026-06-22

---

## Timeline & Next (for Alabama)

**Phase 1 MVP target:** runnable + 10/10 tests + docs in <1 day of focused execute.

**After plan approval:** orchestrator posts summary + path to Telegram. On "ja/kör/ok" → spawn grok-build execute.

**Risks & mitigations (brief):**
- Over-scope: Strict MVP boundaries + mocks only.
- Embed cost in cache: Documented as negligible; mock for tests.
- Latency of routing+embed: Accept 50-150ms p50 overhead (research notes 50-100ms common); optimize later.
- Format drift: Build resilient parser early.

**Post-execute manual:** Register MossRouter as upstream in future LemonCake or agent flows. Consider EU hosting + first resell pilot.

---

**Appendix: Ready-to-use structured prompt (for orchestrator / grok-build execute)**

```
/plan

<PASTE ENTIRE CONTENTS OF THIS plan.md ABOVE THE LINE>

Now implement exactly as specified. Use MOSS_MOCK for all tests. Target zero real keys. Follow LemonCake style for tests/README. When complete, run the verification script and report PASS/FAIL counts + any manual checks.
```

---

**Plan complete.**  
**Location:** `examples/moss-router/plan.md`

**Summary for Telegram (short):**

MossRouter plan.md klar.

- Node.js + Express (LemonCake parity) på 4022
- 5 tiers (nano→flagship) + semantic cache (cosine 0.92) + failover + basic cascade + cost headers
- OpenAI-kompatibel + CLI
- 5 providers (OpenAI/Anthropic/Google/OpenRouter/Groq)
- Full mock mode → 0 secrets, 10+ bash/curl tester
- README + jämförelsetabell (EU moat vs OpenRouter/Portkey/LiteLLM)
- Phase 2 = MCP x402 + persistent + obs (LemonCake extension)
- Allt redo för execute (filstruktur, config, test mapping, citat från research)

Väntar på "ja" / "kör" / "ok" för att starta implementation.

Citations: se plan.md (openai pricing, bifrost, litellm, semantic cache papers, EU moat research, lemoncake etc).

---

**END OF PLAN**
