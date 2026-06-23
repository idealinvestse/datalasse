# Self-modification zones

Use this map before any Grok worker touches files outside a normal coding repo.

## Green — workspace (proceed after clear task)

- `/root/.openclaw/workspace/**`
- `skills/**`, `memory/**`
- `AGENTS.md`, `SOUL.md`, `USER.md`, `IDENTITY.md`, `TOOLS.md`, `HEARTBEAT.md`

Policy: spawn Grok plan phase after the user intent is explicit. Post plan in Telegram; wait for OK before execute phase.

## Yellow — OpenClaw config (approval required)

- `~/.openclaw/openclaw.json`
- `skills.entries.*`, model primary/fallbacks, channel settings
- `commands.ownerAllowFrom`

Policy:

1. Ask owner in Telegram **before plan phase** (task + zone + risk).
2. Run Grok plan phase; post plan summary; wait for second OK before execute.
3. Backup: `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak`
4. After edit: `openclaw config validate`
5. Restart gateway if service/env/model/skills changed.

## Red — secrets and runtime (explicit yes + risk note)

- `gateway.auth.token`, `channels.*.botToken`, API keys
- `~/.openclaw/credentials/**`, auth sqlite/profiles
- systemd units, crontab, nginx, firewall

Policy: never touch without explicit "ja, gör det" plus a one-line risk summary. Prefer `openclaw config set` over hand-editing secrets. Never paste tokens in chat or worker output.

## External repos

- Use an isolated checkout or temp git repo for third-party code.
- Do not run background Grok workers inside `~/Projects/openclaw` upstream tree.

## Post-change logging

After any self-mod, append a short note to `memory/YYYY-MM-DD.md`: what changed, why, and how to roll back.