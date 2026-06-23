#!/usr/bin/env bash
# research-dispatcher.sh
# Automatic research detection + 48h cache for grok-build.
# Used by run-grok-task.sh (or manually) before composing the plan prompt.
#
# Usage examples:
#   source research-dispatcher.sh
#   if needs_research "$user_prompt"; then
#       research_block=$(prepare_research_findings "$user_prompt")
#   fi
#
# Cache location: $WORKSPACE/memory/research-cache/<key>.json
# Key = sha256 of normalized query (first 12 chars for filename safety)
#
set -euo pipefail

WORKSPACE="${WORKSPACE:-/root/.openclaw/workspace}"
CACHE_DIR="${WORKSPACE}/memory/research-cache"
TTL_HOURS=48

# Research classification system (significantly strengthened June 2026)
# Returns structured decision instead of simple boolean.

# === HIGH-CONFIDENCE TRIGGERS (almost always need external data) ===
HIGH_CONFIDENCE_PATTERNS=(
    # Explicit pricing / limits / availability questions
    'pricing' 'current pricing' 'price' 'cost' 'free tier' 'paid plan'
    'rate limit' 'quota' 'limits' 'how much does'
    # Time-sensitive external facts
    'june 2026' 'july 2026' '2026' 'current status' 'as of 2026'
    'is .* still' 'does .* still exist' 'deprecated' 'sunset'
    # x402 / payment rails
    'x402' 'x-402' 'micropayment' 'usdc payment' 'facilitator'
    # MCP monetization & marketplace
    'monetiz' 'monetization' 'billing' 'payment' 'skill marketplace'
    'agent economy' 'mcp server.*revenue' 'mcp.*monetiz'
    # Agensi / new agent platforms
    'agensi' 'agent.*marketplace' 'skill.*market'
)

# === SERVICE + ACTION COMBINATIONS (medium-high confidence) ===
SERVICE_ACTION_PATTERNS=(
    # External service + integration/usage verb
    'integrate.*(x402|mcp|openrouter|serper|exa|agensi)'
    '(x402|mcp|openrouter).*integrate'
    'add.*(billing|payment|monetization).*to'
    'use.*(x402|mcp).*for'
    'connect.*to.*(x402|mcp|openrouter)'
    # Status / comparison questions
    '(what|how).*current.*(x402|mcp|openrouter|serper|exa)'
    'compare.*(x402|mcp|openrouter)'
    'best.*(x402|mcp|openrouter).*2026'
)

# === INTERNAL-ONLY SIGNALS (negative triggers - do NOT research) ===
# These are checked FIRST and override everything else.
# Made more contextual to reduce false negatives (e.g. "refactor the x402 integration" should still trigger research).
INTERNAL_ONLY_PATTERNS=(
    # Strong explicit signals
    'purely internal' 'internal only' 'internal-only' 'no external' 'skip research'
    'do not research' 'no research needed' 'research not required'
    'self contained' 'self-contained' 'workspace only' 'our own code base'
    # Context + action (more precise than single words)
    'purely internal refactor' 'internal refactor only' 'internal code change'
    'just.*internal' 'only.*internal.*change'
    # Negative research intent
    'without.*research' 'no need.*research' 'research.*not needed'
)

# Legacy flat list kept for backward compatibility / simple greps
RESEARCH_KEYWORDS=(
    pricing x402 mcp agensi openrouter api 2026
    monetization billing payment "skill marketplace" "agent economy"
    "current status" adoption deprecation
)

needs_research() {
    local decision
    decision=$(classify_research_need "$1")
    case "$decision" in
        HIGH|MEDIUM) return 0 ;;
        *) return 1 ;;
    esac
}

# Structured classification (HIGH | MEDIUM | INTERNAL | NONE)
classify_research_need() {
    local prompt="$1"
    local lower
    lower=$(echo "$prompt" | tr '[:upper:]' '[:lower:]' | tr -s ' ')

    # 0. INTERNAL-ONLY patterns first (override)
    for pat in "${INTERNAL_ONLY_PATTERNS[@]}"; do
        if [[ "$lower" == *"$pat"* ]]; then
            echo "INTERNAL"
            return
        fi
    done

    # 1. High-confidence external signals
    for pat in "${HIGH_CONFIDENCE_PATTERNS[@]}"; do
        if [[ "$lower" == *"$pat"* ]]; then
            echo "HIGH"
            return
        fi
    done

    # 2. Service + action patterns (use real regex =~ because patterns contain ( | .* etc.)
    for pat in "${SERVICE_ACTION_PATTERNS[@]}"; do
        if [[ "$lower" =~ $pat ]]; then
            echo "MEDIUM"
            return
        fi
    done

    # 3. Legacy keyword fallback
    for kw in "${RESEARCH_KEYWORDS[@]}"; do
        if [[ "$lower" == *"$kw"* ]]; then
            echo "MEDIUM"
            return
        fi
    done

    echo "NONE"
}

