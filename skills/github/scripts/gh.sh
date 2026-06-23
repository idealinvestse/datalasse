#!/usr/bin/env bash
# gh.sh — minimal GitHub CLI wrapper (no gh CLI required)
# Usage: ./gh.sh <subcommand> [args]
# Subcommands: status, repo, issue, pr, release, workflow, search

set -euo pipefail

TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
API="https://api.github.com"

die() { echo "✗ $*" >&2; exit 1; }
need_token() {
  [ -n "$TOKEN" ] || die "GITHUB_TOKEN (or GH_TOKEN) not set. Required for this operation."
}

# --- low-level API call ---
# Usage: api <METHOD> <PATH> [JSON_BODY]
api() {
  local method="$1"; shift
  local path="$1"; shift
  local data="${1:-}"
  local args=(-sS -X "$method"
              -H "Accept: application/vnd.github+json"
              -H "X-GitHub-Api-Version: 2022-11-28")
  [ -n "$TOKEN" ] && args+=(-H "Authorization: Bearer $TOKEN")
  [ -n "$data" ]  && args+=(-H "Content-Type: application/json" -d "$data")
  curl "${args[@]}" "$API$path"
}

# --- status / auth ---
cmd_status() {
  if [ -n "$TOKEN" ]; then
    local user scope
    user=$(api GET "/user"  | jq -r '.login // "?"')
    scope=$(api GET "/user" | jq -r '"type=\(.type)"')
    echo "✓ Authenticated as: $user ($scope)"
  else
    echo "○ No token (read-only, 60 req/h IP-limited)"
  fi
  api GET "/rate_limit" | jq -r '
    "Rate limit: \(.resources.core.remaining)/\(.resources.core.limit) (resets \(.resources.core.reset | todate))",
    "  search: \(.resources.search.remaining)/\(.resources.search.limit)",
    "  actions: \(.resources.actions.remaining)/\(.resources.actions.limit)"
  '
}

# --- repo ---
cmd_repo() {
  local action="${1:-list}"; shift || true
  case "$action" in
    list)
      local user="${1:-}"
      if [ -n "$user" ]; then
        api GET "/users/$user/repos?per_page=100&sort=updated" \
          | jq '.[] | {name, full_name, private, html_url, description}'
      else
        need_token
        api GET "/user/repos?per_page=100&sort=updated" \
          | jq '.[] | {name, full_name, private, html_url, description}'
      fi
      ;;
    view)
      local repo="${1:?repo OWNER/NAME required}"; shift
      api GET "/repos/$repo" \
        | jq '{name, full_name, private, html_url, description, default_branch, stargazers_count, forks_count, open_issues_count}'
      ;;
    create)
      local name="${1:?repo name required}"; shift
      local priv="false" desc="" org=""
      while [ $# -gt 0 ]; do
        case "$1" in
          --private) priv="true"; shift ;;
          --public)  priv="false"; shift ;;
          --description) desc="$2"; shift 2 ;;
          --org) org="$2"; shift 2 ;;
          *) die "repo create: unknown flag: $1" ;;
        esac
      done
      need_token
      local body
      body=$(jq -n --arg n "$name" --arg d "$desc" --argjson p "$priv" \
        '{name:$n, description:$d, private:$p}')
      if [ -n "$org" ]; then
        api POST "/orgs/$org/repos" "$body" | jq '{name, full_name, html_url}'
      else
        api POST "/user/repos" "$body" | jq '{name, full_name, html_url}'
      fi
      ;;
    clone)
      local repo="${1:?repo OWNER/NAME required}"; shift
      git clone "https://github.com/$repo.git" "$@"
      ;;
    fork)
      local repo="${1:?repo OWNER/NAME required}"
      need_token
      api POST "/repos/$repo/forks" "" | jq '{name, full_name, html_url}'
      ;;
    delete)
      local repo="${1:?repo OWNER/NAME required}"
      need_token
      [[ "${YES:-0}" == "1" ]] || { read -rp "Delete $repo? [y/N] " r; [[ "$r" =~ ^[Yy]$ ]] || exit 1; }
      api DELETE "/repos/$repo" >/dev/null && echo "✓ deleted $repo"
      ;;
    *) die "repo: unknown action: $action (list|view|create|clone|fork|delete)" ;;
  esac
}

