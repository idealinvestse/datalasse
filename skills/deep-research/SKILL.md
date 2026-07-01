---
name: deep-research
description: Consolidated 6-stage deep research orchestrator (DECOMPOSE→SEARCH→DEEP→EXTRACT→SYNTHESIZE→VERIFY) plus goal management, watch, recipes, metrics, feedback, status and related tools.
---

# deep-research

The single home for the deep research skill ecosystem.

## Entry Points
- `bin/deep-research "your question" --depth=auto --budget=0.20` (recommended; uses shims)
- Direct: `skills/deep-research/bin/deep-research ...`

## Key Files
- `bin/deep-research` (shim) / `skills/deep-research/bin/deep-research` (implementation)
- `skills/deep-research/lib/research-state.sh` (shared state for goals/runs/plans)
- `skills/deep-research/lib/retry.sh`, `fallback.sh`
- All tools now co-located for cohesion

## Notes
- 6-stage pipeline unchanged.
- State in `memory/research/` + `~/.config/moss/research` (via lib) untouched.
- `bin/deep-research-test` and `skills/deep-research-test/` kept separate (model validator + roadmap).
- See original `bin/deep-research --help` and individual `--help`.
