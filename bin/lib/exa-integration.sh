#!/usr/bin/env bash
# exa-integration.sh — shared Exa integration for all Mossfund research scripts
# Source this from any script that needs Exa search.
#
# Provides:
#   ensure_exa_key()     — verify EXA_API_KEY is available, source secrets if needed
#   exa_search()         — search Exa and return JSON results
#   exa_search_md()      — search Exa and return formatted markdown
#   exa_prompt_header()  — markdown header for sub-agent/research prompts
#
# Usage:
#   source bin/lib/exa-integration.sh
#   exa_search "query" [count] [neural|keyword]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- ensure API key ---
ensure_exa_key() {
  if [[ -z "${EXA_API_KEY:-}" ]]; then
    local sd_secrets="$HOME/.config/moss/secrets-systemd.env"
    if [[ -f "$sd_secrets" ]]; then
      set -a; source "$sd_secrets"; set +a
    else
      local secrets="$HOME/.config/moss/secrets.env"
      if [[ -f "$secrets" ]]; then
        source "$secrets"
      fi
    fi
  fi
  if [[ -z "${EXA_API_KEY:-}" ]]; then
    echo "ERROR: EXA_API_KEY not set. Check ~/.config/moss/secrets.env" >&2
    return 1
  fi
  return 0
}

# --- Exa search returning JSON ---
exa_search() {
  local query="${1:?"exa_search: query required"}"
  local count="${2:-5}"
  local type="${3:-neural}"
  
  ensure_exa_key || return 1
  
  curl -s "https://api.exa.ai/search" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$(cat <<JSON
{
  "query": $(echo "$query" | jq -Rs .),
  "type": "$type",
  "numResults": $count
}
JSON
)"
}

# --- Exa search returning markdown (for sub-agent prompts) ---
exa_search_md() {
  local query="${1:?"exa_search_md: query required"}"
  local count="${2:-5}"
  local type="${3:-neural}"
  
  local resp
  resp=$(exa_search "$query" "$count" "$type") || return 1
  
  if echo "$resp" | jq -e '.error' >/dev/null 2>&1; then
    echo "*Exa error: $(echo "$resp" | jq -r '.error.message // .error')*" >&2
    return 2
  fi
  
  local results_count
  results_count=$(echo "$resp" | jq '[.results[]?] | length' 2>/dev/null || echo 0)
  
  if [[ "$results_count" -eq 0 ]]; then
    echo "*Inga resultat från Exa för: $query*"
    return 0
  fi
  
  echo "### 🔬 Exa Search ($type): ${query:0:80}"
  echo ""
  
  echo "$resp" | jq -c '.results[]?' 2>/dev/null | while IFS= read -r item; do
    local title url author published score
    title=$(echo "$item" | jq -r '.title // "Untitled"')
    url=$(echo "$item" | jq -r '.url // "#"')
    author=$(echo "$item" | jq -r '.author // ""')
    published=$(echo "$item" | jq -r '.published // ""')
    score=$(echo "$item" | jq -r '.score // ""')
    
    echo "- **[${title}](${url})**"
    [[ -n "$author" && "$author" != "null" ]] && echo "  - Author: $author"
    [[ -n "$published" && "$published" != "null" ]] && echo "  - Published: $published"
    [[ -n "$score" && "$score" != "null" ]] && echo "  - Score: $score"
    echo ""
  done
}

# --- Markdown header for sub-agent prompts ---
exa_prompt_header() {
  cat <<'HEADER'
## 🔧 Available Search Tools

You have **TWO** search engines available — use **BOTH**:

1. **web_search + web_fetch** — OpenClaw built-in search (general web, free tier)
2. **exec("bin/exa-search \"query\" --count=5")** — **Exa AI neural search** (better for business data, pricing, competitors, market research, technical documentation)

**How to use Exa:**
```bash
# Neural search (best for most queries):
exec("bin/exa-search \"AI API reselling Europe pricing\" --count=5")

# Keyword search (for exact matches):
exec("bin/exa-search \"synthetic data generation\" --type=keyword --count=3")
```

**Strategy:**
1. Start with Exa neural search for initial deep findings
2. Use web_search for supplementary/broader results
3. Use web_fetch to read pages found via Exa

HEADER
}

# --- Sub-agent prompt template with Exa ---
exa_research_prompt() {
  local topic="${1:?"exa_research_prompt: topic required"}"
  local output_file="${2:?"exa_research_prompt: output_file required"}"
  
  echo "## UPPGIFT: Deep Research för Mossfund"
  echo ""
  echo "Forska djupt på: **$topic**"
  echo ""
  exa_prompt_header
  echo ""
  echo "## Output"
  echo ""
  echo "Skriv din fullständiga rapport till: \`$output_file\`"
  echo ""
  echo "## Required Sections"
  echo ""
  echo "1. Sammanfattning (Executive Summary, 3-5 meningar)"
  echo "2. Marknadsanalys (storlek, tillväxt, trender)"
  echo "3. Konkurrentanalys (namn, priser, styrkor/svagheter)"
  echo "4. Affärsmodellsrekommendation"
  echo "5. Revenue estimate (lägsta/realistiskt/aggressivt per månad)"
  echo "6. Genomförbarhet (1-10) och tid till första intäkt"
  echo "7. Confidence Audit"
  echo ""
  echo "Var grundlig. Minst 5 Exa-sökningar + 3 web_fetch."
}

: "${EXA_API_KEY:=}"  # ensure variable is declared
