# Devin integration examples

All examples default to MOCK=1 friendly.

Costs shown are approximate (see research report).

## Files

- `basic_session.py` — create + wait + result (~8 ACU)
- `github_pr_review.py` — structured JSON review output (~20-30 ACU)
- `batch_migration.py` — asyncio + Semaphore(2) parallel runs (N * ~12 ACU)
- `telegram_notifier.py` — long poll + openclaw message notify on done (variable)
- `README.md`

## Run

```bash
cd /root/.openclaw/workspace
MOCK=1 PYTHONPATH=skills/devin python examples/devin-integration/basic_session.py
```

For live, set real keys in env or ~/.config/devin/devin.env and omit MOCK.

## Expectations

- Always provide `--max-acu` (or accept default 10).
- Use for scoped work only.
- Monitor `memory/devin/devin.log`.
