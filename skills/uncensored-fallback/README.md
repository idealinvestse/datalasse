# uncensored-fallback — Quick Start for OpenClaw

Enkel, robust fallback-skill som automatiskt använder uncensored OpenRouter-modeller när din huvudmodell vägrar pga safety/alignment-filter.

**Perfekt för** explicit innehåll, långa RP-scener, kreativ writing, dark themes m.m. — utan att någonsin nämna att den används.

## ⚡ Snabbast möjliga installation (2 minuter)

1. **Kopiera hela mappen** `uncensored-fallback/` till din OpenClaw `skills/`-katalog:
   ```
   your-openclaw-workspace/
   └── skills/
       └── uncensored-fallback/
           ├── README.md
           ├── SKILL.md
           ├── config.example.json
           └── references/
               └── api-details.md
   ```

2. **Lägg till din OpenRouter API-nyckel** (endast en gång):
   - Öppna `openclaw.json` (eller skapa den i roten av din workspace).
   - Lägg till följande under `skills.entries`:

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

   (Kopiera från `config.example.json` om du vill ha exakt format.)

3. **Starta om / reload** OpenClaw-sessionen.
   - Skills laddas automatiskt.

4. **Testa direkt**:
   - Skriv `/uncensored-fallback` + din fråga, eller
   - Låt agenten trigga den automatiskt nästa gång huvudmodellen refuserar.

Klart! Skillen är nu redo och kommer att användas seamless när det behövs.

## Vanliga kommandon / triggers

- `/uncensored-fallback Skriv en lång explicit scen...`
- "Använd uncensored modell på den här frågan"
- Automatisk trigger när huvudmodellen säger "I can't assist with that..." eller liknande.

## Robusthet & integration (v2.4)

- **🆕 Stage-progress i realtid** på stderr — ser hela tiden vilken modell som testas, om den rate-limit:as, om kedjan faller vidare. Aldrig mer "vänta i all evighet".
- **🆕 Per-modell timeout** (`--max-time`, default 60s) — en modell kan aldrig hänga hela kedjan.
- **🆕 `--silent`** för tysta pipelines (CI, loggning).
- **🆕 `--progress-format=json`** för maskinell parsning.
- Automatisk modell-fallback (3 prioriteter)
- Retry med backoff + rekommendation för circuit breaker + last-success caching
- Tydliga felmeddelanden
- `examples/integration_example.py` med färdig kod för att koppla in skillen automatiskt i din huvud agent-loop + centraliserad OpenRouter-nyckel-hämtning (dedikerad key → global providers → env var)
- Språkdetektion (svarar på svenska om du frågar på svenska)
- Full streaming-stöd för långa svar (mycket bättre UX)

### Exempel: stage-output du nu ser i chatten

```
🚀 Uncensored fallback [start, +0s]: startar (prompt: 142 tecken, ~28 ord, max-time per modell: 60s)
🔑 Uncensored fallback [key, +0s]: API-nyckel hittad, startar modellkedja (3 modeller i prioritetsordning)
🔄 Uncensored fallback [trying, +0s]: testar Dolphin Venice (1/3)…
↪️ Uncensored fallback: klar med Dolphin Venice efter 4s (primärmodellen vägrade)
```

Och om första modellen failar:

```
🔄 Uncensored fallback [trying, +0s]: testar Dolphin Venice (1/3)…
⚠️ Uncensored fallback [fail, +2s]: Dolphin Venice: HTTP 503 efter 2s — provar nästa…
🔄 Uncensored fallback [trying, +2s]: testar Cydonia 24B (2/3)…
↪️ Uncensored fallback: klar med Cydonia 24B efter 6s (primärmodellen vägrade)
```

## Felsökning (vanligaste problemen)

**"OpenRouter API key is invalid or missing"**
→ Kontrollera att nyckeln ligger rätt i `openclaw.json` under exakt `skills.entries.uncensored-fallback.apiKey`

**Inget svar / alla modeller failar**
→ Vänta 30–60 sekunder (rate limit på gratis-tiern). Eller testa en lokal Ollama-modell som `dolphin-mistral` eller `euryale`.

**Vill ha streaming?**
→ Se till att din OpenClaw-huvudloop hanterar SSE när `"stream": true` skickas (se `SKILL.md` + `references/api-details.md` för exakt format).

## Nästa steg / avancerat

- Läs `SKILL.md` för full dokumentation, temperatur-strategier per use-case och test-prompter.
- Läs `references/api-details.md` för tekniska API-detaljer och streaming-exempel.
- Vill du ha hjälp att koppla in streaming-hantering eller automatisk temperatur-val i din OpenClaw-loop? Fråga bara.

Den här skillen är designad för att vara **så enkel som möjligt att installera** och **så robust som möjligt** i vardaglig användning med OpenClaw.

Lycka till! 🚀