# --- issue ---
cmd_issue() {
  local action="${1:-list}"; shift || true
  local repo="" state="open" limit="30"
  local ISSUE_TITLE="" ISSUE_BODY="" ISSUE_LABELS="" ISSUE_NUM=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --repo)   repo="$2"; shift 2 ;;
      --state)  state="$2"; shift 2 ;;
      --limit)  limit="$2"; shift 2 ;;
      --title)  ISSUE_TITLE="$2"; shift 2 ;;
      --body)   ISSUE_BODY="$2"; shift 2 ;;
      --label|--labels) ISSUE_LABELS="$2"; shift 2 ;;
      --number) ISSUE_NUM="$2"; shift 2 ;;
      --yes)    YES=1; shift ;;
      *) break ;;
    esac
  done
  [ -n "$repo" ] || die "--repo required"

  case "$action" in
    list)
      api GET "/repos/$repo/issues?state=$state&per_page=$limit" \
        | jq '.[] | select(.pull_request == null) | {number, title, state, user: .user.login, labels: [.labels[].name], updated_at}'
      ;;
    view)
      [ -n "$ISSUE_NUM" ] || die "--number required for view"
      api GET "/repos/$repo/issues/$ISSUE_NUM" \
        | jq '{number, title, state, body, user: .user.login, labels: [.labels[].name], created_at, updated_at}'
      ;;
    create)
      [ -n "$ISSUE_TITLE" ] || die "--title required for create"
      need_token
      local payload
      if [ -n "$ISSUE_LABELS" ]; then
        payload=$(jq -n --arg t "$ISSUE_TITLE" --arg b "${ISSUE_BODY:-}" --arg l "$ISSUE_LABELS" \
          '{title:$t, body:$b, labels: ($l|split(","))}')
      else
        payload=$(jq -n --arg t "$ISSUE_TITLE" --arg b "${ISSUE_BODY:-}" \
          '{title:$t, body:$b}')
      fi
      api POST "/repos/$repo/issues" "$payload" | jq '{number, title, html_url}'
      ;;
    close)
      [ -n "$ISSUE_NUM" ] || die "--number required for close"
      need_token
      api PATCH "/repos/$repo/issues/$ISSUE_NUM" '{"state":"closed"}' \
        | jq '{number, state, closed_at}'
      ;;
    comment)
      [ -n "$ISSUE_NUM" ] && [ -n "$ISSUE_BODY" ] || die "--number and --body required for comment"
      need_token
      local payload=$(jq -n --arg b "$ISSUE_BODY" '{body:$b}')
      api POST "/repos/$repo/issues/$ISSUE_NUM/comments" "$payload" \
        | jq '{id, html_url}'
      ;;
    *) die "issue: unknown action: $action (list|view|create|close|comment)" ;;
  esac
}

