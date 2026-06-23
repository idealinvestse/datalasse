# Deep Research Autonomy Roadmap
**Senast uppdaterad:** 2026-06-18 22:09 UTC
**Scope:** Hela deep research-stacken i `~/.openclaw/workspace/bin/` + `skills/deep-research-*`

## 🎯 Målbild: "Self-Driving Research"

> Moss kan själv identifiera forskningsfrågor, köra dem med rätt inställningar, verifiera resultat, och presentera dem — utan mänsklig interaktion i loopen.

## Nuvarande nivå: L0 (Manuell)

Allt körs via `bin/deep-research "fråga"` — manuell trigg, manuell output-tolkning.

---

## 📊 Förbättringsområden (5 kategorier)

### 1. Reliability (tillförlitlighet)

| Problem | Impact | Effort | Prioritet |
|---------|--------|--------|-----------|
| Exa driftstopp = pipeline kraschar | 🟥 Hög | 🟧 Medel | 🔴 P0 |
| OPENROUTER_API_KEY inte tillgänglig i bash | 🟧 Medel | 🟢 Låg | 🟡 P1 |
| Stage 6 heuristik fel-flaggar 3/4 URLs | 🟧 Medel | 🟧 Medel | 🟡 P1 |
| Inget retry vid transient errors (timeout, 429) | 🟧 Medel | 🟢 Låg | 🟡 P1 |

**Konkreta åtgärder:**

- [ ] **bin/lib/retry.sh** — wrapper med exponential backoff (3 retries, 1s/2s/4s)
- [ ] **bin/lib/fallback.sh** — automatisk Exa → Serper fallback per query type
- [ ] **bin/lib/or-key.sh** — workaround för att hämta OPENROUTER_API_KEY från OpenClaw runtime
- [ ] **Förbättrad Stage 6** — använd Serper "verbatim match" istället för "domain match" (minskar false positives)

---

### 2. Performance (hastighet)

| Problem | Impact | Effort | Prioritet |
|---------|--------|--------|-----------|
| Inget cache = samma fråga kostar 2x | 🟧 Medel | 🟧 Medel | 🟡 P1 |
| Stage 2 är parallell men Stage 3 är sekventiell | 🟢 Låg | 🟢 Låg | 🟢 P2 |
| Inga timeouts per stage | 🟢 Låg | 🟢 Låg | 🟢 P2 |

**Konkreta åtgärder:**

- [ ] **bin/cache-research** — SQLite-baserat result cache (key = query hash, TTL = 24h)
- [ ] **Stage 3 parallelisering** med cost-guard awareness (kör 2 i taget istället för 1)
- [ ] **Per-stage timeouts** — `--stage-timeout=30` per stage, graceful degradation

---

### 3. Autonomy (självständighet) ⭐ STÖRSTA GAP

| Problem | Impact | Effort | Prioritet |
|---------|--------|--------|-----------|
| Manuell trigg (ingen auto-discovery av frågor) | 🟥 Hög | 🟥 Hög | 🟡 P1 |
| Ingen self-evaluation (kollar inte om resultatet är bra) | 🟧 Medel | 🟧 Medel | 🟡 P1 |
| Moss lär sig inte från tidigare körningar | 🟧 Medel | 🟧 Medel | 🟢 P2 |
| Ingen feedback-loop (användaren säger inte vad som var bra) | 🟧 Medel | 🟧 Medel | 🟢 P2 |

**Konkreta åtgärder:**

- [ ] **`bin/research-watch`** — cron-baserad bevakning: bevaka keywords/topics, kör deep research när något viktigt händer
- [ ] **`bin/research-quality`** — Stage 7: automatisk kvalitetsbedömning
  - Räkna unika källor per påstående (mål: ≥2)
  - Upptäck cirkelresonemang (URL som bara hänvisar till sig själv)
  - Verifiera att synthesis-citat matchar källan
- [ ] **`bin/research-feedback`** — `--rate=N` flagga för att låta användaren betygsätta, spara till `~/.config/moss/research-ratings.jsonl`
- [ ] **Daily research digest** — cron `0 8 * * *` kör 2-3 frågor relaterade till Mossfund, sammanfatta, leverera till Telegram

---

### 4. Observability (insyn)

| Problem | Impact | Effort | Prioritet |
|---------|--------|--------|-----------|
| Ingen metrics över tid (cost, latency, success rate) | 🟧 Medel | 🟧 Medel | 🟡 P1 |
| Inga alerts när något går fel | 🟧 Medel | 🟢 Låg | 🟡 P1 |
| Svårt att jämföra olika pipelines | 🟢 Låg | 🟧 Medel | 🟢 P2 |

**Konkreta åtgärder:**

- [ ] **`bin/research-metrics`** — append till `~/.config/moss/research-metrics.jsonl`:
  ```json
  {"timestamp": "...", "query": "...", "stages_run": 5, "total_cost": 0.07,
   "latency_s": 45, "sources_found": 12, "verification_pass_rate": 0.75}
  ```
- [ ] **`STATUS_deep_research.md`** — auto-genererad dashboard (körs av cron)
  - Total queries denna vecka
  - Total cost denna vecka
  - Genomsnittlig verification_pass_rate
  - Modeller använda
  - API health (Exa/Serper status)
- [ ] **Telegram alerts** — om cost > $X eller pass_rate < 50%