# Human-readable explanation (includes the triggering pattern when possible)
explain_research_decision() {
    local prompt="$1"
    local decision matched
    decision=$(classify_research_need "$prompt")
    local lower
    lower=$(echo "$prompt" | tr '[:upper:]' '[:lower:]' | tr -s ' ')

    # Find which pattern actually matched (for transparency)
    matched="(no specific pattern)"
    case "$decision" in
        HIGH)
            for pat in "${HIGH_CONFIDENCE_PATTERNS[@]}"; do
                if [[ "$lower" == *"$pat"* ]]; then
                    matched="$pat"
                    break
                fi
            done
            echo "HIGH confidence external research required (trigger: $matched)"
            ;;
        MEDIUM)
            for pat in "${SERVICE_ACTION_PATTERNS[@]}"; do
                if [[ "$lower" =~ $pat ]]; then
                    matched="$pat"
                    break
                fi
            done
            if [[ "$matched" == "(no specific pattern)" ]]; then
                for kw in "${RESEARCH_KEYWORDS[@]}"; do
                    if [[ "$lower" == *"$kw"* ]]; then
                        matched="$kw"
                        break
                    fi
                done
            fi
            echo "MEDIUM confidence – service/action or keyword match (trigger: $matched)"
            ;;
        INTERNAL)
            for pat in "${INTERNAL_ONLY_PATTERNS[@]}"; do
                if [[ "$lower" == *"$pat"* ]]; then
                    matched="$pat"
                    break
                fi
            done
            echo "INTERNAL-ONLY signal detected – research explicitly disabled (trigger: $matched)"
            ;;
        NONE)
            echo "No research signals detected – internal refactor or unrelated task"
            ;;
    esac
}

# Create a stable cache key from the prompt (sha256, 24 chars for lower collision risk)
# Includes full prompt hash + length to avoid prefix-collision attacks.
make_cache_key() {
    local prompt="$1"
    local norm len hash
    norm=$(echo "$prompt" | tr '[:upper:]' '[:lower:]' | tr -s '[:space:]' ' ' | sed 's/^ *//;s/ *$//')
    len=$(echo -n "$norm" | wc -c)
    hash=$(echo -n "$norm" | sha256sum | cut -c1-24)
    echo "${hash}-${len}"
}

cache_path() {
    local key="$1"
    echo "${CACHE_DIR}/${key}.json"
}

# Returns 0 if fresh cache exists, 1 otherwise. Also echoes the path if fresh.
has_fresh_cache() {
    local key="$1"
    local path
    path="$(cache_path "$key")"

    if [[ ! -f "$path" ]]; then
        return 1
    fi

    local mtime now age_hours
    mtime=$(stat -c %Y "$path" 2>/dev/null || echo 0)
    now=$(date +%s)
    age_hours=$(( (now - mtime) / 3600 ))

    if (( age_hours < TTL_HOURS )); then
        echo "$path"
        return 0
    fi

    return 1
}

# Write research results to cache
write_research_cache() {
    local key="$1"
    local quick_results="$2"
    local deep_results="$3"
    local sources="$4"
    local path
    path="$(cache_path "$key")"

    mkdir -p "$CACHE_DIR"

    python3 - "$path" "$key" "$quick_results" "$deep_results" "$sources" <<'PY'
import json, sys, datetime
path, key, quick, deep, sources = sys.argv[1:6]

data = {
    "key": key,
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "ttl_hours": 48,
    "quick_results": quick,
    "deep_results": deep,
    "sources": sources
}

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")
PY
    echo "Research cached → $path"
}

# Read and format fresh cache as Research Findings markdown block
read_research_cache_as_findings() {
    local path="$1"

    python3 - "$path" <<'PY'
import json, sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

print("## Research Findings (from cache)")
print(f"- Cached at: {data.get('timestamp')}")
print(f"- TTL: {data.get('ttl_hours')} hours")
print()
print("### Quick facts")
print(data.get("quick_results", "(no quick results)"))
print()
print("### Deep context")
print(data.get("deep_results", "(no deep results)"))
print()
print("### Sources")
print(data.get("sources", "(no sources)"))
PY
}

# Main entry: prepare the Research Findings block for the plan prompt.
# If fresh cache exists → return it.
# Otherwise → return a placeholder instructing the planner (or human) to run research.
prepare_research_findings() {
    local user_prompt="$1"
    local key
    key="$(make_cache_key "$user_prompt")"

    local cached_path
    if cached_path="$(has_fresh_cache "$key")"; then
        read_research_cache_as_findings "$cached_path"
        return 0
    fi

    # No fresh cache – return placeholder that tells the planner what to do
    cat <<EOF
## Research Findings (AUTO-DISPATCH REQUIRED)

No fresh cache entry found for this query.

**Next step (automatic in future versions):**  
The orchestrator should now spawn two parallel research sub-agents:

1. Quick factual (Serper)
   - Use template: skills/grok-build/references/subagent-quick-serper.md
   - Task: "Search for current facts about: $(echo "$user_prompt" | head -c 120)..."

2. Deep technical synthesis (Exa)
   - Use template: skills/grok-build/references/subagent-deep-exa.md
   - Task: "Synthesize adoption, pitfalls and best practices for: $(echo "$user_prompt" | head -c 120)..."

After both sub-agents complete, call:
  research-dispatcher.sh write_cache <key> "<quick>" "<deep>" "<sources>"

Then re-run prepare_research_findings to get the final block.

**Manual fallback:** Run the two sub-agent prompts manually and cache the results.
EOF
}