# --- pr ---
cmd_pr() {
  local action="${1:-list}"; shift || true
  local repo="" state="open" limit="30"
  local PR_TITLE="" PR_BODY="" PR_HEAD="" PR_BASE="" PR_NUM="" PR_METHOD=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --repo)   repo="$2"; shift 2 ;;
      --state)  state="$2"; shift 2 ;;
      --limit)  limit="$2"; shift 2 ;;
      --title)  PR_TITLE="$2"; shift 2 ;;
      --body)   PR_BODY="$2"; shift 2 ;;
      --head)   PR_HEAD="$2"; shift 2 ;;
      --base)   PR_BASE="$2"; shift 2 ;;
      --number) PR_NUM="$2"; shift 2 ;;
      --method) PR_METHOD="$2"; shift 2 ;;
      --yes)    YES=1; shift ;;
      *) break ;;
    esac
  done
  [ -n "$repo" ] || die "--repo required"

  case "$action" in
    list)
      api GET "/repos/$repo/pulls?state=$state&per_page=$limit" \
        | jq '.[] | {number, title, state, head: .head.ref, base: .base.ref, user: .user.login, draft, html_url}'
      ;;
    view)
      [ -n "$PR_NUM" ] || die "--number required for view"
      api GET "/repos/$repo/pulls/$PR_NUM" \
        | jq '{number, title, state, head: .head.ref, base: .base.ref, mergeable, draft, user: .user.login, html_url, body}'
      ;;
    create)
      [ -n "$PR_HEAD" ] && [ -n "$PR_BASE" ] && [ -n "$PR_TITLE" ] \
        || die "--head --base --title required for create"
      need_token
      local payload
      payload=$(jq -n --arg t "$PR_TITLE" --arg b "${PR_BODY:-}" \
                     --arg h "$PR_HEAD" --arg b2 "$PR_BASE" \
        '{title:$t, body:$b, head:$h, base:$b2}')
      api POST "/repos/$repo/pulls" "$payload" | jq '{number, title, html_url}'
      ;;
    merge)
      [ -n "$PR_NUM" ] || die "--number required for merge"
      need_token
      local method="${PR_METHOD:-merge}"
      [[ "${YES:-0}" == "1" ]] \
        || { read -rp "Merge PR #$PR_NUM with '$method'? [y/N] " r; [[ "$r" =~ ^[Yy]$ ]] || exit 1; }
      local payload=$(jq -n --arg m "$method" '{merge_method:$m}')
      api PUT "/repos/$repo/pulls/$PR_NUM/merge" "$payload" \
        | jq '{merged, message, sha}'
      ;;
    *) die "pr: unknown action: $action (list|view|create|merge)" ;;
  esac
}

# --- release ---
cmd_release() {
  local action="${1:-list}"; shift || true
  local repo="" limit="20"
  local REL_TAG="" REL_NAME="" REL_NOTES="" REL_GEN=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --repo)   repo="$2"; shift 2 ;;
      --limit)  limit="$2"; shift 2 ;;
      --tag)    REL_TAG="$2"; shift 2 ;;
      --name)   REL_NAME="$2"; shift 2 ;;
      --notes)  REL_NOTES="$2"; shift 2 ;;
      --generate-notes) REL_GEN=1; shift ;;
      --yes)    YES=1; shift ;;
      *) break ;;
    esac
  done
  [ -n "$repo" ] || die "--repo required"

  case "$action" in
    list)
      api GET "/repos/$repo/releases?per_page=$limit" \
        | jq '.[] | {tag_name, name, published_at, prerelease, draft, html_url}'
      ;;
    create)
      [ -n "$REL_TAG" ] || die "--tag required for create"
      need_token
      local payload
      if [ "$REL_GEN" = "1" ]; then
        payload=$(jq -n --arg t "$REL_TAG" --arg n "${REL_NAME:-$REL_TAG}" \
          '{tag_name:$t, name:$n, generate_release_notes:true}')
      else
        payload=$(jq -n --arg t "$REL_TAG" --arg n "${REL_NAME:-$REL_TAG}" \
                       --arg b "${REL_NOTES:-}" \
          '{tag_name:$t, name:$n, body:$b}')
      fi
      api POST "/repos/$repo/releases" "$payload" \
        | jq '{tag_name, name, html_url}'
      ;;
    delete)
      [ -n "$REL_TAG" ] || die "--tag required for delete"
      need_token
      local id
      id=$(api GET "/repos/$repo/releases/tags/$REL_TAG" | jq -r '.id')
      [[ "${YES:-0}" == "1" ]] \
        || { read -rp "Delete release $REL_TAG? [y/N] " r; [[ "$r" =~ ^[Yy]$ ]] || exit 1; }
      api DELETE "/repos/$repo/releases/$id" >/dev/null && echo "✓ deleted $REL_TAG"
      ;;
    *) die "release: unknown action: $action (list|create|delete)" ;;
  esac
}

