#!/usr/bin/env bash
# Same as check.sh but also processes test files

declare -A ACCEPTED
while IFS='|' read -r script flags; do
  ACCEPTED["$script"]="$flags"
done < /tmp/flag-audit/accepted-flags.txt

issues=0
echo "=== Cross-check report (all callers incl. tests) ==="
echo ""

while IFS= read -r line; do
  invocation="${line#*:*:}"
  target=$(echo "$invocation" | grep -oE "bin/[a-z0-9_-]+" | head -1 | sed 's|bin/||')
  [ -z "$target" ] && continue
  
  accepted="${ACCEPTED[$target]:-}"
  [ -z "$accepted" ] && continue
  
  for flag in $(echo "$invocation" | grep -oE -- "--[a-z][a-z0-9-]+(=[a-zA-Z0-9_.,:@/-]+)?" | sort -u); do
    bare=$(echo "$flag" | sed 's/=.*//')
    
    if ! echo " $accepted " | grep -q " $bare "; then
      echo "MISMATCH: $line"
      echo "  Target: $target | Flag: $bare | Accepted: $accepted"
      echo ""
      issues=$((issues + 1))
    fi
  done
done < /tmp/flag-audit/invocations.txt

echo "==="
echo "Total mismatches: $issues"
