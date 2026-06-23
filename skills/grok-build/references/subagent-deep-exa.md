# Sub-Agent Task Definition: Deep Technical Context (Exa)

## Purpose
Deep, high-value synthesis on complex external topics: adoption patterns, real-world usage, pitfalls, integration architecture, pricing psychology, ecosystem comparisons, or "how people actually solved X in 2026". Use this when the task requires strategic or architectural decisions, not just facts.

## When to Spawn
- MCP / x402 / agent payment architecture decisions
- Marketplace or monetization strategy (Agensi, skill pricing, MCP servers)
- "Best current pattern for Y" or multi-option comparisons
- Security/compliance research with real examples
- New tool or protocol viability (is this mature enough? what are the failure modes?)
- Research-heavy features where internal knowledge is insufficient

## Example Task (copy-paste ready)

**Model:** `openrouter/x-ai/grok-4.3` (or a strong reasoning model)

**Task prompt:**
```
You are a deep research sub-agent using Exa. Perform a thorough, source-backed synthesis.

User need: <paste user request, e.g. "MCP server monetization models that actually work in 2026, including x402 integration">

Instructions:
1. Use exa-research or exa-search with a clear research goal.
2. Focus on: real usage examples, pricing that converts, successful platforms, common failure modes, recommended architecture patterns, and 2026-specific context.
3. Synthesize into 8–12 actionable insights. Include source URLs or Exa task IDs for every major claim.
4. Explicitly flag any deprecations, hype vs reality gaps, or "infrastructure exists but demand does not" situations.
5. Prioritize primary sources and recent data (2025–2026).
```

**Tools allowed:** `["exa-research", "exa-search", "web_fetch"]`

**Expected output length:** 800–2000 tokens (structured synthesis + sources)

**Timeout:** 2–6 minutes (long-running research task)

## Integration with Grok-Build
- The orchestrator spawns this in parallel with the quick Serper sub-agent when the task has both factual and strategic dimensions.
- Results populate the `## Research Findings` block in the main plan prompt.
- The final Telegram plan summary includes the synthesized insights + citations so the approver sees the depth of evidence.

## Cost & Performance
- Higher token usage but dramatically better plan quality for non-trivial external integrations.
- Worth the cost when the alternative is an outdated or naive plan.

## Example Real-World Use (Mossfund context)
- Task: "Add x402 billing to an MCP server skill"
- Quick Serper: "Confirm current x402 volume and facilitators (June 2026)"
- Deep Exa: "Analyze which MCP monetization patterns are actually generating revenue and how x402 is typically integrated"
- Combined result: A plan that is both factually current and architecturally sound.

This sub-agent closes the "external reality gap" that previously caused grok-build plans to recommend approaches that were already outdated or suboptimal in the live ecosystem.