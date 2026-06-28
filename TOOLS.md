# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Intelliserve LLM Gateway

- **Dashboard:** https://api.intelliserve.se/dashboard
- **API:** https://api.intelliserve.se/v1 (OpenAI-compatible)
- **Docs:** https://api.intelliserve.se/docs
- **Repo:** `idealinvestse/oscar-llm-smart-router`
- **Install:** `curl -sSL https://raw.githubusercontent.com/idealinvestse/oscar-llm-smart-router/main/scripts/install-intelliserve-vps.sh | sudo bash`
- **Profiles:** `cheapest`, `fastest`, `high-security`, `coding`, `research`, `agentic`
- **Headers:** `X-Intelliserve-Profile`, `X-Intelliserve-Session`
- **OpenClaw:** se `oscar-llm-smart-router/docs/openclaw-integration.md`

## Mailcow (e-post för OpenClaw)

- **Admin UI:** https://mail.intelliserve.se (inloggning: `admin` / `moohoo` — byt lösenord direkt)
- **Domän:** `intelliserve.se`
- **Agent-mailbox:** `openclaw@intelliserve.se`
- **Credentials:** `/root/.config/mailcow/openclaw.env` (mode 600)
- **Himalaya config:** `/root/.config/himalaya/config.toml`
- **API-nyckel:** `MAILCOW_API_KEY` i `openclaw.json` env.vars
- **IMAP:** `mail.intelliserve.se:993` (TLS)
- **SMTP:** `mail.intelliserve.se:587` (STARTTLS)
- **Skill:** `himalaya` (aktiverad) — list/read/search/compose/send via CLI
- **Verifiering:** `himalaya folder list` och `himalaya envelope list`

### DNS (krävs för extern leverans)

| Typ | Namn | Värde |
|-----|------|-------|
| A | mail.intelliserve.se | 167.233.38.175 |
| MX | intelliserve.se | mail.intelliserve.se (prio 10) |
| TXT | intelliserve.se | SPF/DKIM/DMARC — hämta från Mailcow admin → DNS |

## Hetzner Cloud (`hetzner-cloud` skill)

