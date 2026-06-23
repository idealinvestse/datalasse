---
name: "brave-search"
description: "Web search via Brave Search API. Use for independent search quota when OpenClaw's default is blocked or rate-limited."
---

# Brave Search (updated 2026-06-22)

**Status:** Thin wrapper / alias around the built-in `web_search` tool.

This skill provides an independent search quota via Brave Search when the OpenClaw default provider is rate-limited or blocked.

## Usage

Use the standard `web_search` tool. When the default provider hits limits, this skill can be enabled as a fallback with its own Brave API quota.

## Gateway Integration

To enable as a first-class skill:

```json
{
  "skills": {
    "entries": {
      "brave-search": { "enabled": true }
    }
  }
}
```

## Notes

- No standalone `scripts/brave_search.sh` exists.
- The skill is intentionally lightweight — it reuses the existing `web_search` implementation.
- Smoke test: `web_search` with a simple query should succeed when this entry is enabled.

**Last updated:** 2026-06-22 (structural audit)
