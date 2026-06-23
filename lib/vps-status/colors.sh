#!/usr/bin/env bash
# lib/vps-status/colors.sh
# Color helpers for vps-status. Pure bash, no external deps.
# Respects --no-color, NO_COLOR env, and TTY detection.

# ANSI codes (standard)
if [[ -z "${RED:-}" ]]; then
  RED='\033[0;31m'
  YELLOW='\033[0;33m'
  GREEN='\033[0;32m'
  RESET='\033[0m'
  BOLD='\033[1m'
fi

# Internal: do we emit color?
# Caller sets USE_COLOR=1 or 0 before sourcing or calling.
# Defaults to auto.
_should_color() {
  local force_color="${1:-}"
  if [[ -n "${NO_COLOR:-}" ]]; then
    return 1
  fi
  if [[ "$force_color" == "0" || "$USE_COLOR" == "0" ]]; then
    return 1
  fi
  if [[ -t 1 ]]; then
    return 0
  fi
  return 1
}

# colorize "text" level
# level: ok | warn | crit | ""
colorize() {
  local text="$1"
  local level="${2:-}"
  if ! _should_color "${USE_COLOR:-}"; then
    printf '%s' "$text"
    return
  fi
  case "$level" in
    crit|red)
      printf '%b%s%b' "$RED" "$text" "$RESET"
      ;;
    warn|yellow)
      printf '%b%s%b' "$YELLOW" "$text" "$RESET"
      ;;
    ok|green)
      printf '%b%s%b' "$GREEN" "$text" "$RESET"
      ;;
    *)
      printf '%s' "$text"
      ;;
  esac
}

# Helper to color a percentage value based on thresholds
# color_pct pct warn_threshold crit_threshold
color_pct() {
  local pct="$1"
  local warn_t="${2:-70}"
  local crit_t="${3:-90}"
  local lvl="ok"
  # numeric compare, handle floats
  if awk "BEGIN {exit !($pct >= $crit_t)}" 2>/dev/null; then
    lvl="crit"
  elif awk "BEGIN {exit !($pct >= $warn_t)}" 2>/dev/null; then
    lvl="warn"
  fi
  colorize "$pct" "$lvl"
}

# Simple bar: make_bar 75 10 -> [#######   ]
make_bar() {
  local pct="${1:-0}"
  local width="${2:-10}"
  local filled
  filled=$(awk "BEGIN {f = int($pct * $width / 100); if (f > $width) f=$width; print f}")
  local empty=$((width - filled))
  local bar
  bar="$(printf '%*s' "$filled" | tr ' ' '#')"
  bar="${bar}$(printf '%*s' "$empty" | tr ' ' ' ')"
  printf '[%s]' "$bar"
}
