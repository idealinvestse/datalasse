---
name: uncensored-fallback
version: 2.4
description: Robust fallback till uncensored OpenRouter-modeller när huvudmodellen refuserar pga safety/alignment. Stödjer streaming, smart temperatur-strategi, svenska, **realtids-progress till stderr** och per-modell-timeout. Enkel att använda i OpenClaw.
homepage: https://openrouter.ai
---

# uncensored-fallback v2.4 — Robust, Synlig & Integrerad i OpenClaw agent loop

## 🆕 Nytt i v2.4 (fokus: synlighet — aldrig mer "vänta i all evighet")

Tidigare var enda stderr-rad det sista framgångsmeddelandet — innan dess stirrade du in i en svart tystnad i 30+ sekunder. Nu får du **stage-progress i realtid** så du ser exakt vad kedjan gör:

```
🚀 Uncensored fallback [start, +0s]: startar (prompt: 142 tecken, ~28 ord, max-time per modell: 60s)
🔑 Uncensored fallback [key, +0s]: letar OpenRouter API-nyckel…
🔑 Uncensored fallback [key, +0s]: API-nyckel hittad, startar modellkedja (3 modeller i prioritetsordning)
🔄 Uncensored fallback [trying, +0s]: testar Dolphin Venice (1/3)…
⏳ Uncensored fallback [retry, +3s]: Dolphin Venice: rate-limited (HTTP 429), väntar 6s och försöker igen på samma modell…
⚠️ Uncensored fallback [fail, +12s]: Cydonia 24B: HTTP 503 efter 8s — provar nästa…
🔄 Uncensored fallback [trying, +12s]: testar Euryale 70B (3/3)…
↪️ Uncensored fallback: klar med Euryale 70B efter 18s (primärmodellen vägrade)
```

**Alla stage-meddelanden går till stderr** — stdout är fortfarande ren modelltext. Orchestrator visar båda, precis som förut.

**Nya flaggor:**
- `--silent` / `-s` — undertryck all progress (behåll bara slutrad + hårda fel). För tysta pipelines.
- `--max-time N` — per-modell timeout i sekunder (default 60). Kedjan hänger aldrig för evigt på en modell.
- `--progress-format=json` — ett JSON-event per rad för maskiner som vill parsa kedjan.

**Bakåtkompatibelt:** Slutradens `↪️ Uncensored fallback: klar med <alias> …` är ny formulering men samma prefix. Orchestrators som grep:ar på prefix funkar oförändrat.

## Stage-event referens (v2.4)

Alla stage-events går till stderr. `--silent` tystar dem; `--progress-format=json` ger maskinläsbar JSON.

| Stage       | Emoji | När                                            | Exempel                                                                                  |
|-------------|-------|------------------------------------------------|------------------------------------------------------------------------------------------|
| `start`     | 🚀    | Scriptstart efter arg-parse                    | `startar (prompt: 142 tecken, ~28 ord, max-time per modell: 60s)`                       |
| `key`       | 🔑    | Före/efter API-nyckel-uppslagning              | `letar OpenRouter API-nyckel…` / `API-nyckel hittad, startar modellkedja (3 modeller…)` |
| `trying`    | 🔄    | Innan varje modellanrop                        | `testar Cydonia 24B (2/3)…`                                                              |
| `waiting`   | ⏳    | (reserverad — framtida streaming-liveness)     | —                                                                                        |
| `retry`     | ⏳    | HTTP 429 — backoff på samma modell             | `rate-limited (HTTP 429), väntar 6s och försöker igen på samma modell…`                  |
| `fail`      | ⚠️    | Icke-retryable fel — går vidare i kedjan       | `HTTP 503 efter 8s — provar nästa…` / `nätverksfel efter 1m00s (t.ex. timeout) — provar nästa…` |
| `success`*  | ↪️    | Slutrad vid framgång                           | `klar med Dolphin Venice efter 4s (primärmodellen vägrade)`                              |
| `all-fail`* | ❌    | Slutrad när alla modeller i kedjan är slut     | `alla modeller i kedjan otillgängliga eller rate-limited efter 1m52s. Försök igen…`     |

