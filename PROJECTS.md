# PROJECTS.md — Active Project Repos

> **Index of git repos Moss is actively developing.**
> Updated: 2026-06-23 21:48 UTCali
>
> | Project | Repo path | Workspace link | Branch | Status | Primary docs | Workspace bridge |
> |---------|-----------|----------------|--------|--------|--------------|------------------|
> | Automatisk-sentimentanalys | `~/projects/Automatisk-sentimentanalys` | `projects/sentimentanalys/` (symlink) | `main` | Phase 6 complete, Phase 5+ active | `docs/LLM_AGENT_GUIDE.md` + `docs/GROK_BUILD_PLAN_FAS1-3.md` | `memory/projects/sentimentanalys/CONTEXT.md` |
> | mossfund | `~/.openclaw/workspace/projects/mossfund/` | (native) | n/a | Research phase complete, execution on hold | (internal) | `memory/projects/mossfund/...` |

## Conventions for adding a new project

1. Clone to `~/projects/<name>` (canonical working dir)
2. Symlink: `ln -sfn ~/projects/<name> ~/.openclaw/workspace/projects/<name>`
3. Create `~/.openclaw/workspace/memory/projects/<name>/{research,decisions,findings}/`
4. Write `~/.openclaw/workspace/memory/projects/<name>/CONTEXT.md` — bridge file with:
   - Path to repo + branch conventions
   - Path to repo's own AGENTS.md / LLM_AGENT_GUIDE.md
   - Active plan reference (`memory/grok-plans/<date>-<project>-<phase>.md`)
   - Workflow knobs (research dispatcher tier defaults, model overrides, secrets)
5. Add row to the table above.
6. Update `MEMORY.md` "Workspace-struktur" + "Aktuella projekt" sections.

## Symlink target vs workspace-native

- **Canonical git working dir** = `~/projects/<name>` (always). This is what `git` commands run on, what `gh` PRs from, etc.
- **Workspace link** = `~/.openclaw/workspace/projects/<name>` (symlink). This is what OpenClaw tools (read/edit/exec) see. Lets MEMORY/INDEX-style reasoning find the project.
- **Workspace-native** (e.g. mossfund/) = the repo lives directly under workspace and shares its gitignore. Use only for Moss-private tooling, never for code that goes to GitHub.