# --- workflow ---
cmd_workflow() {
  local action="${1:-list}"; shift || true
  local repo="" branch=""
  local WF_NAME="" WF_RUN=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --repo)     repo="$2"; shift 2 ;;
      --branch)   branch="$2"; shift 2 ;;
      --workflow) WF_NAME="$2"; shift 2 ;;
      --run)      WF_RUN="$2"; shift 2 ;;
      *) break ;;
    esac
  done
  [ -n "$repo" ] || die "--repo required"

  case "$action" in
    list)
      api GET "/repos/$repo/actions/workflows" \
        | jq '.workflows[] | {id, name, path, state, html_url}'
      ;;
    runs)
      local path="/repos/$repo/actions/runs?per_page=20"
      [ -n "$WF_NAME" ] && path="/repos/$repo/actions/workflows/$WF_NAME/runs?per_page=20"
      api GET "$path" \
        | jq '.workflow_runs[] | {id, name, status, conclusion, event, head_branch, created_at, html_url}'
      ;;
    run)
      [ -n "$WF_NAME" ] || die "--workflow <name.yml> required for run"
      need_token
      local payload="{}"
      [ -n "$branch" ] && payload=$(jq -n --arg b "$branch" '{ref:$b}')
      api POST "/repos/$repo/actions/workflows/$WF_NAME/dispatches" "$payload" \
        >/dev/null && echo "✓ triggered $WF_NAME (branch: ${branch:-default})"
      ;;
    logs)
      [ -n "$WF_RUN" ] || die "--run <id> required for logs"
      # Returns a 302 redirect to a signed log URL — surface the redirect target
      curl -sS -I \
        -H "Accept: application/vnd.github+json" \
        ${TOKEN:+-H "Authorization: Bearer $TOKEN"} \
        "$API/repos/$repo/actions/runs/$WF_RUN/logs" \
        | awk 'tolower($1) == "location:" { print $2 }'
      ;;
    *) die "workflow: unknown action: $action (list|runs|run|logs)" ;;
  esac
}

# --- search ---
cmd_search() {
  local type="${1:?search type required: repos|issues|code|prs}"; shift
  local query="$*"
  [ -n "$query" ] || die "search query required"
  local encoded
  encoded=$(jq -rn --arg q "$query" '$q|@uri')
  case "$type" in
    repos)  api GET "/search/repositories?q=$encoded" \
              | jq '.items[] | {full_name, description, stargazers_count, html_url}' ;;
    issues) api GET "/search/issues?q=$encoded" \
              | jq '.items[] | select(.pull_request == null) | {number, title, state, repository: .repository_url, html_url}' ;;
    prs)    api GET "/search/issues?q=$encoded+is:pr" \
              | jq '.items[] | {number, title, state, repository: .repository_url, html_url}' ;;
    code)   api GET "/search/code?q=$encoded" \
              | jq '.items[] | {name, path, repository: .repository.full_name, html_url}' ;;
    *) die "search: unknown type: $type (repos|issues|code|prs)" ;;
  esac
}

# --- main ---
usage() {
  cat <<EOF
gh.sh — minimal GitHub wrapper (curl + jq)

Usage: ./gh.sh <subcommand> [args]

Subcommands:
  status                          Auth check + rate limit
  repo <action> --repo ORG/NAME   list|view|create|clone|fork|delete
  issue <action> --repo ORG/NAME  list|view|create|close|comment
  pr <action> --repo ORG/NAME     list|view|create|merge
  release <action> --repo ORG/NAME list|create|delete
  workflow <action> --repo ORG/NAME list|runs|run|logs
  search <type> <query>           repos|issues|code|prs

Env: GITHUB_TOKEN or GH_TOKEN (required for write ops)

Examples:
  ./gh.sh status
  ./gh.sh repo list --user oscar
  ./gh.sh issue list --repo oscar/foo --state open
  ./gh.sh pr create --repo oscar/foo --head feat --base main --title "..." --body "..."
EOF
}

SUBCMD="${1:-}"; shift || true
case "$SUBCMD" in
  status)              cmd_status "$@" ;;
  repo)                cmd_repo "$@" ;;
  issue)               cmd_issue "$@" ;;
  pr)                  cmd_pr "$@" ;;
  release)             cmd_release "$@" ;;
  workflow)            cmd_workflow "$@" ;;
  search)              cmd_search "$@" ;;
  help|--help|-h|"")   usage ;;
  *)                   die "unknown subcommand: $SUBCMD. Run: $0 help" ;;
esac