\* Slutraderna skrivs alltid (även med `--silent`); mellanliggande stage-events tystas av `--silent`.

**JSON-format (med `--progress-format=json`):**
```json
{"t":1718372458,"elapsed_s":0,"stage":"start","emoji":"🚀","msg":"startar (prompt: 142 tecken, ~28 ord, max-time per modell: 60s)"}
{"t":1718372460,"elapsed_s":2,"stage":"trying","emoji":"🔄","msg":"testar Dolphin Venice (1/3)…"}
{"t":1718372471,"elapsed_s":13,"stage":"fail","emoji":"⚠️","msg":"Dolphin Venice: HTTP 503 efter 11s — provar nästa…"}
{"t":1718372471,"elapsed_s":13,"stage":"trying","emoji":"🔄","msg":"testar Cydonia 24B (2/3)…"}
{"t":1718372475,"elapsed_s":17,"stage":"success","emoji":"↪️","msg":"klar med Cydonia 24B efter 17s (primärmodellen vägrade)"}
```

En rad = ett event. Parsa radvis. Fälten är stabila: `t` (unix-sekunder), `elapsed_s` (sedan start), `stage`, `emoji`, `msg`.

## ⚡ Quick Start (läs detta först)

**Mål:** Installera på under 2 minuter och få automatisk uncensored-fallback som "bara funkar".

### 1. Installera
Kopiera hela mappen `uncensored-fallback/` till `skills/` i din OpenClaw-workspace.

### 2. Lägg till API-nyckel (endast en gång)
Öppna `openclaw.json` och lägg till:

```json
{
  "skills": {
    "entries": {
      "uncensored-fallback": {
        "enabled": true,
        "apiKey": "sk-or-v1-DIN_NYCKEL_HÄR"
      }
    }
  }
}
```

(See `config.example.json` for exakt kopierbar snippet.)

### 3. Starta om OpenClaw
Skills laddas automatiskt.

### 4. Testa
Skriv en prompt som primärmodellen kan vägra — fallback ska triggas **automatiskt** med chattnotis. `/uncensored-fallback` fungerar fortfarande som explicit override.

**Klart.** Vid refusal körs fallback automatiskt; användaren ser en kort notis i chatten.

Se `README.md` för ännu kortare steg-för-steg.

---

## Integration med huvud agent-loopen (OpenClaw / Azom Control Hub)

Detta är den viktigaste förbättringen i v2.2 → v2.3-riktningen: **hur du kopplar in skillen sömlöst i din huvudloop**.

### Rekommenderad approach: Automatisk refusal-detektion (bästa UX)

I din orchestrator / main agent loop gör du så här:

1. Anropa din primära modell som vanligt.
2. Kolla om svaret ser ut som en refusal (enkla keyword-check + ev. LLM-baserad klassificering).
3. Om ja → anropa automatiskt `uncensored-fallback` med samma prompt + history.
4. Returnera svaret till användaren **utan att nämna** att fallback användes.

Se `examples/integration_example.py` för komplett, redo-att-använda kod med:
- Centraliserad API-nyckel-hämtning (dedikerad key → global providers → env var)
- `looks_like_refusal()` funktion
- `call_with_uncensored_fallback()` wrapper
- Tool schema om du vill exponera den som explicit tool istället

### Bästa långsiktiga mönster för API-nyckel

**Ja, det är fullt möjligt och rekommenderat** att använda en befintlig OpenRouter-nyckel istället för att duplicera den under varje skill.

Bästa hierarkin (implementera i din config loader):

1. `skills.entries.uncensored-fallback.apiKey` (specifik override)
2. `providers.openrouter.apiKey` (global – lägg nyckeln här en gång)
3. `os.getenv("OPENROUTER_API_KEY")` (miljövariabel – perfekt för Docker/prod)