---

### 5. Extensibility (utökningsbarhet)

| Problem | Impact | Effort | Prioritet |
|---------|--------|--------|-----------|
| Stage 4 (contents extraction) är inte auto-kallad | 🟢 Låg | 🟢 Låg | 🟢 P2 |
| Inget plugin-system för nya search providers | 🟢 Låg | 🟧 Medel | 🟢 P2 |
| bin/deep-research är 12 KB monolith | 🟢 Låg | 🟧 Medel | 🟢 P2 |

**Konkreta åtgärder:**

- [ ] **Stage 4 auto-invoke** — om Stage 6 hittar "stale" URLs, kör Stage 4 för att hämta fresh content
- [ ] **`bin/research-plugin`** — interface för nya providers (Tavily, Brave, Firecrawl)
- [ ] **Refactor** bin/deep-research → dela upp i `bin/lib/stage-{1,2,3,4,5,6}.sh`

---

## 🎯 Prioriterad handlingsplan (nästa 2 veckor)

### Vecka 1: Reliability + Observability (grundläggande hygiene)

| Dag | Uppgift | Effort |
|-----|---------|--------|
| Mån | bin/lib/retry.sh + bin/lib/fallback.sh (Exa→Serper) | 2h |
| Mån | bin/lib/or-key.sh workaround | 1h |
| Tis | bin/research-metrics + STATUS_deep_research.md | 3h |
| Ons | Stage 6 förbättring (Serper verbatim match) | 2h |
| Tor | Test coverage för retry/fallback | 2h |
| Fre | Telegram alerts för cost + health | 2h |

### Vecka 2: Autonomy (största värdet)

| Dag | Uppgift | Effort |
|-----|---------|--------|
| Mån | bin/research-quality (Stage 7) | 4h |
| Tis | bin/research-watch + cron | 3h |
| Ons | bin/research-feedback + ratings | 2h |
| Tor | Daily research digest (cron 8am) | 3h |
| Fre | End-to-end test av daily digest → Telegram | 2h |

---

## 🚀 Quick wins (kan börja idag)

### A) bin/lib/retry.sh (30 min)

```bash
retry_with_backoff() {
  local max_attempts=3
  local delay=1
  local cmd="$1"
  for attempt in $(seq 1 $max_attempts); do
    if eval "$cmd"; then return 0; fi
    echo "  ⚠️ Attempt $attempt failed, retrying in ${delay}s..." >&2
    sleep $delay
    delay=$((delay * 2))
  done
  return 1
}
```

Integrera i `bin/deep-research`:
```bash
retry_with_backoff "$EXA_BIN \"$Q\" --type=$TYPE --num=$N > $WORKDIR/exa-$i.json"
```

### B) bin/research-quality (Stage 7) — 1h

Lägger till Stage 7 som kör EFTER synthesis:
- Räknar unika URLs per påstående
- Detekterar hallucinerade källor (URL i rapport som inte finns i sökresultat)
- Ger 0-100 score, appendas till rapport

### C) bin/cache-research (cache) — 1h

```bash
# Använd: bin/cache-research "my query" [--ttl=24h]
# Om finns i cache: print cached JSON
# Om inte: kör deep-research, spara result
```

---

## 🧭 Vision: "Self-Driving Research" (3-6 mån)

**Steg 1 (nu):** Manuell körning → L0
**Steg 2 (1 mån):** Cron + cache + retry → L1 (semi-autonom)
**Steg 3 (3 mån):** Self-evaluation + learning → L2 (adaptiv)
**Steg 4 (6 mån):** Auto-discovery + autonomous research → L3 (full autonomi)

**L3 capability:** Moss kan:
- Läsa Mossfund README + STATUS.md
- Identifiera osäkra påståenden / luckor i research
- Köra deep research automatiskt för att fylla luckorna
- Verifiera att nya data inte motsäger existerande
- Leverera daily digest till Telegram med bara viktigaste insikterna

**Detta är vad Mossfund MVP kunde bli** — Moss som forsknings-delegat som hittar intäktsidéer själv.

---

## 📎 Relaterade filer

- `bin/deep-research` (12.4 KB) — huvudpipeline
- `bin/exa-search`, `bin/serper-search` — search providers
- `bin/exa-contents`, `bin/exa-research` — Exa utilities
- `bin/research-decompose` — Stage 1
- `bin/tests/*` — verifiering
- `skills/deep-research-test/INTEGRATION-EXA.md` — Exa-specifika detaljer
- `skills/deep-research-test/CONFIG.md` — model + API stack
- `skills/deep-research-test/SKILL.md` — orchestrator-dokumentation

---

## Phase 2 design (research-state extensions)

### bin/research-watch
- Cron-driven: pick active goals with unanswered plan steps
- Run `bin/deep-research` per step; `--mark-step=step-N`
- Respect budget caps per goal/day

### bin/research-feedback
- `--rate=1-5` on reports; append to `~/.config/moss/research-ratings.jsonl`

### bin/research-metrics
- Aggregate `metrics.jsonl` → trends, cost/quality charts data

### research-goal plan (full LLM)
- Call `bin/research-decompose`; map sub-queries → plan steps
- Set `total_steps` from array length

### Adaptive prioritization + self-improving prompts
- LLM reviews goals + recent runs; suggests priority changes
- Track query formulations vs `verification_pass_rate`