- **CLI:** `skills/hetzner-cloud/bin/hcloud-cli`
- **Skill:** `hetzner-cloud` (aktiverad) — DNS, servrar, volumes, firewalls, rDNS
- **Token:** `HCLOUD_TOKEN` permanent lagrad i `~/.config/moss/secrets.env` (mode 600) + speglad i `openclaw.json` → `env.vars` (skapa i Hetzner Cloud Console → Security → API tokens)
- **Default zone:** `HCLOUD_DEFAULT_ZONE=intelliserve.se`
- **Setup venv:** `cd skills/hetzner-cloud && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- **Verifiering:** `skills/hetzner-cloud/bin/hcloud-cli status --json`
- **Health monitor:** `bin/secrets-validate` (hourly cron) — validerar längd (≥60), regex, och live API-probe mot `/v1/datacenters`

## Grok Build

- Binary: `/root/.grok/bin/grok`
- Default model: `grok-build`
- Coding delegate skill: `grok-build` (`/grok-build` or `/skill grok-build`)
- Flow: compose `/plan` prompt → `run-grok-task.sh plan` → Telegram OK → `run-grok-task.sh execute`
- Pending state between phases: `memory/grok-pending.json`
- Owner Telegram: `438805461` (plan review + completion notify)
- Gateway PATH includes `/root/.grok/bin` via systemd

## vps-status

- `./bin/vps-status` — read-only local Ubuntu VPS status (glances/top style). CPU, mem+swap, disk, net, procs, PSI, services, uptime.
  - `./bin/vps-status --section=cpu --no-color`
  - `./bin/vps-status --json | python3 -m json.tool`  (or jq if installed)
  - `--watch=2`, `--top 5`, `--section=mem|disk|procs|all`

- `./bin/refresh-vps-snapshot` — refresh `STATUS.md` + `STATUS.json` from current `vps-status`. Cron: `*/5 * * * *` (see `crontab -l`). Alerts via Telegram on threshold breach (CPU≥90%, MEM≥95%, DISK≥95%, load>2×nproc, failed services).
  - Always-fresh snapshot files: `STATUS.md` (human) + `STATUS.json` (machine).
  - Stale check: `cat .vps-snapshot-stamp` — should be <15 min old.

Add whatever helps you do your job. This is your cheat sheet.

## Research subagents (default: deepseek-v4-pro)

**Per Alabama 2026-06-23**: Use `deepseek-v4-pro` as the default model when spawning research subagents via `sessions_spawn`. Override only when:
- User explicitly requests another model
- Task requires specific capability (vision, code-heavy, ultra-long context)
- Cost ceiling requires `deepseek-v4-flash`

Example brief:
```
sessions_spawn task="..." taskName="..." model="openrouter/deepseek/deepseek-v4-pro" ...
```

Other research-grade models to consider:
- `openrouter/deepseek/deepseek-v4-flash` — budget research
- `openrouter/minimax/minimax-m3` — fast, decent quality

## Web search provider (Brave = primary)

**Per 2026-06-23:** All `web_search` calls (main + subagents) go through Brave Search.

- **Provider:** `tools.web.search.provider = "brave"` (`@openclaw/brave-plugin` v2026.6.5)
- **API key:** `BRAVE_API_KEY` in `openclaw.json` `env.vars` (~1K queries/mo free credit)
- **Parallel-free plugin** stays enabled as fallback
- **Switch back:** `openclaw config set tools.web.search.provider parallel-free` (or unset for auto-detect)
- **Verify:** `web_search` response includes `"provider": "brave"` field

Research workflows using Brave (via `web_search`):
- Main session research queries
- Research subagents: deep-research, research-goal, research-watch, research-feedback, research-refresh, research-prioritize, research-discover
- grok-build research-dispatcher (delegates to subagents)

---



## Internal LLM Router (Phase 1, 2026-06-27)

CLI helper: `bin/llm-call --group=<name> --prompt="..." [--dry-run] [--json]`

| Task group | Default first tier | Cost cap/call | Cost cap/hour | Use case |
|---|---|---|---|---|
| `cron-status-check` | `liquid/lfm-2.5-1.2b-instruct:free` (OR) | $0.0005 | $0.01 | Heartbeat, secrets-validate, vps-snapshot |
| `cron-classify` | `cohere/north-mini-code:free` (OR) | $0.001 | $0.05 | Log triage, alert routing |
| `subagent-research-quick` | `google/gemma-4-31b-it:free` (OR) | $0.002 | $0.20 | Fast factual sub-agents |
| `subagent-research-deep` | `deepseek/deepseek-v4-pro` (OR) | $0.05 | $1.00 | Deep synthesis |
| `subagent-code-quick` | `openai/gpt-oss-20b` (Groq) | $0.01 | $0.30 | Small edits, fixes |
| `subagent-code-deep` | `grok-4.3` (OR) | $0.08 | $0.80 | Multi-file refactor, plans |
| `planning-grok` | `grok-4.3` (OR) | $0.10 | $0.50 | grok-build full plan tasks |
| `interactive-synthesis` | `claude-sonnet-4.6` (OR) | $0.15 | $2.00 | Main session synthesis |

- Free-first: each group defaults to free tier, escalates on 429/5xx/timeout/cost-cap (max 2 jumps).
- Telemetry: JSONL per call → `memory/research/llm-router-telemetry-YYYY-MM-DD.jsonl`. Rollup: `bin/llm-call --group=<g> --prompt="x" --rollup`.
- MOCK: `MOCK=1 bin/llm-call ...` for deterministic zero-cost path.
- Tests: `MOCK=1 python3 -m pytest tests/test_internal_router.py tests/test_internal_router_integration.py -v` (9/9).

## Groq i OpenClaw (2026-06-23)

**Alla 17 Groq-modeller** valbara som `groq/<model>` i OpenClaw. Plugin redan bundled.

### Snabbval
- **Default chat:** `groq/llama-3.3-70b-versatile` (OpenClaws föreslagna)
- **Snabbast/billigast:** `groq/llama-3.1-8b-instant` ($0.05/$0.08, json_mode)
- **Strict schema:** `groq/openai/gpt-oss-20b` (constrained decoding)
- **Vision:** `groq/meta-llama/llama-4-scout-17b-16e-instruct`
- **Audio (Whisper):** `groq/whisper-large-v3-turbo` (default via `voiceModel`)
- **Free router:** `groq/groq/compound` eller `openrouter/free`

### Free router varianter (multi-provider)
OpenRouter free-tier: gemma-4-26b/31b:free, nemotron-3-super-120b:free, hermes-3-405b:free, dolphin-mistral-24b:free, liquid/lfm-2.5-1.2b:free, llama-3.2-3b:free, llama-3.3-70b:free, cohere/north-mini-code:free
Groq free: groq/compound, groq/compound-mini, gpt-oss-safeguard-20b

### Auth
- `GROQ_API_KEY` i `~/.config/moss/secrets-systemd.env` (mode 600)
- Backup: `~/.openclaw/openclaw.json.bak.1782255296`

## Git pushes (fine-grained PAT gotcha)

**Workspace remote:** `https://github.com/idealinvestse/datalasse.git` (master, public)
**Local bare mirror:** `/root/repos/openclaw-workspace.git` (always-synced backup)

Fine-grained PATs (`github_pat_*`) do NOT work with `git credential helper` for push over HTTPS — only classic PATs or SSH keys do. Use URL-rewrite instead:

```bash
git -c "url.https://x-access-token:${GITHUB_TOKEN}@github.com/.insteadOf=https://github.com/" push origin master
```

`~/.bashrc.snippet` defines a `gitpush` wrapper that does this. Source it from `.bashrc` if desired — do NOT auto-modify `.bashrc` without owner approval.

Also: fine-grained PATs **cannot create new repos via API** (no `Administration: write` scope). Create via UI, then push.

---
## Related

- [Agent workspace](/concepts/agent-workspace)