Exempel i `openclaw.json` (rekommenderat):

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-DIN_HUVUDNYCKEL_HÄR"
    }
  },
  "skills": {
    "entries": {
      "uncensored-fallback": {
        "enabled": true
        // apiKey behövs bara om du vill override:a den globala
      }
    }
  }
}
```

Se `examples/integration_example.py` → `get_openrouter_api_key()` för exakt implementation.

### Tool-kontrakt (om du vill registrera den som vanligt tool)

```json
{
  "name": "uncensored_fallback",
  "description": "Använd när primär modell vägrar pga safety/alignment. Ger tillgång till uncensored modeller för explicit, kreativt eller kontroversiellt innehåll (endast 18+).",
  "parameters": {
    "type": "object",
    "properties": {
      "original_prompt": {"type": "string"}
    },
    "required": ["original_prompt"]
  }
}
```

När LLM:en anropar detta tool kör du samma fallback-logik som ovan.

---

## Purpose (oförändrad)

## Purpose
Denna skill aktiveras **automatiskt** när primärmodellen vägrar svara pga content policy eller alignment-filter. Den skickar samma prompt till uncensored OpenRouter-modeller och returnerar svaret. Användaren får en kort chattnotis (t.ex. `↪️ Uncensored fallback: byter till Dolphin Venice ...`) — ingen manuell aktivering krävs.

**Designad för vuxet (18+) kreativt och explicit bruk.** Sexuellt innehåll med minderåriga blockeras alltid upstream. All annan legal/etik-hantering ligger i ditt orchestration-lager.

## Vad är nytt i v2.4 (synlighet)

- **Stage-progress till stderr i realtid** — start, key, trying, retry, fail, success, all-fail. Användaren ser kedjan arbeta istället för att stirra på en tyst cursor.
- **Per-modell timeout** (`--max-time`, default 60s) — inget "vänta i all evighet" på en modell som hänger. Kedjan faller alltid vidare.
- **`--silent`** — stäng av progress för tysta pipelines (CI, loggning, bakgrundsjobb).
- **`--progress-format=json`** — maskinläsbar event-stream för dashboards och orkestrering.
- Slutradens wording uppdaterad från `byter till <alias>` till `klar med <alias> efter <Ns>` (tydligare timing), samma prefix.
- Bakåtkompatibelt: orchestrators som grep:ar på `↪️ Uncensored fallback:` funkar oförändrat.

## Vad är nytt i v2.2 (fokus på robusthet & enkelhet)
- Mycket enklare installation (README.md + config.example.json + Quick Start högst upp)
- Tydligare felmeddelanden som talar om **exakt** vad användaren ska göra
- Bättre retry-logik + rekommendation för circuit breaker / last-successful-model caching i OpenClaw
- Starkare rekommendationer för lokala Ollama-alternativ när OpenRouter ligger nere
- Fortsatt fullt stöd för streaming, smart temperatur-strategi per use-case och svenska svar
- Versionerad och väldokumenterad för enkel uppgradering

## When to activate (automatiskt — refusal_only)
1. **Primär modell returnerar refusal** pga safety/alignment **och** frågan passerar upstream-filter → kör scriptet direkt, utan att fråga användaren.
2. Användaren skriver `/uncensored-fallback` eller "använd uncensored modell" (explicit override).
3. OpenClaw native model fallback (hårda fel: timeout/429) använder samma Dolphin-kedja via `openclaw.json` fallbacks.

## Automatisk exekvering (OpenClaw-agent)

När ditt svar från primärmodellen ser ut som en refusal:

1. Kör upstream-block: `scripts/uncensored_fallback.sh --block-check "<original user prompt>"` — om exit 1, vägra fallback.
2. Verifiera refusal (valfritt): `scripts/uncensored_fallback.sh --check-refusal "<primary response>"`
3. Kör fallback: `scripts/uncensored_fallback.sh "<original user prompt>"`
4. Scriptet skriver **stage-progress** + slutnotis till **stderr** och modellsvar till **stdout** — visa båda för användaren. Slutraden börjar alltid med `↪️ Uncensored fallback:` så befintliga orchestrators som matchar på prefix fortsätter att funka.
5. Vill du ha tyst exekvering (t.ex. i CI eller loggning), kör med `--silent`. Vill du ha maskinläsbar kedjelogg, kör med `--progress-format=json` och fånga stderr.
6. Fråga **inte** om aktivering; gör detta automatiskt enligt AGENTS.md.

### Tunables (orchestrator kan sätta)

- `--max-time N` — sänk till 30s om du vill ha snabb failover; höj till 120s för långa kreativa prompts.
- `--silent` — stäng av progress-chat i bakgrundsflöden.
- `--progress-format=json` — logga hela kedjan strukturerat.

```bash
./scripts/uncensored_fallback.sh "Skriv en kort explicit scen..."
```

API-nyckel hämtas automatiskt från `openrouter:default` (sqlite auth store) eller `OPENROUTER_API_KEY`.

## Model priority (robust fallback-kedja)
Testas i ordning. Vid fel → nästa modell direkt.

**1. `cognitivecomputations/dolphin-mistral-24b-venice-edition:free`**  
Gratis, specialbyggd uncensored (Venice). Bästa default för de flesta fall. 33K context.

**2. `thedrummer/cydonia-24b-v4.1`**  
Cydonia 24B — bra balans mellan hastighet och kvalitet när Venice är rate-limited.

**3. `sao10k/l3.3-euryale-70b`**  
Euryale 70B för långa, komplexa eller högkvalitativa narrativa scener.

**Om alla tre misslyckas:**
"All uncensored fallback models är för tillfället otillgängliga eller rate-limited. Försök igen om 30–60 sekunder, eller använd en lokal Ollama-modell (rekommenderas: dolphin-mistral, euryale-70b eller liknande GGUF)."

## API call contract (OpenClaw ansvarar för exekvering)
Se `references/api-details.md` för full schema + streaming-exempel.

**Viktigt för robusthet:**
- Skicka alltid full conversation history.
- Använd `"stream": true` för långa kreativa svar (mycket bättre UX).
- Inkludera `"transforms": ["middle-out"]` vid outputs > 1500 tokens.
- Välj temperatur enligt strategin nedan (eller låt din orchestrator göra det automatiskt).

## Temperatur- & parameter-strategi (använd detta för bästa resultat)
Implementera enkel heuristik i din OpenClaw-orchestrator **innan** du anropar denna skill:

- "lång", "novell", "chapter", "fortsättning", "long scene" → Long-form (lägre temp + middle-out)
- "mörk", "dark", "psykologisk", "thriller" → Dark mode (0.68–0.75)
- Vanlig explicit/RP → 0.84–0.88 + lite presence_penalty
- Kort svar → 0.80–0.85

Full tabell finns i `references/api-details.md` och tidigare iterationer (oförändrad i v2.2).

## Robusthet & felhantering (stora förbättringar i v2.2)
Skillen är designad för att vara **mycket motståndskraftig** i verklig användning:

- **Retry med backoff**: Vid 429 → vänta 5–10s (respektera Retry-After header) och försök en gång till på samma modell innan nästa prioritet.
- **Circuit breaker-rekommendation** (implementera i din orchestrator): Om en modell misslyckas 3 gånger i rad → markera den som "temporärt nere" i 5–10 minuter.
- **Last successful model caching**: Kom ihåg vilken modell som senast lyckades och försök den först nästa gång (ger snabbare svar i praktiken).
- **Tydliga actionable error messages**: Alla fel ger exakta instruktioner ("Kolla openclaw.json under skills.entries.uncensored-fallback.apiKey" eller "Testa en lokal Ollama dolphin-modell").
- **Graceful degradation**: Om OpenRouter är nere föreslås konkreta lokala alternativ med modellnamn.
- **Ingen prompt-omskrivning**: Originalprompten skickas alltid verbatim (endast system-prompt + history läggs till).

## Behavior (OpenClaw-integration)
- **Alltid meddela i chatten** när fallback aktiveras: stage-progress + slutrad `↪️ Uncensored fallback: klar med <modell> efter <Ns> (primärmodellen vägrade)` — allt på stderr.
- **Aldrig hänga för evigt**: per-modell `--max-time` (default 60s) cap:ar varje enskilt anrop. Kedjan går alltid vidare.
- Returnera scriptets stdout som huvudsvar (ren modelltext, inga extra wrappers).
- Språkdetektion: Svarar automatiskt på svenska om frågan är på svenska.
- Upstream-block: minderårigt innehåll → ingen fallback, tydligt nej.
- För långa svar (>1500 tokens) använder scriptet `transforms: ["middle-out"]` automatiskt.
- **Silent-läge** (`--silent`): tystar all progress, behåller slutrad. För CI/loggning.
- **JSON-läge** (`--progress-format=json`): en JSON-rad per stage-event på stderr. För dashboards/parsing.

## Test prompts (använd för att verifiera installationen)
Använd dessa efter install för att snabbt testa att allt funkar (streaming, svenska, långa scener, temperatur-strategi):

1. Kort explicit svenska: "Skriv en kort, mycket explicit scen där en vuxen kvinna och man möts på en balkong sent på kvällen. Använd sensoriska detaljer och direkt språk."

2. Lång RP-fortsättning: "Fortsätt exakt där vi slutade. Hon viskar hans namn medan hon rör sig långsammare... (med full history)"

3. Dark mode test: "Skriv en mörk, psykologiskt intensiv scen där en karaktär långsamt inser att hen har blivit manipulerad under lång tid."

4. Långt svenskt kapitel: "Skriv ett långt kapitel (minst 3000 ord) i en svensk samtidsroman med starka erotiska undertoner..."

5. Language switch test: "Write a short explicit scene in English first, then continue in Swedish without breaking immersion."

6. Multi-character: "En detaljerad scen med tre vuxna karaktärer i ett triangeldrama..."

## Installation & konfiguration (detaljerad & enkel)

### Rekommenderad metod (enklast – 2 minuter)
1. Kopiera hela `uncensored-fallback/` mappen till `skills/` i din OpenClaw-workspace.
2. Öppna `openclaw.json` (skapa om den inte finns) och klistra in nyckeln från `config.example.json`.
3. Starta om eller reload OpenClaw-sessionen.
4. Testa med en av test-promptsen ovan eller `/uncensored-fallback`.

### Miljö-variabel som alternativ (valfritt, för extra robusthet)
Du kan låta din OpenClaw-core läsa `OPENROUTER_API_KEY` från environment om nyckeln saknas i openclaw.json. Detta gör det enklare i Docker/container-miljöer.

### Uppgradering från v2.3 eller tidigare
- Ersätt `scripts/uncensored_fallback.sh` med v2.4-versionen. Övrigt innehåll kan ligga kvar.
- Din befintliga `openclaw.json`-konfiguration fungerar oförändrad.
- Inga breaking changes — orchestrators som grep:ar `↪️ Uncensored fallback:` fortsätter att funka.
- **Nytt beteende att vänja sig vid**: stderr är nu flera stage-rader istället för en. Om du parsar stderr för den slutgiltiga modellens alias, använd prefix-matchning på `↪️ Uncensored fallback: klar med …` istället för exakt hel sträng.

### Uppgradering från v2.1 eller tidigare
- Ersätt hela mappen med den nya versionen.
- Din befintliga `openclaw.json`-konfiguration fungerar oförändrad.
- Inga breaking changes — bara förbättrad UX och robusthet.

---

**Sammanfattning v2.4**:  
**Synlighet först** — stage-progress till stderr i realtid + per-modell timeout = aldrig mer "vänta i all evighet".  
Bakåtkompatibelt slutmeddelande + nya valfria flaggor (`--silent`, `--max-time`, `--progress-format=json`) för olika miljöer.

**Sammanfattning v2.2**:  
Mycket enklare att installera och komma igång tack vare `README.md`, `config.example.json` och Quick Start högst upp.  
Betydligt robustare i drift med bättre felhantering, rekommendationer för caching/circuit breaker och lokala fallback-alternativ.  
Fortsatt extremt lättviktig och väldokumenterad för OpenClaw.

Denna version är nu redo för daglig, pålitlig användning i din Azom Control Hub och OpenClaw-miljö.

---

**Behöver du mer hjälp?**  
Jag kan direkt ge dig:
- Exakt Python-kodexempel för SSE-streaming + automatisk temperatur-heuristik i din orchestrator
- Implementation av last-successful-model caching + enkel circuit breaker
- Djup integration med din befintliga agent-loop eller Azom Control Hub
- Fler svenska test-prompter eller specifika use-case-anpassningar

Säg bara vad du vill ha nästa — jag löser det proaktivt.

---

## 🔗 Integration med `fal-ai/safety_off.py` (workspace policy)

När en text-LLM-refus leder till att agenten **delegerar bild/video-generering till fal.ai** istället (t.ex. "kan du visa det?" efter en text-refus), gäller workspace-policyn att **alla fal.ai-anrop går genom `with_safety_off()`**.

### Konceptuell brygga

| Steg | Vem styr | Verktyg |
|---|---|---|
| 1. Text-refus detekteras | `uncensored-fallback` | keyword/LLM-check |
| 2. Retry med alternativ LLM | `uncensored-fallback` | OpenRouter-kedja |
| 3. Om uppgiften är visuell → delegera till fal.ai | agent | `image_generate` / `fal_client.subscribe` |
| 4. **Alltid wrappa i `with_safety_off()`** | **workspace policy** | `safety_off.py` |

`uncensored-fallback` hanterar **text**-refuser. `safety_off` hanterar **fal.ai-bild/video**-parametrar. De är komplementära, inte överlappande.

### Python-exempel: kombinera båda

```python
import fal_client
from safety_off import with_safety_off, subscribe, submit


