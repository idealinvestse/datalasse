# devin skill — Devin.ai integration

Production-ready client + CLI for Cognition Labs Devin autonomous engineer.

See `SKILL.md` for full docs, setup, commands, and integration patterns.

## Quick start (MOCK)

```bash
MOCK=1 skills/devin/bin/devin doctor
id=$(MOCK=1 skills/devin/bin/devin create "fix the login bug")
MOCK=1 skills/devin/bin/devin watch "$id" --max 30s
MOCK=1 skills/devin/bin/devin result "$id"
```

Default safety: `--max-acu 10`. High values require `--yes`.

## Run tests

```bash
MOCK=1 bash skills/devin/tests/test_devin.sh
MOCK=1 python -m pytest skills/devin/tests/test_devin_client.py -v
```

## Examples

See `examples/devin-integration/`.

All logs go to `memory/devin/devin.log` (keys always masked).
