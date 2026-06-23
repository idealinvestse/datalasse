# Common Workflows

## Cut a release (commit → tag → release)

```bash
# In repo root
git tag v0.2.0 && git push --tags

./scripts/gh.sh release create v0.2.0 \
  --repo idealinvestse/moss-router \
  --generate-notes
```

## PR + auto-merge after CI

```bash
# Create PR
./scripts/gh.sh pr create \
  --repo idealinvestse/foo \
  --head fix-typo \
  --base main \
  --title "Fix typo in README" \
  --body "Closes #42"

# Poll CI
./scripts/gh.sh workflow runs --repo idealinvestse/foo --workflow ci.yml

# Merge when green
./scripts/gh.sh pr merge 123 --repo idealinvestse/foo --method squash --yes
```

## Issue triage batch

```bash
# List open bugs, oldest first
./scripts/gh.sh issue list --repo idealinvestse/foo --state open \
  | jq -r 'select(.labels | index("bug")) | "\(.number)\t\(.title)"'

# Close stale issues (older than 90 days) — review first, then:
./scripts/gh.sh issue list --repo idealinvestse/foo --state open \
  | jq -r 'select(.updated_at < (now - 7776000 | todate)) | .number' \
  | while read n; do
      ./scripts/gh.sh issue close "$n" --repo idealinvestse/foo --yes
    done
```

## Trigger Actions on demand

```bash
./scripts/gh.sh workflow run deploy.yml \
  --repo idealinvestse/foo \
  --branch main
```

## Find repos by topic

```bash
./scripts/gh.sh search repos "topic:moss language:typescript"
```

## Clone + open in editor

```bash
./scripts/gh.sh repo clone idealinvestse/moss-router ~/code/
cd ~/code/moss-router
code .  # or your editor
```

## Bulk label issues

```bash
./scripts/gh.sh issue list --repo idealinvestse/foo --limit 100 \
  | jq -r 'select(.labels | length == 0) | .number' \
  | while read n; do
      curl -sS -X POST \
        -H "Authorization: Bearer $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/idealinvestse/foo/issues/$n/labels" \
        -d '{"labels":["needs-triage"]}'
    done
```