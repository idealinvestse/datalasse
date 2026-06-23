# Exa för Deep Research — Moss Pipeline

**Senast uppdaterad:** 2026-06-18 (efter Exa Setup Guide + docs research)
**Syfte:** Definiera *hur* Moss ska använda Exa API för deep research — rätt ändamål, rätt inställningar, totaltäckande.

---

## 1. Exa capabilities inventory

### Endpoints (5 stycken, var och en med distinkt syfte)

| Endpoint | Roll i deep research | Latency | Kostnad |
|----------|---------------------|---------|---------|
| `POST /search` | Discovery + retrieval + synthesis (med `outputSchema`) | 250ms–40s beroende på `type` | $0.007–$0.015/sök |
| `POST /contents` | Ren text från redan-kända URLs (post-search) | ~500ms | $0.001/1k pages |
| `POST /answer` | Question-first retrieval med citerade svar | ~3s | $5/1k |
| **`POST /research`** | **Automatiserad djupforskning, strukturerad JSON + citations** | ~30s+ | custom |
| `GET /research/{id}` | Hämta research task-status | polling | – |

**Nyckelinsikt #1:** `/research` är en **parallell högnivå-endpoint** som inte kräver manuell multi-step-pipeline. Bra för "deep" frågor där vi vill ha Exas egen koordinerade research.

### Search types (alla 6 typer har olika latency/quality trade-off)

| Type | Speed | Cost | Bäst för |
|------|-------|------|----------|
| `instant` | ~250ms | $7/1k | Real-time chat, voice, "är detta rätt?"-frågor |
| `fast` | ~450ms | $7/1k | Latency-känsliga UI |
| `auto` | ~1s | $7/1k | **Default för de flesta queries** |
| `deep-lite` | ~4s | $10/1k | Lightweight multi-step, färre källor |
| `deep` | 4–15s | $12/1k | Multi-hop med strukturerad output |
| `deep-reasoning` | 12–40s | $15/1k | Forskningsfrågor med multi-step reasoning |

### Benchmarks (FRAMES dataset, multi-hop retrieval)

```
Exa Deep Max      94% / 11s
Claude Opus 4.7   86% / 8s
Gemini 3 Pro      90% / 17s
You.com Exhaustive 90% / 30s
GPT 5.4 (xhigh)   88% / 58s
Perplexity Deep   68% / 82s
Parallel Ultra    88% / 1457s
```

**Nyckelinsikt #2:** Exa Deep Max är bäst i klassen för deep multi-hop. Vi behöver inte chaina flera API:er för det mesta.

### Structured output (`outputSchema`)

- Fungerar på **alla** search types
- Returnerar syntetiserad JSON i `output.content` + field-level citations i `output.grounding`
- Max 10 properties, max nesting depth 2
- Kombinera med `systemPrompt` för source preferences + dedupe

---

## 2. Deep research pipeline för Moss

### Stage-för-stage

```
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: QUESTION DECOMPOSITION                            │
│   Model: grok-4.3                                          │
│   Input:  användarfråga (1 sträng)                         │
│   Output: 3–5 sub-queries, var och en med:                 │
│           - query (str)                                    │
│           - type (instant/fast/auto/deep-lite/deep/reason) │
│           - max_results (int)                              │
│           - output_schema_path (path, optional)            │
│           - synthesis_hints (str, optional)                │
│   Cost:  ~$0.005/request                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: PARALLEL SEARCH                                   │
│   Sources per sub-query (välj utifrån stage-1 hints):      │
│   A. Exa /search (semantic, neural)                        │
│      → discovery, konceptuella queries, "hitta liknande"   │
│   B. Serper /search (keyword, SERP)                        │
│      → keyword queries, "vem sa vad", datum-specifikt      │
│   C. Exa /contents (för kända URLs från stage 1 output)    │
│   Parallelisera via backgrounded bash exec                 │
│   Cost:  5 queries × $0.007 (Exa auto) = $0.035            │
│          5 queries × $0.000 (Serper free) = $0             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 3: DEEP RETRIEVAL (vid behov)                        │
│   Triggers:                                                │
│     - multi-hop fråga ("A vs B vs C")                      │
│     - strukturering krävs (outputSchema)                   │
│     - användaren bad om "deep" / "thorough"                │
│   Method: Exa /search med type=deep eller deep-reasoning   │
│           + systemPrompt + outputSchema                    │
│   Cost:  $0.012–$0.015/query (5x = $0.060–$0.075)         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 4: CONTENT EXTRACTION                                │
│   För URLs som behöver fulltext (RAG-style):               │
│     Exa /contents --max-age=24 --text-max=20000            │
│   Output: ren text, inget HTML                             │
│   Cost:  $0.001/1k pages                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 5: SYNTHESIS                                         │
│   Model: deepseek-v4-pro (eller kimi-k2.6 om browsing)     │
│   Input:  alla stage 2+3+4 resultat (strukturerad JSON)    │
│   Output: sammanhängande rapport, källhänvisningar inline  │
│   Format: Markdown med sektioner per sub-question          │
│   Cost:  ~$0.05 (ca 4k tokens context + 1k output)         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 6: VERIFICATION (optional, för känsliga claims)       │
│   Cross-check:                                             │
│     - Hämta top-3 källa från rapport                       │
│     - Kör ny Exa-sökning på kontroversiella påståenden      │
│     - Flagga avvikelser                                    │
│   Cost:  ~$0.02                                             │
└─────────────────────────────────────────────────────────────┘
```

