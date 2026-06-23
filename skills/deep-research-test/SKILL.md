---
name: deep-research-test
description: Orchestrator for testing + selecting models and APIs for deep research workflows. Generates a recommended config based on what's available and validated.
---

# deep-research-test

Orchestrator that tests and recommends the best model routing + API stack for deep research workflows.

## When to use

- Choosing which model to use for which phase of a research task
- Checking which APIs (Brave, Exa, Tavily, etc.) are configured and available
- Generating an up-to-date config recommendation
- Auditing what's actually accessible on this OpenRouter tenant vs. what's documented

## Usage

```bash
# Check model status
bin/deep-research-test models

# Check API keys + status
bin/deep-research-test apis

# Generate config report
bin/deep-research-test report

# Full run (models + apis + report)
bin/deep-research-test all
```

## Outputs

- `~/.openclaw/workspace/skills/deep-research-test/CONFIG.md` — current best setup
- `/tmp/deep-research-test-results.json` — machine-readable results (when run with live tests)

## Key files

- `bin/deep-research-test` — the orchestrator script
- `CONFIG.md` — generated config recommendation
- `references/PLANNING-PROMPT.md` — source prompt (with caveats)

## Validation status (2026-06-18)

- **5 models validated as accessible** (2026-06-19 update: grok-4.1-fast → grok-4.3): grok-4.3, deepseek-v4-flash/pro, minimax-m3, qwen3.6-35b-a3b
- **11 models from PLANNING-PROMPT validated as INVALID** (fall back to qwen, no multi-model deliberation)
- **7 search/data APIs researched** (Exa, Tavily, Perplexity, OpenAI Deep Research, SerpAPI, Brave, Firecrawl)
- **Recommendation:** Exa (free 20k/mo) + Tavily (extract) + SearXNG (self-hosted backup) = €5-35/mo
