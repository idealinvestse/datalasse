# GitHub Auth Setup

The skill reads `GITHUB_TOKEN` first, then `GH_TOKEN` as fallback.

## Quickest path (CLI only, fine-grained)

1. https://github.com/settings/tokens?type=beta → **Generate new token** (fine-grained)
2. Resource owner: your account (or orgs you manage)
3. Repository access: **All repos** or specific
4. Permissions:
   - **Contents:** Read + Write (push, releases)
   - **Issues:** Read + Write
   - **Pull requests:** Read + Write
   - **Actions:** Read + (optional) Write (trigger workflows)
   - **Metadata:** Read (default — required)
5. Expiry: 90 days (recommended)

## Classic token (broader, simpler)

Use only if fine-grained is too restrictive. https://github.com/settings/tokens

Scopes:
- `repo` — full private repo access
- `public_repo` — public repos only
- `workflow` — update Actions

## Storage

**Never commit.** This workspace uses `~/.config/moss/secrets.env` (mode 600) as the canonical secret store, managed by `bin/load-secrets` and `bin/secrets-validate`.

Add the token (only once):

```bash
printf '\nexport GITHUB_TOKEN=%q\n' "$YOUR_TOKEN" >> ~/.config/moss/secrets.env
chmod 600 ~/.config/moss/secrets.env
```

Or use the workspace helper:

```bash
# Source secrets in current shell (eval for non-interactive)
eval "$(~/.openclaw/workspace/bin/load-secrets)"
~/.openclaw/workspace/skills/github/scripts/gh.sh status
```

For one-off commands, export inline:

```bash
GITHUB_TOKEN=ghp_... ./scripts/gh.sh repo create my-repo --private
```

## Verify

```bash
~/.openclaw/workspace/bin/secrets-validate
~/.openclaw/workspace/skills/github/scripts/gh.sh status
```

Expect:
- `OK: GITHUB_TOKEN (93 chars)` and `OK: GitHub live (user: <you>, 5000 req/h)` from the validator
- `✓ Authenticated as: <your-username>` + `Rate limit: ~4990/5000` from `gh.sh status`

## Rotation

Fine-grained PATs expire. Set a calendar reminder before expiry, or move to a GitHub App for long-lived auth.

## Rate limits

| Tier           | Auth   | Limit        |
|----------------|--------|--------------|
| Core REST      | none   | 60 / hour    |
| Core REST      | token  | 5000 / hour  |
| Search         | token  | 30 / minute  |
| Actions        | token  | 1000 / hour  |

`./scripts/gh.sh status` shows current remaining + reset time.