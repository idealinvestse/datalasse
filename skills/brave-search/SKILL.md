---
name: "brave-search"
description: "Primary web search provider via Brave Search API. Use when web_search is called from research subagents, deep dives, or any research workflow."
---

# Brave Search (updated 2026-06-23)

**Status:** **Primary** web_search provider for all research workflows.

The gateway uses `@openclaw/brave-plugin` (v2026.6.5, npm-installed) with
`BRAVE_API_KEY` resolved from `~/.openclaw/openclaw.json` env block. Provider
config lives at `plugins.entries.brave.config.webSearch` and `tools.web.search.provider = "brave"`.

## Why Brave (not parallel-free)

- Independent quota (Brave's $5/month free credit → ~1,000 queries/month free)
- Better rate limits than Parallel free MCP
- Structured results with snippets, country/language/freshness filters
- LLM Context mode available for grounded queries (`webSearch.mode = "llm-context"`)

## Where it's wired

- **Main session web_search** → Brave (primary)
- **Research subagents** (deep-research, research-goal, research-watch, research-feedback, research-refresh, research-prioritize, research-discover) → inherit `web_search` from session → Brave
- **grok-build research-dispatcher** → uses subagents → Brave
- **Parallel (free)** plugin remains enabled as fallback for non-rate-limit-sensitive flows

## Configuration

```json5
{
  plugins: {
    entries: {
      brave: {
        enabled: true,
        config: {
          webSearch: {
            mode: "web",          // or "llm-context"
          },
        },
      },
    },
  },
  tools: {
    web: {
      search: {
        provider: "brave",
        enabled: true,
        maxResults: 7,
        timeoutSeconds: 30,
      },
    },
  },
}
```

`BRAVE_API_KEY` is resolved from `env.vars.BRAVE_API_KEY` in `openclaw.json`.

## Switching back to fallback

If Brave quota runs out, unset `tools.web.search.provider` to enter auto-detect
mode (the next available provider key wins by precedence), or set it back to
`"parallel-free"`.

## Notes

- Brave Search plan: $5 per 1,000 requests, with $5/month free credit (renewing)
- Results cached 15 min by default
- `brave.http` diagnostics flag available for troubleshooting (no API key in logs)
- Set usage limit in Brave dashboard to avoid surprise charges: https://api-dashboard.search.brave.com

**Last updated:** 2026-06-23 (promoted to primary provider)