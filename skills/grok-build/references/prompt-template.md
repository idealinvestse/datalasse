/plan

## Goal

<One sentence: what the user wants done>

## Research Findings (MANDATORY for external APIs, pricing, new tools, best practices)

- Quick facts (docs, pricing, current status): <summary from Serper sub-agent or direct search>
- Deep technical context (adoption, patterns, pitfalls 2026): <summary from Exa sub-agent>
- Sources: <key URLs or task IDs>
- Gaps / unknowns: <what still needs verification>

If no external research needed (pure internal code change), state: "No external research required — internal refactor only."

## Context

- Workdir: <absolute path>
- Zone: <green | yellow | red>
- Requester channel: <telegram | webchat | ...>
- Related files: <paths if known>

## Requirements

- <bullet list derived from user message + informed by research>

## Out of scope

- Secrets, tokens, credentials
- Changes outside the stated zone without approval
- Using deprecated or unverified external services (flag any from research)

## Verification

- <how to confirm success: commands, file checks, openclaw config validate, external API test calls, etc.>

## Rules (planning phase)

- PLANNING ONLY: explore, read, search, write plan.md.
- Do NOT modify source files in this phase (only plan.md).
- When the plan is ready, summarize it clearly and STOP.
- Do not implement until a separate execution phase is triggered.
- Always cite research sources in the final plan summary sent to Telegram.

---

**Research Augmentation Rule:** Before spawning the main Grok planner, the orchestrator MUST run parallel sub-agents for research when the task touches external services. Results are injected here.