### Cost-stack per deep-research-request

| Stack | Konfiguration | Kostnad/request |
|-------|---------------|----------------|
| **Budget** | grok-fast + 5×Serper + serper synth | ~$0.06 |
| **Balanced** | grok-fast + 5×Exa-auto + deepseek-pro synth | ~$0.10 |
| **Premium** | grok-fast + 5×Exa-deep + /research | ~$0.30 |
| **Agentic** | Exa /research endpoint (låter Exa koordinera) | ~$0.50 |

### Modeller (validerade på denna OpenRouter-tenant)

| Roll | Modell | Behov |
|------|--------|-------|
| Question decomposition | `openrouter/x-ai/grok-4.3` | speed, instruction-following |
| Search-orchestration | `openrouter/x-ai/grok-4.3` | tool calling |
| Synthesis | `openrouter/deepseek/deepseek-v4-pro` | quality, long context |
| Final report formatting | `openrouter/moonshotai/kimi-k2.7-code` | structured output |

---

## 3. När vi **inte** ska använda Exa

| Situation | Använd istället |
|-----------|-----------------|
| Snabb keyword-match ("vem är VD för X") | Serper.dev |
| Känd URL som ska läsas in | Exa `/contents` (eller curl + trafilatura) |
| Intern data som inte är på webben | Direkt LLM (ingen search) |
| Real-time chat med en mening per svar | `instant` + highlights (eller LLM-cached) |
| Fråga som inte behöver källor | Modell + minne |
| Bulk B2B lead research | Exa Websets ($49/mo, 8k credits) |

---

## 4. Failure modes & fallbacks

| Problem | Detection | Fallback |
|---------|-----------|----------|
| Exa 401/403 | `curl` returns 401 | Serper.dev för keyword, modell-svar utan källor |
| Exa 429 rate-limit | response code 429 | Vänta + retry, eller byt till Serper |
| Exa timeouter (>40s) | wrapper timeout=60 | Returnera partiella resultat, låt synthesis hantera |
| outputSchema tom | `output.content == {}` | Kör om med `systemPrompt` explicitare |
| Modell-failback till qwen | `model_id` matchar ogiltig route | Acceptera degraderad kvalitet, logga till `experiments/` |
| Cost over budget | running sum > $X | Switch till Budget-stack automatiskt |

---

## 5. Implementation roadmap

### ✅ Klart
- [x] `bin/exa-search` wrapper — canonically aligned (auto/fast/instant/deep-lite/deep/deep-reasoning + outputSchema + systemPrompt + maxAgeHours + maxCharacters)
- [x] `bin/serper-search` — 11 endpoints, live-testad
- [x] `bin/load-secrets` — säker nyckel-load
- [x] `bin/deep-research-test` orchestrator (3 lägen: models/apis/report)
- [x] Validerade modeller (2026-06-19: grok-4.1-fast → grok-4.3): grok-4.3, deepseek-v4-flash/pro, minimax-m3, qwen3.6-35b-a3b

### 🔄 Pågående
- [ ] **Bin/exa-contents** — separat wrapper för `/contents` endpoint
- [ ] **Bin/exa-research** — wrapper för `/research` endpoint (om det blir aktuellt)
- [ ] **Bin/deep-research orchestrator v2** — implementerar 6-stage pipeline ovan

### ⏭️ Nästa steg (efter Mossfund-MVP)
- [ ] **Python tool** — `skills/exa-tool/` med function calling för agent-loop
- [ ] **Websets integration** — om B2B-research blir ett use case
- [ ] **Cost guard** — `--budget=0.20` per-request cap

---

## 6. Konkret arbetsflöde för "research X åt mig"

```bash
# 1. Decomposition (Stage 1)
sub_queries=$(grok_query "$USER_QUESTION" --extract=sub_queries.json)

# 2. Parallel search (Stage 2)
for q in $sub_queries; do
  type=$(echo "$q" | jq -r .type)
  case "$type" in
    instant|fast|auto)  bin/exa-search "$(echo "$q" | jq -r .query)" --type=$type --num=$(echo "$q" | jq -r .max_results) & ;;
    keyword)            bin/serper-search "$(echo "$q" | jq -r .query)" --num=$(echo "$q" | jq -r .max_results) & ;;
  esac
done
wait

# 3. Deep retrieval (Stage 3) om multi-hop
bin/exa-search "complex_query" --type=deep --system-prompt="..." --output-schema=@deep.json &

# 4. Content extraction (Stage 4) om RAG-style
bin/exa-contents "$URLS" --text-max=20000 &

# 5. Synthesis (Stage 5) — Modellkoordinerad
synthesize_prompt=$(combine_results stage_2 stage_3 stage_4)
report=$(deepseek_call "$synthesize_prompt")

# 6. Save + deliver
echo "$report" > /tmp/deep-research-$TIMESTAMP.md
```

---

## 7. Sources

- Exa docs: https://docs.exa.ai (getting-started, search, contents, answer, research)
- Exa Setup Guide (skickad av Alabama, 2026-06-18) — funktionsdetaljer
- Exa Deep product page: https://exa.ai/products/deep (FRAMES benchmark)
- HokAI review (2026-05-21): pricing, customers, valuation
- AIPedia wiki (2026-06-12): endpoint pricing matrix, use cases
- PLANNING-PROMPT.md (lokal) — deep-research-workflow adopted
