# Sub-Agent Task Definition: Quick Factual Lookup (Serper)

## Purpose
Fast, low-cost verification of current external facts: pricing, limits, docs status, availability, or simple "is X still true in 2026?" questions. Use this before the main Grok planner when the task touches an external service whose current state matters.

## When to Spawn
- Pricing tables or free/paid tiers
- Rate limits, quotas, or deprecation notices
- "Does this service still exist / support feature Y?"
- Basic comparison of two similar APIs (price vs limits)
- Confirmation that a URL or endpoint is live

## Example Task (copy-paste ready)

**Model:** `openrouter/x-ai/grok-4.3` (or cheapest reliable model)

**Task prompt:**
```
You are a precise research sub-agent. Perform a quick factual lookup using web search.

User need: <paste concise user request, e.g. "current pricing and limits for serper.dev Google SERP API June 2026">

Instructions:
1. Use web_search or web_fetch to find the official pricing page or docs.
2. Extract ONLY: free tier details, paid plan prices, rate limits, any recent changes or deprecations.
3. Return a clean bullet list with source URLs.
4. If the service appears deprecated or the page is gone, state that clearly.
5. Stop after 1–2 high-quality sources — do not over-research.
```

**Tools allowed:** `["web_search", "web_fetch"]`

**Expected output length:** 150–300 tokens (concise bullets + sources)

**Timeout:** 30–60 seconds

## Integration with Grok-Build
- Results are summarized and inserted into the `## Research Findings` section of the main plan prompt.
- The orchestrator runs this sub-agent in parallel with the deep Exa sub-agent when both are relevant.
- Final Telegram plan summary includes the key facts + source links so the user sees the evidence.

## Cost & Performance
- Typically 1–3 tool calls
- Very low token cost
- High reliability for factual questions

This sub-agent pattern eliminates the most common weakness of the old grok-build flow: making plans based on stale internal knowledge about external services.