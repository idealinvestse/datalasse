#!/usr/bin/env bash
# Grok Build orchestrator: plan phase -> Telegram approval -> execute phase.
# Usage:
#   run-grok-task.sh plan <workdir> <prompt-file> [channel] [target]
#   run-grok-task.sh execute <workdir> [channel] [target]
#
# Harmonized lightly (2026-06 review/refactor pass): style/comments aligned with
# patterns from .grok/bundled skills (e.g. memory.py robustness). See grok-build/SKILL.md.
set -euo pipefail

GROK="${GROK_BIN:-/root/.grok/bin/grok}"
MODEL="${GROK_MODEL:-grok-build}"
PENDING_FILE="${GROK_PENDING_FILE:-/root/.openclaw/workspace/memory/grok-pending.json}"
GROK_SESSIONS="${GROK_SESSIONS_DIR:-/root/.grok/sessions}"

encode_cwd() {
  python3 - "$1" <<'PY'
import sys
from urllib.parse import quote
print(quote(sys.argv[1], safe=""))
PY
}

session_dir_for_cwd() {
  local workdir="$1"
  local encoded
  encoded="$(encode_cwd "$workdir")"
  echo "${GROK_SESSIONS}/${encoded}"
}

find_latest_plan() {
  local workdir="$1"
  local sdir
  sdir="$(session_dir_for_cwd "$workdir")"

  # Collect candidate plan.md paths from BOTH the session directory and the
  # workdir itself. Newer Grok Build models (Composer 2.5 Fast) sometimes
  # write plan.md to the workdir instead of the session subdirectory; we
  # therefore search both and return whichever is newest by mtime.
  local candidates=()

  if [[ -d "$sdir" ]]; then
    while IFS= read -r f; do
      [[ -n "$f" ]] && candidates+=("$f")
    done < <(find "$sdir" -name plan.md -type f 2>/dev/null)
  fi

  if [[ -f "$workdir/plan.md" ]]; then
    candidates+=("$workdir/plan.md")
  fi

  if (( ${#candidates[@]} == 0 )); then
    return 1
  fi

  # Pick the newest by mtime (seconds since epoch, robust on Linux/macOS).
  local newest="${candidates[0]}"
  local newest_mtime
  newest_mtime="$(stat -c %Y "$newest" 2>/dev/null || stat -f %m "$newest" 2>/dev/null || echo 0)"
  local f mtime
  for f in "${candidates[@]}"; do
    mtime="$(stat -c %Y "$f" 2>/dev/null || stat -f %m "$f" 2>/dev/null || echo 0)"
    if (( mtime > newest_mtime )); then
      newest="$f"
      newest_mtime="$mtime"
    fi
  done

  printf '%s\n' "$newest"
}

find_latest_session_id() {
  local workdir="$1"
  local sdir
  sdir="$(session_dir_for_cwd "$workdir")"
  if [[ ! -d "$sdir" ]]; then
    return 1
  fi
  find "$sdir" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %f\n' 2>/dev/null \
    | sort -n | tail -1 | cut -d' ' -f2-
}

summarize_plan() {
  local plan_file="$1"
  if [[ ! -f "$plan_file" ]]; then
    echo "(No plan.md found yet)"
    return
  fi
  python3 - "$plan_file" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").strip()
lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
preview = "\n".join(lines[:40])
if len(lines) > 40:
    preview += "\n...(truncated)"
print(preview)
PY
}

write_pending() {
  local workdir="$1" plan_path="$2" session_id="$3" channel="$4" target="$5" task_id="$6"
  mkdir -p "$(dirname "$PENDING_FILE")"
  python3 - "$PENDING_FILE" "$workdir" "$plan_path" "$session_id" "$channel" "$target" "$task_id" <<'PY'
import json, sys, datetime
path, workdir, plan_path, session_id, channel, target, task_id = sys.argv[1:8]
data = {
    "taskId": task_id,
    "workdir": workdir,
    "planPath": plan_path,
    "sessionId": session_id,
    "channel": channel,
    "target": target,
    "phase": "awaiting_approval",
    "createdAt": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY
}

read_pending_field() {
  local field="$1"
  python3 - "$PENDING_FILE" "$field" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
print(data.get(sys.argv[2], ""))
PY
}

clear_pending() {
  rm -f "$PENDING_FILE"
}

notify() {
  local channel="$1" target="$2" message="$3"
  if command -v openclaw >/dev/null 2>&1; then
    openclaw message send --channel "$channel" --target "$target" --message "$message" || true
  fi
}

run_plan_phase() {
  local workdir="$1" prompt_file="$2" channel="${3:-telegram}" target="${4:-438805461}"
  if [[ ! -x "$GROK" ]]; then
    echo "error: grok not found at $GROK" >&2
    exit 127
  fi
  if [[ ! -f "$prompt_file" ]]; then
    echo "error: prompt file not found: $prompt_file" >&2
    exit 1
  fi

  # === Research dispatcher integration (improvement #3) ===
  # Automatically detect if this plan prompt needs external research and report cache status.
  # This runs transparently before the actual Grok planner is invoked.
  local DISPATCHER="${BASH_SOURCE%/*}/research-dispatcher.sh"
  if [[ -f "$DISPATCHER" ]]; then
    # shellcheck disable=SC1090
    if source "$DISPATCHER" 2>/dev/null; then
      local prompt_text
      prompt_text=$(cat "$prompt_file" 2>/dev/null || echo "")
      if [[ -n "$prompt_text" ]] && needs_research "$prompt_text"; then
        local decision
        decision=$(classify_research_need "$prompt_text" 2>/dev/null || echo "MEDIUM")
        echo "== research-dispatcher: $decision signal detected =="
        explain_research_decision "$prompt_text" || true

        local key
        key=$(make_cache_key "$prompt_text")
        if has_fresh_cache "$key" >/dev/null 2>&1; then
          echo "Cache status: FRESH (will be used)"
        else
          echo "Cache status: MISS (research sub-agents recommended before execute)"
        fi
        echo ""
      fi
    fi
  fi
  # === end research dispatcher hook ===

  mkdir -p "$workdir"
  local task_id
  task_id="$(date +%s)-$$"

  echo "== grok-build plan phase =="
  echo "workdir: $workdir"
  echo "taskId: $task_id"

  cd "$workdir"
  "$GROK" -p "$(cat "$prompt_file")" \
    --cwd "$workdir" \
    --model "$MODEL" \
    --output-format plain \
    --max-turns 25

  local plan_path session_id
  plan_path="$(find_latest_plan "$workdir" || true)"
  session_id="$(find_latest_session_id "$workdir" || true)"

  if [[ -z "$plan_path" ]]; then
    echo "warning: plan.md not found under $(session_dir_for_cwd "$workdir")" >&2
  fi

  write_pending "$workdir" "${plan_path:-}" "${session_id:-}" "$channel" "$target" "$task_id"

  echo ""
  echo "== PLAN SUMMARY (post in Telegram, wait for OK) =="
  if [[ -n "$plan_path" ]]; then
    echo "plan: $plan_path"
    summarize_plan "$plan_path"
  else
    echo "(Grok finished but no plan.md was written — review process log)"
  fi
  echo ""
  echo "Pending state: $PENDING_FILE"
  echo "Next: after owner replies ja/kör/ok, run:"
  echo "  {baseDir}/scripts/run-grok-task.sh execute $workdir $channel $target"
}

run_execute_phase() {
  local workdir="$1" channel="${2:-telegram}" target="${3:-438805461}"
  if [[ ! -f "$PENDING_FILE" ]]; then
    echo "error: no pending task at $PENDING_FILE — run plan phase first" >&2
    exit 1
  fi

  local pending_workdir plan_path
  pending_workdir="$(read_pending_field workdir)"
  plan_path="$(read_pending_field planPath)"

  if [[ "$pending_workdir" != "$workdir" ]]; then
    echo "warning: pending workdir ($pending_workdir) differs from arg ($workdir)" >&2
  fi

  local execute_prompt
  execute_prompt="$(mktemp -t openclaw-grok-execute.XXXXXX)"
  cat >"$execute_prompt" <<EOF
Plan approved by owner. Execute the approved plan now.

Plan file: ${plan_path:-plan.md in session directory}
Workdir: $workdir

Instructions:
1. Read and follow plan.md exactly.
2. Implement all planned changes.
3. Run the verification steps from the plan.
4. When finished, send exactly one message:
   openclaw message send --channel ${channel} --target '${target}' --message '<brief result summary>'
5. Do not use heartbeat or system events for completion.
EOF

  echo "== grok-build execute phase =="
  echo "workdir: $workdir"

  cd "$workdir"
  local output
  if ! output="$("$GROK" -p "$(cat "$execute_prompt")" \
    --continue \
    --cwd "$workdir" \
    --model "$MODEL" \
    --always-approve \
    --check \
    --output-format plain 2>&1)"; then
    notify "$channel" "$target" "Grok Build failed during execute phase. Check gateway logs."
    echo "$output"
    exit 1
  fi

  echo "$output"
  clear_pending
  echo ""
  echo "Execute phase complete. Pending state cleared."
}

usage() {
  echo "Usage: $0 plan <workdir> <prompt-file> [channel] [target]" >&2
  echo "       $0 execute <workdir> [channel] [target]" >&2
  exit 1
}

main() {
  local cmd="${1:-}"
  shift || usage
  case "$cmd" in
    plan)
      [[ $# -ge 2 ]] || usage
      run_plan_phase "$1" "$2" "${3:-telegram}" "${4:-438805461}"
      ;;
    execute)
      [[ $# -ge 1 ]] || usage
      run_execute_phase "$1" "${2:-telegram}" "${3:-438805461}"
      ;;
    *)
      usage
      ;;
  esac
}

main "$@"