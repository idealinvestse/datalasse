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
| **shared-calendar**  | `projects/shared-calendar/`  | Produktion (V1.2)| CalDAV + Radicale + cron-fire |
| **sentimentanalys**  | `~/projects/Automatisk-sentimentanalys/` (symlink) | Orientation (Fas 4/5/6) | Svenskt call-center AI |

**Mossfund nyckelfiler:**
- `projects/mossfund/CATALOG.md` — Master single source of truth (27 plays, 4 tiers)
- `projects/mossfund/5a-playbooks/PLAYBOOK.md` — Master playbook
- `projects/mossfund/4a-innovative-ideas/synergies-2026-06-19.md`

**Shared Calendar nyckelfiler:**
- `projects/shared-calendar/cal/agent.py` — CalDAV + CRUD + recurring
- `projects/shared-calendar/bin/fire-reminder` — cron-fired Telegram-reminder
- `https://cal.intelliserve.se` — production URL

**Sentimentanalys:**
- Symlink: `~/.openclaw/workspace/projects/sentimentanalys/`
- Helper: `bin/sentimentanalys-context`
- Bridge: `memory/projects/sentimentanalys/CONTEXT.md`

---

## 🛠️ Skills (14 st)

| Skill                    | Plats                              | Användning          | Kommentar |
|--------------------------|------------------------------------|---------------------|---------|
| **grok-build**           | `skills/grok-build/`               | Hög (default)       | Plan → Telegram-godkännande → Execute |
| **devin**                | `skills/devin/`                    | Hög (NY 06-30)      | Devin.ai API (Cognition Labs) + 4 examples |
| **uncensored-fallback**  | `skills/uncensored-fallback/`      | Medel               | Auto vid safety-refusal |
| **deep-research**        | `skills/deep-research/`            | Hög                 | 6-stage L2 pipeline + goal/watch/feedback |
| **hetzner-cloud**        | `skills/hetzner-cloud/`            | Hög                 | DNS + servrar + multi-project |
| **vps-status**           | `skills/vps-status/`               | Hög (cron)          | `./bin/vps-status` |
| **fal-ai**               | `skills/fal-ai/`                   | Medel               | 1 376 modeller, safety-off policy |
| **fal_image**            | `skills/fal_image/`                | Låg                 | Python-modul + examples |
| **fal-image**            | `skills/fal-image/`                | —                   | ⚠️ Tom placeholder, konsolidering behövs |
| **github**               | `skills/github/`                   | Medel               | `bin/github-watchdog` cron |
| **x402-mcp-biller**      | `skills/x402-mcp-biller/`          | Medel               | MCP + micropayments |
| **brave-search**         | `skills/brave-search/`             | Låg                 | Oberoende sök-kvot |
| **start-crypto-miner**   | `skills/start-crypto-miner/`       | Låg                 | SRBMiner-Multi på hemmalasse |
| **deep-research-test**   | `skills/deep-research-test/`       | Låg                 | Validera research-metodik |

**Total LOC (alla skills):** ~208 000 (hetzner-cloud dominerar med 200K)

**Rekommendation:** Konsolidera fal_image/fal-image/fal-ai till 1 skill (Oscar's godkännande krävs för radering).

---

## 🔬 Research & Autonomy

| Resurs                        | Plats                                      | Status             | Kommentar |
|-------------------------------|--------------------------------------------|--------------------|---------|
| `STATUS_RESEARCH.md`          | root                                       | 21 aktiva goals    | Risk för sprawl — behöver triage |
| `memory/research/`            | `memory/research/`                         | 4.1 MB+            | Cache + state + rapporter |
| `memory/research-cache/`      | `memory/research-cache/`                   | —                  | 24h TTL SQLite |
| `bin/research-*` + deep-research | `bin/` (shims) + `skills/deep-research/`   | L2-system          | Consolidated in skills/deep-research/ (shims preserve bin/ paths); research-goal, research-watch, research-feedback |
| `plan.md`                     | root                                       | Aktiv              | Senaste grok-build plan |
| `memory/grok-plans/`          | `memory/grok-plans/`                       | 3 filer            | Standardisera hit |

**Research-rapporter (juni 2026):**
- `memory/research/devin-api-research.md` (29 KB, 27 källor) — Devin.ai API
- `memory/research/autonomous-agent-patterns-2026.md` (10-20 KB) — agent design (kommer 05:15)
- `memory/research/fal-safety-research.md`, `memory/research/llm-router-design.md` etc.

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

## 📌 Aktuella fokusområden (2026-07-01)

1. ✅ **MEMORY.md + INDEX.md** — klara
2. ✅ **Devin.ai integration** — klar (MOCK-läge, 12+ tester, 4 examples)
3. ✅ **Mailcow + Mailgun** — fullt operationellt (in + ut)
4. ✅ **Failed services fixat** — caddy + cloud-init-hotplugd maskerade
5. ✅ **Mailcow backup-script** — hourly cron
6. ⏸ Research triage-policy (21 goals)
7. ⏸ **Fal-skill konsolidering** (3 → 1, behöver Oscar's godkännande)
8. ⏸ Riktiga Devin credentials (MOCK → live)
9. ⏸ **Wolt-mail follow-up** (kom aldrig fram)

### 🌿 Nattskift 2026-07-01 (03:21-07:00)

- **03:30** VPS health + 2 failed services fixade
- **03:50** MEMORY.md uppdaterad med jun 30-lärdomar (315 → 433 rader)
- **03:55** Git commit `acbdd78` pushad till GitHub
- **04:25** Mailcow backup-script (308K/run, hourly cron)
- **04:50** Skill-audit (14 skills, 1 triplett-notering)
- **05:15** Deep research: autonomous agent patterns (deepseek-v4-pro)
- **05:55** INDEX.md uppdaterad med nya skills/projekt
- **06:30** Cleanup: .pyc, gamla tmp, gamla loggar
- **06:50** Skriv summering till Oscar
- **07:00** Skicka summering via Telegram

---

**Senast uppdaterad:** 2026-07-01 03:30 UTC  
**Av:** Moss (huvudsession, nattskift 03:21-07:00)  
**Nästa:** Konsolidering av recent memory + eventuell subagent-spawn

---

*Denna fil är levande — uppdatera vid varje större förändring.*