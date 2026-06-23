# MossRouter — Multi-Tier LLM Router (EU Sovereign)

Drop-in OpenAI compatible gateway with cost tiers, semantic cache, failover, Groq LPU speed, & per-request USD cost attribution.

**Status:** Phase 1 MVP — runnable with `MOSS_MOCK=1`, zero secrets.

---

## Quick Start

```bash
cd examples/moss-router
npm install
MOSS_MOCK=1 npm start
# other terminal:
MOSS_MOCK=1 ./bin/moss-router chat --tier nano "Hello from Moss"
MOSS_MOCK=1 ./bin/moss-router chat --tier premium --speed=fast "Explain EU AI Act fast"
curl -X POST http://localhost:4022/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Moss-Tier: eco" \
  -d '{"model":"moss:eco","messages":[{"role":"user","content":"Hi"}]}'
MOSS_MOCK=1 npm test
```

---

## Tiers (June 2026 pricing)

| Tier     | Purpose                  | Example winners (incl Groq)                     |
|----------|--------------------------|-------------------------------------------------|
| nano     | Ultra cheap              | groq/llama-3.1-8b-instant ($0.05/$0.08), gemini-2.0-flash |
| eco      | Daily balance            | groq/gpt-oss-20b ($0.075/$0.30), gemini-2.5-flash |
| standard | Quality work             | groq/llama-3.3-70b + gpt-4.1                    |
| premium  | Reasoning                | groq/gpt-oss-120b (OpenAI-quality at low cost + speed) |
| flagship | Max quality              | gpt-5.5 / claude-opus-4.8 + groq qwen           |

Use `X-Moss-Tier: nano` or `model: "moss:nano"`.

---

## Providers (5)

- **OpenAI**
- **Anthropic** (prompt caching hints on system)
- **Google Gemini**
- **OpenRouter** (pass-through + fallback)
- **Groq Cloud ⚡** (LPU, 500-1000 T/s, cheapest/fastest for many tiers, OpenAI SDK compatible)

Groq base: `https://api.groq.com/openai/v1` — **no new dependency**.

---

## Speed Mode (Groq LPU preference)

```bash
MOSS_MOCK=1 ./bin/moss-router chat --tier premium --speed=fast "..."
# or header
curl ... -H "X-Moss-Speed: fast"
```

Routes to Groq models first within the tier for lowest latency.

---

## Configuration

See `config.example.json`. Override with env vars + `MOSS_MOCK=1`.

---

## HTTP API (drop-in)

Base `http://localhost:4022/v1`

- `POST /v1/chat/completions` — full OpenAI shape + moss extensions
- Headers: `X-Moss-Tier`, `X-Moss-Tenant`, `X-Moss-Speed`, `X-Moss-Force-Fail`, `X-Moss-Cascade`
- Response headers: `X-Moss-Cost-USD`, `X-Moss-Model`, `X-Moss-Tier`, `X-Moss-Cache`, `X-Moss-Latency-Ms`, `X-Moss-Provider`

Extra:
- `GET /tiers`, `GET /v1/models`, `GET /v1/moss/route`

---

## CLI

```
moss-router chat --tier nano "prompt"
moss-router chat --tier eco --speed=fast --tenant acme "prompt"
moss-router models --provider groq
moss-router tiers
moss-router interactive
```

---

## Semantic Cache

In-memory cosine similarity (default 0.92). Per-tenant isolation via `X-Moss-Tenant`.

Cache hits return instantly with `X-Moss-Cache: hit` and `$0` cost.

---

## Failover & Cascading

- Per-provider retry + ordered fallbacks inside tier.
- Basic cascade: on full tier failure, escalate per `cascade.order`.
- Trigger simulation: `X-Moss-Force-Fail: groq`

---

## Cost Attribution

Every response includes:

- `X-Moss-Cost-USD`
- Body `moss: { costUsd, tier, provider, cache }`

Uses provider-reported tokens × static June 2026 table (Groq prices included).

---

## Comparison Table

See `plan.md` for full MossRouter vs OpenRouter / Portkey / LiteLLM / Groq.

**MossRouter moat:** Self-hosted EU, GDPR/AI Act ready, future x402 MCP billing (LemonCake), consolidated invoice, Groq + 4 other providers, semantic cache + tiers built-in.

---

## Verification

```bash
MOSS_MOCK=1 npm test   # or ./test-moss-router.sh
```

Must pass all checks (info, CLI nano/cascade/speed/groq-models, HTTP standard + tier + failover + Groq failover + cache + cost headers + tenant isolation).

See plan.md for complete checklist.

---

## Phase Roadmap

**Phase 1 (current):** 5 providers + tiers + in-mem semantic cache + failover + cascade + cost + CLI + mock tests.

**Phase 2:** Persistent cache, observability, MCP + x402 (LemonCake pattern), multi-tenant.

**Phase 3:** Confidence cascade, EU AI Act dashboard, BankID/Swish billing, Agent.market.

---

**Built by Mossfund** — sister project to LemonCake MCP server.

References & citations in `plan.md`.