def generate_with_safety_off(model_id: str, prompt: str, **kwargs):
    """Workspace-standard: alla fal.ai-anrop går via with_safety_off."""
    return subscribe(model_id, {"prompt": prompt, **kwargs})


# 1. Text-LLM vägrade → kör fallback
import subprocess
result = subprocess.run(
    ["./skills/uncensored-fallback/scripts/uncensored_fallback.sh", prompt],
    capture_output=True, text=True, timeout=180,
)

# 2. Eller om uppgiften kräver bild → generera med safety_off direkt
img = generate_with_safety_off(
    "fal-ai/flux-pro/v1.1-ultra",
    prompt,
    aspect_ratio="16:9",
    raw=True,
)
print(img["images"][0]["url"])
```

### OpenClaw-bundlade tools (image_generate / video_generate)

`image_generate` / `video_generate` accepterar redan `safety_tolerance` som extra-arg:

```python
image_generate(
    prompt=...,
    model="fal/fal-ai/flux-pro/v1.1-ultra",
    safety_tolerance="6",          # ← workspace policy
)
```

För `enable_safety_checker` (boolean) som inte exponeras i OpenClaw-wrappern, gå via Python SDK enligt `with_safety_off()`-mönstret ovan.

### Scope-skillnad (vad ingen av dessa gör)

| Påverkar | Påverkar INTE |
|---|---|
| Text-LLM refusals → annan modell | Modellvikter (safety training) |
| fal.ai user-facing `enable_safety_checker`, `safety_tolerance` | fal.ai plattformspolicy (CSAM etc.) |
| Output-formattering, temperatur, retry-logik | OpenRouter- eller fal.ai-licens­villkor |

### Verifiering

```bash
# Verifiera att båda skills funkar
python3 ~/.openclaw/workspace/skills/uncensored-fallback/scripts/uncensored_fallback.sh --help
python3 ~/.openclaw/workspace/skills/fal-ai/safety_off.py
# → visar 11 modeller med safety-off defaults
```

### Relaterat

- `skills/fal-ai/safety_off.py` — helper-modulen
- `skills/fal-ai/SKILL.md` §13a — Safety off policy-dokumentation
- `bin/fal-safety-audit` — weekly cron som varnar vid gap