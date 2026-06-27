#!/usr/bin/env bash
# fallback.sh — Exa → Serper search fallback with unified result envelope

LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$(dirname "$LIB_DIR")"

# shellcheck source=retry.sh
source "$LIB_DIR/retry.sh"

wrap_exa_response() {
  local raw="$1"
  if echo "$raw" | jq -e '.provider' >/dev/null 2>&1; then
    echo "$raw" | jq -c .
    return 0
  fi
  echo "$raw" | jq -c '{
    provider: "exa",
    results: (.results // []),
    costDollars: (.costDollars // {total: 0})
  }'
}

normalize_serper_response() {
  local raw="$1"
  echo "$raw" | jq -c '{
    provider: "serper",
    results: [.organic[]? | {title, url: .link, highlights: [(.snippet // "")]}],
    costDollars: {total: 0}
  }'
}

_exa_should_fallback() {
  local exit_code="$1"
  local output="$2"

  [ "$exit_code" -ne 0 ] && return 0

  if ! echo "$output" | jq -e '.results' >/dev/null 2>&1; then
    return 0
  fi

  if echo "$output" | jq -e '.error' >/dev/null 2>&1; then
    return 0
  fi

  if echo "$output" | grep -qiE '401|403|timeout|429|invalid api key|unauthorized'; then
    return 0
  fi

  return 1
}

search_with_fallback() {
  local query="$1"
  local type="${2:-auto}"
  local num="${3:-5}"
  local output_path="$4"

  local exa_cmd="${EXA_BIN:-$BIN_DIR/exa-search}"
  local serper_cmd="${SERPER_BIN:-$BIN_DIR/serper-search}"

  local exa_out exa_code

  exa_out=$(mktemp)
  set +e
  retry_with_backoff 3 1 "$exa_cmd" "$query" --type="$type" --count="$num" >"$exa_out" 2>&1
  exa_code=$?
  set -e

  local exa_body
  exa_body=$(cat "$exa_out")
  rm -f "$exa_out"

  if [ "$exa_code" -eq 0 ] && ! _exa_should_fallback 0 "$exa_body"; then
    wrap_exa_response "$exa_body" >"$output_path"
    return 0
  fi

  if _exa_should_fallback "$exa_code" "$exa_body"; then
    echo "↪️ Exa failed for [$type] query — falling back to Serper" >&2
  fi

  local serp_out serp_code
  serp_out=$(mktemp)
  set +e
  retry_with_backoff 3 1 "$serper_cmd" "$query" --num="$num" >"$serp_out" 2>&1
  serp_code=$?
  set -e

  local serp_body
  serp_body=$(cat "$serp_out")
  rm -f "$serp_out"

  if [ "$serp_code" -eq 0 ] && echo "$serp_body" | jq -e '.organic' >/dev/null 2>&1; then
    normalize_serper_response "$serp_body" >"$output_path"
    return 0
  fi

  echo "Error: both Exa and Serper failed for query: $query" >&2
  return 1
}