# Convenience: show cache status for a prompt
cache_status() {
    local user_prompt="$1"
    local key
    key="$(make_cache_key "$user_prompt")"
    local path
    path="$(cache_path "$key")"

    echo "Cache key: $key"
    echo "Cache file: $path"

    if [[ -f "$path" ]]; then
        local mtime now age
        mtime=$(stat -c %Y "$path")
        now=$(date +%s)
        age=$(( (now - mtime) / 3600 ))
        echo "Age: ${age}h (TTL ${TTL_HOURS}h)"
        if (( age < TTL_HOURS )); then
            echo "Status: FRESH"
        else
            echo "Status: STALE"
        fi
    else
        echo "Status: MISSING"
    fi
}

# === Cache management commands (improvement #6) ===

cache_list() {
    echo "Research cache entries in $CACHE_DIR (TTL ${TTL_HOURS}h):"
    if [[ ! -d "$CACHE_DIR" ]]; then
        echo "(cache directory does not exist)"
        return
    fi

    local count=0
    while IFS= read -r -d '' f; do
        [[ -f "$f" ]] || continue
        local key age status
        key=$(basename "$f" .json)
        local mtime now
        mtime=$(stat -c %Y "$f")
        now=$(date +%s)
        age=$(( (now - mtime) / 3600 ))
        if (( age < TTL_HOURS )); then
            status="FRESH"
        else
            status="STALE"
        fi
        echo "  $key  (${age}h, $status)"
        ((count++))
    done < <(find "$CACHE_DIR" -name '*.json' -print0 2>/dev/null | sort -z)

    echo "Total: $count entries"
}

cache_clear() {
    local target="${1:-all}"

    if [[ "$target" == "all" ]]; then
        if [[ -d "$CACHE_DIR" ]]; then
            rm -f "$CACHE_DIR"/*.json 2>/dev/null || true
            echo "Cleared entire research cache."
        else
            echo "Cache directory did not exist."
        fi
        return
    fi

    # Assume target is a key or prompt
    local path
    if [[ -f "$target" ]]; then
        path="$target"
    else
        local key
        key="$(make_cache_key "$target")"
        path="$(cache_path "$key")"
    fi

    if [[ -f "$path" ]]; then
        rm -f "$path"
        echo "Cleared cache entry: $path"
    else
        echo "No cache entry found for: $target"
    fi
}

cache_inspect() {
    local target="$1"
    local path

    if [[ -f "$target" ]]; then
        path="$target"
    else
        local key
        key="$(make_cache_key "$target")"
        path="$(cache_path "$key")"
    fi

    if [[ ! -f "$path" ]]; then
        echo "Cache entry not found: $path"
        return 1
    fi

    echo "=== Cache entry: $path ==="
    cat "$path"
}

cache_refresh() {
    # Convenience: clear + show prepare message
    local prompt="$1"
    cache_clear "$prompt"
    echo ""
    echo "Now run research (Serper + Exa) manually or via sessions_spawn, then:"
    echo "  research-dispatcher.sh write <key> '<quick>' '<deep>' '<sources>'"
    echo "Or re-run prepare to get the placeholder again."
}

# Allow sourcing or direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-}" in
        needs)
            needs_research "${2:-}" && echo "YES" || echo "NO"
            ;;
        classify)
            classify_research_need "${2:-}"
            ;;
        explain)
            explain_research_decision "${2:-}"
            ;;
        prepare)
            prepare_research_findings "${2:-}"
            ;;
        status)
            cache_status "${2:-}"
            ;;
        write)
            # write <key> <quick> <deep> <sources>
            write_research_cache "${2:-}" "${3:-}" "${4:-}" "${5:-}"
            ;;
        list)
            cache_list
            ;;
        clear)
            cache_clear "${2:-all}"
            ;;
        inspect)
            cache_inspect "${2:-}"
            ;;
        refresh)
            cache_refresh "${2:-}"
            ;;
        *)
            echo "Usage: research-dispatcher.sh {needs|classify|explain|prepare|status|write|list|clear|inspect|refresh} [arg]"
            echo "  needs|classify|explain <prompt>     - decision making"
            echo "  prepare|status <prompt>            - research flow"
            echo "  write <key> <quick> <deep> <src> - store results"
            echo "  list|clear|inspect|refresh         - cache management"
            exit 1
            ;;
    esac
fi
