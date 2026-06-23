#!/usr/bin/env bash
# Backward-compatible wrapper around run-grok-task.sh.
# Usage: spawn-grok-worker.sh <workdir> <prompt-file> [channel] [target]
# If grok-pending.json exists -> execute phase; else -> plan phase.
#
# Light harmonization note (2026-06): delegates cleanly; see run-grok-task.sh header.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PENDING="${GROK_PENDING_FILE:-/root/.openclaw/workspace/memory/grok-pending.json}"

WORKDIR="${1:?workdir required}"
PROMPT_FILE="${2:?prompt file required}"
CHANNEL="${3:-telegram}"
TARGET="${4:-438805461}"

if [[ -f "$PENDING" ]]; then
  exec "$SCRIPT_DIR/run-grok-task.sh" execute "$WORKDIR" "$CHANNEL" "$TARGET"
else
  exec "$SCRIPT_DIR/run-grok-task.sh" plan "$WORKDIR" "$PROMPT_FILE" "$CHANNEL" "$TARGET"
fi