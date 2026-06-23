---
name: grok-build
description: "Build, fix, implement, refactor, or self-mod via Grok Build plan mode; triggers on bygg/fixa/koda/implementera/grok."
metadata:
  {
    "openclaw":
      {
        "emoji": "⚡",
        "requires":
          {
            "bins": ["grok"],
            "config": ["skills.entries.grok-build.enabled"],
          },
      },
  }
---

# Grok Build

Default coding delegate for Moss. Use Grok Build (`/root/.grok/bin/grok`) with **plan → Telegram approval → execute**.

Prompt template: `{baseDir}/references/prompt-template.md`
Zone map: `{baseDir}/references/self-mod-zones.md`

## When to use (trigger phrases)

Use **immediately** when the user asks (do not ask which tool to use):

- bygg, fixa, implementera, koda, refaktorera, lägg till, uppdatera skill
- build, fix, implement, refactor, add feature, update config, self-mod
- "use grok", "grok build", multi-file edits, non-trivial coding

Reply briefly: "Tar det i Grok Build (planläge)…" then start the workflow.

## When not to use

- Single-line `edit` is enough
- Read-only lookup or web search
- User only wants an explanation, not changes

## Research classification (significantly strengthened June 2026)

`research-dispatcher.sh` now uses a **tiered classification engine** (HIGH | MEDIUM | INTERNAL | NONE) instead of simple keyword matching. This is the default behaviour for all grok-build tasks.

### Decision levels
- **HIGH** — explicit pricing, payment rails (x402), monetization, time-sensitive 2026 facts, deprecation checks, "integrate X402 with MCP" style questions
- **MEDIUM** — service + action patterns (e.g. "how do I use OpenRouter for...", "compare MCP monetization"), or legacy keyword matches
- **INTERNAL** — explicit signals like "purely internal refactor", "no research needed", "skip research", "internal only" → research is **disabled**
- **NONE** — generic coding, internal logic, no external service signals

**Key improvements (June 2026):**
- Real regex matching (`=~`) for SERVICE_ACTION_PATTERNS
- 24-character cache keys + prompt length to reduce collisions
- Contextual negative triggers that correctly allow "refactor the x402 integration" while blocking "purely internal refactor"
- `explain_research_decision` reports the exact triggering pattern
- Automatic hook in `run-grok-task.sh` (runs on every plan phase)
- Cache management: `list`, `clear`, `inspect`, `refresh`

**How it works (automatic):**
1. On every `run-grok-task.sh plan ...` the dispatcher hook runs `classify_research_need` + `explain_research_decision`
2. If HIGH/MEDIUM and cache miss → research sub-agents are recommended (or can be spawned automatically in future)
3. Results are written to `memory/research-cache/<24char-hash>-<len>.json` (48h TTL)
4. On cache hit the previous research block is reused

**CLI (research-dispatcher.sh):**
- `needs|classify|explain <prompt>`
- `prepare|status <prompt>`
- `write <key> <quick> <deep> <sources>`
- `list|clear|inspect|refresh`

Extend patterns by editing `research-dispatcher.sh` (HIGH_CONFIDENCE_PATTERNS, SERVICE_ACTION_PATTERNS, INTERNAL_ONLY_PATTERNS). Cache directory: `memory/research-cache/`. This system makes grok-build substantially more accurate and cost-efficient on external research tasks.

## Workflow (always follow)

1. **Auto research-dispatch (default when relevant)** — run `research-dispatcher.sh detect "$TASK"`.
   - No match → use the exact sentence: "No external research required — internal refactor only."
   - Match:
     - Check `research-dispatcher.sh cache-status "$TASK"`.
     - HIT (fresh <48h) → `RESEARCH=$(research-dispatcher.sh get-block "$TASK")` (includes "(cached Xh ago)").
     - MISS → prepare tasks with `prepare-quick` / `prepare-deep`, emit two `sessions_spawn(...)` (model openrouter/x-ai/grok-4.3, using the filled templates from `references/subagent-*.md`), `yield`, collect sub-agent results, `research-dispatcher.sh save ...`, then `get-block`.
   - Inject `$RESEARCH` into the `## Research Findings` section **before** calling the main planner.
   - See `references/research-augmented-plan.md`, `subagent-quick-serper.md`, `subagent-deep-exa.md`.
2. **Compose prompt** — fill `{baseDir}/references/prompt-template.md` using the research block from step 1 (or the neutral sentence). The enriched prompt is passed to `run-grok-task.sh`.
3. **Yellow/red zone** — get explicit Telegram yes **before** step 4.
4. **Plan phase** — background spawn with the enriched prompt (research already injected in step 1-2):
   ```bash
   PROMPT=$(mktemp -t openclaw-grok-prompt.XXXXXX)
   # write composed /plan prompt (with ## Research Findings) to $PROMPT
   bash background:true workdir:<workdir> command:"{baseDir}/scripts/run-grok-task.sh plan <workdir> $PROMPT <channel> <target>"
   ```
   (The research-dispatcher is only used in the orchestrator turn, before this background call.)
5. **Post plan** — read process log / plan summary (includes research citations); send concise plan to user in Telegram. Ask: "Ska jag köra? (ja/kör/ok)"
6. **Wait** — do NOT execute until owner approves.
7. **Execute phase** — on ja/kör/ok:
   ```bash
   bash background:true workdir:<workdir> command:"{baseDir}/scripts/run-grok-task.sh execute <workdir> <channel> <target>"
   ```
8. **Log** — append outcome to `memory/YYYY-MM-DD.md`.

Pending state lives in `memory/grok-pending.json` between phases.

## Hard rules

- Always compose a structured `/plan` prompt before spawning Grok.
- Never skip the Telegram plan review before execute.
- Launch plan/execute with `background:true`; monitor via `process`.
- Never expose tokens or API keys.
- Yellow/red zone: approval before plan phase, not only before execute.

## Workdir selection

| Task type | workdir |
| --------- | ------- |
| Self-mod / skills / memory | `/root/.openclaw/workspace` |
| OpenClaw config | `/root/.openclaw` (yellow) |
| External project | repo root or isolated temp git repo |

## Approval keywords

Treat as execute approval: `ja`, `japp`, `ok`, `kör`, `kora`, `go`, `yes`, `approve`, `kör på`.

## Status to user

- After plan spawn: taskId, workdir, "plan kommer strax"
- After plan: post summary + ask for OK
- After execute spawn: "kör planen nu"
- On finish: short result (Grok also notifies via `openclaw message send`)

## Process actions

`list`, `poll`, `log`, `kill` via OpenClaw `process` tool.

---
**Note (2026-06 harmonize/refactor + auto research)**: Automatic research dispatch + 48h JSON cache under `memory/research-cache/` (via `scripts/research-dispatcher.sh`) is now the default for tasks matching the keywords. The core plan → Telegram gate → execute flow and all safety rules are unchanged. Backing scripts received light alignment. OpenClaw workspace skills complement .grok bundled ones.