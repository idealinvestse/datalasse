# INDEX.md — OpenClaw Workspace Navigation

> **Huvudnavigering för Moss (och Alabama).**  
> Enkel, uppdateringsbar översikt över workspace-struktur, aktiva projekt, skills och research-status.

---

## 📍 Core Identity & Guidelines

| Fil                  | Syfte                                      | Uppdateras av |
|----------------------|--------------------------------------------|---------------|
| `AGENTS.md`          | Arbetsregler, memory-policy, red lines     | Moss          |
| `SOUL.md`            | Persona, vibe, core truths                 | Moss          |
| `USER.md`            | Om Alabama (namn, preferenser, kontext)    | Moss          |
| `IDENTITY.md`        | Moss identitet (namn, emoji, avatar)       | Moss          |
| `TOOLS.md`           | Lokala noter (SSH, kameror, TTS, etc.)     | Moss          |
| `MEMORY.md`          | **Curated long-term memory** (destillerad essens) | Moss     |
| `decisions.md`       | Policy-beslut som påverkar flera sessioner | Moss          |

---

## 🗂️ Projects

| Projekt              | Plats                        | Status          | Kommentar |
|----------------------|------------------------------|-----------------|---------|
| **mossfund**         | `projects/mossfund/`         | Research klar   | Huvudprojekt — 27 plays, 6 playbooks, väntar go-beslut |
| (tomt)               | `projects/`                  | —               | Nästa: skapa underprojekt här |

**Mossfund nyckelfiler:**
- `projects/mossfund/CATALOG.md` — Master single source of truth (27 plays, 4 tiers)
- `projects/mossfund/5a-playbooks/PLAYBOOK.md` — Master playbook
- `projects/mossfund/4a-innovative-ideas/synergies-2026-06-19.md`

---

## 🛠️ Skills (9 st)

| Skill                    | Plats                              | Användning          | Kommentar |
|--------------------------|------------------------------------|---------------------|---------|
| **grok-build**           | `skills/grok-build/`               | Hög (default)       | Plan → Telegram-godkännande → Execute |
| **uncensored-fallback**  | `skills/uncensored-fallback/`      | Medel               | Auto vid safety-refusal |
| **fal-ai**               | `skills/fal-ai/`                   | Medel               | 1 376 modeller, safety-off policy |
| **fal_image**            | `skills/fal_image/`                | Låg                 | — |
| **brave-search**         | `skills/brave-search/`             | Låg                 | Oberoende sök-kvot |
| **deep-research-test**   | `skills/deep-research-test/`       | Låg                 | Validera research-metodik |
| **vps-status**           | `skills/vps-status/`               | Hög (cron)          | `./bin/vps-status` |
| **x402-mcp-biller**      | `skills/x402-mcp-biller/`          | Medel               | MCP + micropayments |
| **node-connect** etc.    | —                                  | —                   | Inte installerade än |

**Rekommendation:** Skapa "workspace-audit" skill via `skill_workshop` när mönster upprepas.

---

## 🔬 Research & Autonomy

| Resurs                        | Plats                                      | Status             | Kommentar |
|-------------------------------|--------------------------------------------|--------------------|---------|
| `STATUS_RESEARCH.md`          | root                                       | 21 aktiva goals    | Risk för sprawl — behöver triage |
| `memory/research/`            | `memory/research/`                         | 4.1 MB             | Cache + state |
| `memory/research-cache/`      | `memory/research-cache/`                   | —                  | 24h TTL SQLite |
| `bin/research-*`              | `bin/` (ej synligt här)                    | L2-system          | research-goal, research-watch, research-feedback |
| `plan.md`                     | root                                       | Aktiv              | Senaste grok-build plan |
| `memory/grok-plans/`          | `memory/grok-plans/`                       | 2 filer            | Standardisera hit |

**Research goals (juni 2026):**
- 21 aktiva (mest mossfund-relaterade)
- 14 klara
- Total cost ~$1.05 över 96 runs (juni)

---

## 📊 Monitoring & Health

| Resurs               | Plats                  | Uppdatering       | Kommentar |
|----------------------|------------------------|-------------------|---------|
| `STATUS.md`          | root                   | Var 5:e minut     | VPS health (CPU, mem, disk, services) |
| `STATUS.json`        | root                   | Var 5:e minut     | Maskinläsbar snapshot |
| `.vps-snapshot-stamp`| root                   | Var 5:e minut     | Timestamp — kolla om <15 min |
| `bin/refresh-vps-snapshot` | `bin/`            | Cron              | Underhålls-skript |

---

## 📁 Memory-hantering

| Typ                        | Plats                            | Policy |
|----------------------------|----------------------------------|--------|
| **Dagliga råloggar**       | `memory/YYYY-MM-DD*.md`          | Arkivera efter 30 dagar om ej refererad i MEMORY.md |
| **Curated long-term**      | `MEMORY.md`                      | Endast huvudsession — destillerad |
| **Research state**         | `memory/research/` + `research-cache/` | 24h TTL + goals.jsonl |
| **Grok plans**             | `memory/grok-plans/`             | Flytta hit + standardisera |

---

## ⚡ Grok Build & Taskflow

- **Default för kod:** `grok-build` skill (plan → Telegram OK → execute)
- **Subtask-orchestration:** `sessions_spawn` + `taskflow` skill (när >1 parallell agent behövs)
- **Research-augmented plans:** `research-dispatcher.sh` triggas automatiskt vid "pricing", "2026", "monetiz" etc.

---

## 🚀 Snabbkommandon (för Moss)

```bash
# VPS health
./bin/vps-status --section=all --no-color

# Research status
cat STATUS_RESEARCH.md

# Senaste memory
ls -lt memory/ | head -5

# Grok build (plan-fas)
skills/grok-build/scripts/run-grok-task.sh plan <workdir> <prompt>

# Skapa ny skill-förslag
skill_workshop action=create name="..." description="..."
```

---

## 📌 Aktuella fokusområden (2026-06-22)

1. **MEMORY.md + INDEX.md** — klara (denna fil)
2. Research triage-policy (21 goals)
3. Skill maturity audit (9 skills)
4. Grok-plan standardisering
5. Överväg `taskflow` + subagents för nästa stora audit

---

**Senast uppdaterad:** 2026-06-22 08:10 UTC  
**Av:** Moss (huvudsession)  
**Nästa:** Konsolidering av recent memory + eventuell subagent-spawn (se alternativ B)

---

*Denna fil är levande — uppdatera vid varje större förändring.*