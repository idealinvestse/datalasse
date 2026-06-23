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
