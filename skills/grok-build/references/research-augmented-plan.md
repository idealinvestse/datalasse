# Research-Augmented Planning for Grok-Build

## Purpose
The standard grok-build plan phase is excellent at code structure and internal logic but historically lacks fresh external data (pricing, API status, current best practices, deprecations, competitor patterns). This leads to plans that are internally coherent but factually outdated.

This reference defines when and how to inject parallel research before the main Grok planner is called. The goal is **higher accuracy** for any task touching external services, while preserving the strict Telegram approval gate.

## When Research Is Mandatory (Yellow/Red triggers)
Run parallel research sub-agents **before** composing the main `/plan` prompt if the task involves any of these:

- External APIs, SDKs, or services (MCP, x402, Agensi, Stripe, OpenRouter, Serper, Exa, etc.)
- Pricing, quotas, or cost optimization
- Current adoption status, deprecations, or new features (2026 context)
- Security/compliance patterns or new regulatory requirements
- Tool comparisons or "best current X for Y" decisions
- Integration with rapidly moving ecosystems (agent skills marketplaces, payment rails, etc.)

**Rule of thumb:** If the task would benefit from knowing "what is true in June 2026", run research.

## Workflow (Orchestrator Level)
1. User request arrives → grok-build skill detects external relevance.
2. Orchestrator spawns **2 parallel sub-agents** (one quick, one deep) using `sessions_spawn`:
   - Quick factual lookup (Serper)
   - Deep technical synthesis (Exa)
3. Sub-agent results are collected and injected into the updated `prompt-template.md` under the new "Research Findings" section.
4. Main Grok planner is then spawned with the enriched prompt (plan phase only).
5. Plan summary is posted to Telegram **with research citations**.
6. User approves/rejects → execute phase (unchanged).

## Sub-Agent Patterns (Examples)

### Pattern A — Quick Doc / Pricing Lookup (Serper)
**Use when:** Need current pricing page, docs status, or "does X still exist" fact.
**Example task definition:**
```json
{
  "model": "openrouter/x-ai/grok-4.3",
  "task": "Search for the current pricing and key limits of serper.dev Google SERP API. Extract: free tier details, paid plans with prices, rate limits, and any 2026 changes. Return only bullet points with sources.",
  "tools": ["web_search", "web_fetch"]
}
```
**Characteristics:** Fast (5–15s), low cost, high precision for factual data.

### Pattern B — Deep Technical Context (Exa)
**Use when:** Need adoption patterns, pitfalls, real-world usage, comparisons, or "how people actually use X in 2026".
**Example task definition:**
```json
{
  "model": "openrouter/x-ai/grok-4.3",
  "task": "Deep research on MCP server monetization models and real usage in 2026. Focus on: platforms that succeeded, pricing that converts, integration with x402/USDC, common failures, and recommended architecture patterns. Synthesize into 8–12 actionable insights with sources.",
  "tools": ["exa-research", "web_fetch"]
}
```
**Characteristics:** Slower (1–5 min), higher value for complex decisions, produces synthesis instead of raw facts.

## Research Injection Points
- The updated `prompt-template.md` now contains an explicit `## Research Findings` block that the orchestrator must populate.
- All research summaries must include source URLs or task IDs so the final Telegram plan can cite them.
- If research reveals deprecations or major risks, the plan must explicitly flag them under "Out of scope" or "Risks".

## Benefits
- Plans become factually grounded (no more "use service X" when X deprecated last month).
- Cost-optimization suggestions are current (model routing, API choices).
- Integration decisions reflect real 2026 ecosystem state.
- Still 100% human approval gate before any code change.

## Future Extensions (Optional)
- Add a `research-cache.md` that stores recent findings to avoid duplicate calls within 48h.
- Allow user to pre-approve "always research external" for specific zones or keywords.
- Auto-detect when a task touches external services via keyword + tool-analysis heuristics.

This pattern turns grok-build from "great code planner" into "great, up-to-date, research-backed code planner" while keeping safety and control intact.