#!/usr/bin/env bash
# retry.sh — exponential backoff retry wrapper for transient failures

is_transient_failure() {
  local exit_code="${1:-1}"
  local output="${2:-}"

  # Permanent auth/validation errors — never retry
  if echo "$output" | grep -qiE '401|403|400|invalid api key|unauthorized|forbidden|bad request'; then
    return 1
  fi

  # Transient curl exit codes
  case "$exit_code" in
    7|28|52) return 0 ;;
  esac

  # Transient patterns in output
  if echo "$output" | grep -qiE 'timeout|timed out|429|503|502|504|rate limit|too many requests|service unavailable|connection reset|connection refused'; then
    return 0
  fi

  # Exit 2 from API wrappers with transient-looking errors
  if [ "$exit_code" -eq 2 ] && echo "$output" | grep -qiE '429|503|502|504|timeout|rate limit|service unavailable'; then
    return 0
  fi

  return 1
}

retry_with_backoff() {
  local max_attempts="${1:-3}"
  local delay="${2:-1}"
  shift 2

  local attempt=1
  local exit_code=1
  local output=""
  local tmp_out

  while [ "$attempt" -le "$max_attempts" ]; do
    tmp_out=$(mktemp)
    set +e
    "$@" >"$tmp_out" 2>&1
    exit_code=$?
    set -e
    output=$(cat "$tmp_out")
    rm -f "$tmp_out"

    if [ "$exit_code" -eq 0 ]; then
      printf '%s' "$output"
      return 0
    fi

    if ! is_transient_failure "$exit_code" "$output"; then
      printf '%s' "$output" >&2
      return "$exit_code"
    fi

    if [ "$attempt" -lt "$max_attempts" ]; then
      echo "  ⚠️ retry attempt $attempt/$max_attempts failed (exit $exit_code), retrying in ${delay}s..." >&2
      sleep "$delay"
      delay=$((delay * 2))
    fi
    attempt=$((attempt + 1))
  done

  printf '%s' "$output" >&2
  return 1
}