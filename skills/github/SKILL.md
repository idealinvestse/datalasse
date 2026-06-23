---
name: "github"
description: "Manage GitHub repos, issues, PRs, releases, and workflows via git + curl + jq (gh CLI when available)."
---

# GitHub

Operate on GitHub from the workspace. Prefers `gh` CLI when installed; otherwise wraps the REST API via `scripts/gh.sh` (curl + jq). Reads `GITHUB_TOKEN` (or `GH_TOKEN`) from env for write operations.

## Quick start

```bash
# Auth check + rate limit
./scripts/gh.sh status

# Repo ops
./scripts/gh.sh repo list --user idealinvestse
./scripts/gh.sh repo view idealinvestse/openclaw-skills
./scripts/gh.sh repo create my-new-thing --private --description "..."
./scripts/gh.sh repo clone idealinvestse/openclaw-skills ~/code/openclaw-skills

# Issue ops
./scripts/gh.sh issue list --repo idealinvestse/openclaw-skills
./scripts/gh.sh issue create --repo idealinvestse/openclaw-skills --title "Bug" --body "..." --label bug,priority
./scripts/gh.sh issue close 42 --repo idealinvestse/openclaw-skills
./scripts/gh.sh issue comment 42 --repo idealinvestse/openclaw-skills --body "Reproduced on main"

# PR ops
./scripts/gh.sh pr list --repo idealinvestse/openclaw-skills
./scripts/gh.sh pr create --repo idealinvestse/openclaw-skills --head feature-x --base main --title "..." --body "..."
./scripts/gh.sh pr merge 17 --repo idealinvestse/openclaw-skills --method squash

# Releases
./scripts/gh.sh release list --repo idealinvestse/openclaw-skills
./scripts/gh.sh release create v1.0.0 --repo idealinvestse/openclaw-skills --generate-notes

# Workflows / Actions
./scripts/gh.sh workflow list --repo idealinvestse/openclaw-skills
./scripts/gh.sh workflow runs --repo idealinvestse/openclaw-skills --workflow ci.yml
./scripts/gh.sh workflow run ci.yml --repo idealinvestse/openclaw-skills --branch main

# Search
./scripts/gh.sh search repos "moss router"
./scripts/gh.sh search issues "is:open label:bug"
```

## Subcommand reference

- `status` — auth check, scopes, rate limit
- `repo <list|view|create|clone|fork|delete>` — repo CRUD
- `issue <list|view|create|close|comment>` — issues
- `pr <list|view|create|merge>` — pull requests
- `release <list|create|delete>` — releases + tags
- `workflow <list|runs|run|logs>` — Actions
- `search <repos|issues|code|prs>` — global search

Common flags: `--repo OWNER/NAME`, `--state open|closed|all`, `--limit N`, `--yes` (skip confirm).

## Auth

Read-only works without a token (60 req/h IP-limited). Write operations need `GITHUB_TOKEN` with scopes:
- `repo` (full) — private repos + write
- `public_repo` — public read/write only
- `workflow` — trigger Actions

Set in `~/.openclaw/workspace/.env` (workspace-local) or export inline. **Never commit.**

## Conventions

- JSON output by default; pipe to `jq` for filtering
- Destructive ops (`delete`, `merge`, `close`) prompt unless `--yes` is passed
- Idempotent: list → filter → act; never assume IDs
- Script uses `set -euo pipefail`; safe for cron + automation

## gh CLI fallback

If `gh` becomes available (`apt install gh` or `brew install gh`), the skill's intent stays the same. Use `gh` directly for richer UX; the wrapper scripts remain for sandboxed/restricted envs.

## Deep dives

- `references/auth.md` — token scopes + setup
- `references/api.md` — endpoints, rate limits, pagination
- `references/examples.md` — common workflows (release pipeline, issue triage, PR review)
