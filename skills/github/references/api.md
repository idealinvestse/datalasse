# API Notes

Base: `https://api.github.com`
Version: `2022-11-28` (pinned in script headers)

## Endpoints used

| Resource   | Method | Path                                            |
|------------|--------|-------------------------------------------------|
| User       | GET    | `/user`                                         |
| Rate limit | GET    | `/rate_limit`                                   |
| Repo       | GET    | `/repos/{owner}/{repo}`                         |
| Repo       | POST   | `/user/repos`, `/orgs/{org}/repos`              |
| Repo       | DEL    | `/repos/{owner}/{repo}`                         |
| Repo       | POST   | `/repos/{owner}/{repo}/forks`                   |
| Issue      | GET    | `/repos/{owner}/{repo}/issues`                  |
| Issue      | POST   | `/repos/{owner}/{repo}/issues`                  |
| Issue      | PATCH  | `/repos/{owner}/{repo}/issues/{number}`         |
| Comment    | POST   | `/repos/{owner}/{repo}/issues/{number}/comments`|
| PR         | GET    | `/repos/{owner}/{repo}/pulls`                   |
| PR         | POST   | `/repos/{owner}/{repo}/pulls`                   |
| PR         | PUT    | `/repos/{owner}/{repo}/pulls/{number}/merge`    |
| Release    | GET    | `/repos/{owner}/{repo}/releases`                |
| Release    | POST   | `/repos/{owner}/{repo}/releases`                |
| Release    | DEL    | `/repos/{owner}/{repo}/releases/{id}`           |
| Workflow   | GET    | `/repos/{owner}/{repo}/actions/workflows`       |
| Workflow   | GET    | `/repos/{owner}/{repo}/actions/runs`            |
| Workflow   | POST   | `/repos/{owner}/{repo}/actions/workflows/{wf}/dispatches` |
| Search     | GET    | `/search/{repositories,issues,code}`            |

## Pagination

List endpoints accept `per_page` (max 100) and `page` (1-indexed).
Script uses `per_page=100` by default for repos, `30` for issues/PRs.
For deeper pagination, add `--page N` (not yet exposed — add if needed).

## Conditional requests

For polling without burning rate limit, pass `If-None-Match: <etag>`
from previous response. Not implemented yet — add if needed.

## Errors

- `401` — bad/expired token
- `403` — rate limit or insufficient scope
- `404` — wrong owner/repo, or no access
- `422` — validation error (read JSON body for details)
- `502/503` — retry with backoff (script doesn't, manual only)

The script prints raw JSON for non-2xx; check the `message` field.