---
name: devin
description: "Devin.ai (Cognition) autonomous AI software engineer integration. REST v3 client + CLI for delegated coding tasks with strong cost safety and polling."
---

# devin

**Autonomous AI software engineer (git/shell/IDE/browser) from Cognition Labs. Best for well-scoped delegated coding tasks via poll-only REST API.**

## When to use

- Bug fixes from clear tickets/issues
- Code migrations, test generation, boilerplate
- PR reviews + comments
- Background/long-running scoped work (cron / subagent / notifier)

**When NOT to use**
- Real-time interactive debugging or pair-programming
- Ambiguous architecture / greenfield design
- Anything requiring tight human-in-the-loop every minute

## Setup (4 steps)

1. In Devin web UI: create Service User → generate `cog_` key + note `org-xxx` ID.
2. Run doctor (auto-creates config):
   ```bash
   skills/devin/bin/devin-doctor
   ```
3. Edit `~/.config/devin/devin.env` (it is chmod 600).
4. Re-run doctor until "OK".

## Common commands (copy-paste)

```bash
# Health + creds
MOCK=1 skills/devin/bin/devin doctor

# Create (prints ONLY session_id — pipeable)
id=$(MOCK=1 skills/devin/bin/devin create "fix the auth bug in login.py")
id=$(MOCK=1 skills/devin/bin/devin create --repo owner/repo --max-acu 15 "add tests for X")

# High ACU needs confirmation
MOCK=1 skills/devin/bin/devin create --max-acu 80 --yes "big migration"

# Status / list
MOCK=1 skills/devin/bin/devin status "$id"
MOCK=1 skills/devin/bin/devin list --limit 10

# Interact
MOCK=1 skills/devin/bin/devin send "$id" "also write unit tests"
MOCK=1 skills/devin/bin/devin attach "$id" /path/to/spec.pdf

# Wait
MOCK=1 skills/devin/bin/devin watch "$id" --max 30m

# Final output
MOCK=1 skills/devin/bin/devin result "$id"

# Cancel
MOCK=1 skills/devin/bin/devin kill "$id"

# Logs (integration log, keys masked)
skills/devin/bin/devin logs -f
```

## Cost safety (IMPORTANT)

- **Always** set `--max-acu` (CLI default = 10).
- `> 50` requires explicit `--yes` (or `yes=True` in client).
- Every create is logged with max_acu + final ACU consumed.
- Use `estimate_cost()` / doctor to preview `~$22.50 (10 ACUs @ $2.25)`.
- Leave hook for `bin/devin-stats` (future).

## Polling pattern

No webhooks/SSE. Recommended:

```python
client.wait_for_completion(session_id, poll_interval=10, max_wait=3600)
# internal: 10s → 30s exponential backoff + jitter
```

## Error codes

| Code | Meaning | Action |
|------|---------|--------|
| 401 | Bad/missing key | Check ~/.config/devin/devin.env + doctor |
| 403 | Insufficient perms / org | Verify service user role |
| 404 | Unknown session_id | Check id spelling |
| 429 | Rate limit | Backoff (client does this) + Retry-After |
| 5xx | Transient | Auto retry 3x |
| network | Timeout etc. | Auto retry |

## Integration examples

**Cron (nightly PR review)**
```bash
0 3 * * * cd /root/.openclaw/workspace && MOCK=0 /root/.openclaw/workspace/skills/devin/bin/devin create --repo myorg/watchlist --max-acu 30 "Review open PRs and leave comments" >> memory/devin/cron.log 2>&1
```

**Subagent**
Use `sessions_spawn` with task:
`id=$(devin create ...); devin watch $id; devin result $id`

**Telegram long session notifier**
See `examples/devin-integration/telegram_notifier.py` (polls + uses existing message tool).

All activity → `memory/devin/devin.log`

## Sources

Full research + reference wrapper: `memory/research/devin-api-research.md`

Official docs: https://docs.devin.ai/

## Development / testing

```bash
MOCK=1 bash skills/devin/tests/test_devin.sh
MOCK=1 python -m pytest skills/devin/tests/test_devin_client.py -v
```

## Constraints followed

- Python 3.11+
- requests + stdlib only
- 600 perms on credentials
- MOCK everywhere for tests
- Key never logged raw (`cog_****xxxx`)
- Matches AGENTS.md conventions
