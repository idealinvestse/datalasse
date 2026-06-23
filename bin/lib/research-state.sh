# research-state.sh — shared helpers for persistent research state
# shellcheck shell=bash

_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_BIN_DIR="$(dirname "$_LIB_DIR")"
WORKSPACE_DIR="${WORKSPACE_DIR:-$(cd "$_BIN_DIR/.." && pwd)}"

RESEARCH_DIR="${RESEARCH_DIR:-${HOME}/.config/moss/research}"
GOALS_FILE="$RESEARCH_DIR/goals.jsonl"
METRICS_FILE="$RESEARCH_DIR/metrics.jsonl"
STATUS_JSON="$RESEARCH_DIR/status.json"
RUNS_DIR="$RESEARCH_DIR/runs"
PLANS_DIR="$RESEARCH_DIR/plans"
STATUS_MD="$WORKSPACE_DIR/STATUS_RESEARCH.md"
FEEDBACK_FILE="$RESEARCH_DIR/feedback.jsonl"
WATCH_STATE_FILE="$RESEARCH_DIR/watch-state.json"
WATCH_LOG="$RESEARCH_DIR/watch.log"
METRICS_WEEKLY_MD="$RESEARCH_DIR/metrics-weekly.md"
PRIORITIZATION_FILE="$RESEARCH_DIR/prioritization.json"
IMPROVEMENTS_FILE="$RESEARCH_DIR/improvements.json"
DISCOVERED_GOALS_FILE="$RESEARCH_DIR/discovered-goals.json"

research_ensure_dirs() {
  mkdir -p "$RESEARCH_DIR" "$RUNS_DIR" "$PLANS_DIR"
  touch "$GOALS_FILE" "$METRICS_FILE" "$FEEDBACK_FILE"
  if [ ! -f "$WATCH_STATE_FILE" ]; then
    atomic_write "$WATCH_STATE_FILE" '{}'
  fi
}

research_run_id() {
  date -u +%Y-%m-%dT%H-%M-%S
}

atomic_write() {
  local path="$1"
  local content="$2"
  local tmp="${path}.tmp.$$"
  printf '%s' "$content" > "$tmp"
  mv "$tmp" "$path"
}

goals_read_json() {
  research_ensure_dirs
  if [ ! -s "$GOALS_FILE" ]; then
    echo '[]'
    return 0
  fi
  jq -s '.' "$GOALS_FILE" 2>/dev/null || echo '[]'
}

goals_append_line() {
  local json="$1"
  research_ensure_dirs
  printf '%s\n' "$(echo "$json" | jq -c .)" >> "$GOALS_FILE"
}

goals_rewrite_all() {
  local json_array="$1"
  research_ensure_dirs
  local tmp="${GOALS_FILE}.tmp.$$"
  echo "$json_array" | jq -c '.[]' > "$tmp"
  mv "$tmp" "$GOALS_FILE"
}

goals_update_line() {
  local id="$1"
  shift
  local updated
  updated=$(goals_read_json | jq --arg gid "$id" "$@")
  goals_rewrite_all "$updated"
}

goals_update_field() {
  local id="$1"
  local jq_expr="$2"
  goals_update_line "$id" "map(if .id == \$gid then ($jq_expr) else . end)"
}

goal_get() {
  local id="$1"
  local goal
  goal=$(goals_read_json | jq -c --arg id "$id" '.[] | select(.id == $id)')
  if [ -z "$goal" ]; then
    echo "Error: goal not found: $id" >&2
    return 1
  fi
  echo "$goal"
}

research_next_goal_id() {
  local today max next_n
  today=$(date -u +%Y%m%d)
  max=$(goals_read_json | jq -r --arg d "g-${today}-" '
    [.[] | select(.id | startswith($d)) | .id | split("-")[2] | tonumber] | max // 0')
  next_n=$((max + 1))
  printf 'g-%s-%03d' "$today" "$next_n"
}

plan_path_for() {
  local id="$1"
  echo "$PLANS_DIR/${id}.md"
}

new_goal_record() {
  local id="$1"
  local question="$2"
  local priority="$3"
  local tags_json="$4"
  local now plan
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  plan=$(plan_path_for "$id")
  jq -n \
    --arg id "$id" \
    --arg q "$question" \
    --argjson p "$priority" \
    --argjson tags "$tags_json" \
    --arg now "$now" \
    --arg plan "$plan" \
    '{
      id: $id,
      question: $q,
      status: "active",
      priority: $p,
      tags: $tags,
      created_at: $now,
      updated_at: $now,
      notes: [],
      total_steps: 0,
      answered_steps: 0,
      cost_so_far: 0.0,
      runs: [],
      plan_path: $plan
    }'
}

metrics_append() {
  local json="$1"
  research_ensure_dirs
  printf '%s\n' "$(echo "$json" | jq -c .)" >> "$METRICS_FILE"
}

run_write() {
  local run_id="$1"
  local json="$2"
  research_ensure_dirs
  atomic_write "$RUNS_DIR/${run_id}.json" "$json"
}

record_run_for_goal() {
  local goal_id="$1"
  local run_id="$2"
  local artifact_json="$3"
  local cost duration

  if ! goal_get "$goal_id" >/dev/null 2>&1; then
    echo "Warning: goal $goal_id not found; skipping run record" >&2
    return 1
  fi

  run_write "$run_id" "$artifact_json"

  cost=$(echo "$artifact_json" | jq -r '.cost // 0')
  duration=$(echo "$artifact_json" | jq -r '.duration_s // 0')

  metrics_append "$(echo "$artifact_json" | jq -c \
    --arg ts "$(echo "$artifact_json" | jq -r '.timestamp // empty')" \
    '{
      timestamp: (if $ts != "" then $ts else (now | strftime("%Y-%m-%dT%H:%M:%SZ")) end),
      run_id: .run_id,
      goal_id: .goal_id,
      question: .question,
      cost: .cost,
      latency_s: .duration_s,
      stages_run: .stages_run,
      sources_found: .sources_found,
      verification_count: .verification_count,
      status: (if .failed then "failed" else "ok" end)
    }')"

  local now
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  goals_update_line "$goal_id" \
    --arg run_id "$run_id" \
    --argjson cost "$cost" \
    --arg now "$now" \
    'map(if .id == $gid then .runs += [$run_id] | .cost_so_far += $cost | .updated_at = $now else . end)'
}

record_failed_run_for_goal() {
  local goal_id="$1"
  local run_id="$2"
  local query="$3"
  local stages_run="$4"
  local cost="$5"
  local workdir="$6"
  local ts
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  local artifact
  artifact=$(jq -n \
    --arg run_id "$run_id" \
    --arg goal_id "$goal_id" \
    --arg query "$query" \
    --argjson stages "$stages_run" \
    --argjson cost "$cost" \
    --arg workdir "$workdir" \
    --arg ts "$ts" \
    '{
      run_id: $run_id,
      goal_id: $goal_id,
      question: $query,
      stages_run: $stages,
      cost: $cost,
      report_path: null,
      duration_s: 0,
      sources_found: 0,
      verification_count: 0,
      summary: "run failed or incomplete",
      budget_exceeded: false,
      workdir: $workdir,
      timestamp: $ts,
      failed: true
    }')
  record_run_for_goal "$goal_id" "$run_id" "$artifact" || true
}

# Artifact JSON may include optional step_id when --mark-step is used (see deep-research).

feedback_append() {
  local json="$1"
  research_ensure_dirs
  printf '%s\n' "$(echo "$json" | jq -c .)" >> "$FEEDBACK_FILE"
}

feedback_read_json() {
  research_ensure_dirs
  if [ ! -s "$FEEDBACK_FILE" ]; then
    echo '[]'
    return 0
  fi
  jq -s '.' "$FEEDBACK_FILE" 2>/dev/null || echo '[]'
}

watch_state_read() {
  research_ensure_dirs
  if [ ! -s "$WATCH_STATE_FILE" ]; then
    echo '{}'
    return 0
  fi
  jq '.' "$WATCH_STATE_FILE" 2>/dev/null || echo '{}'
}

watch_state_write() {
  local json="$1"
  research_ensure_dirs
  atomic_write "$WATCH_STATE_FILE" "$(echo "$json" | jq -c .)"
}

watch_state_set() {
  local goal_id="$1"
  local step_id="$2"
  local next_run="${3:-}"
  local last_attempt="${4:-}"
  local last_status="${5:-}"
  local state
  state=$(watch_state_read | jq \
    --arg gid "$goal_id" \
    --arg sid "$step_id" \
    --arg next_run "$next_run" \
    --arg last_attempt "$last_attempt" \
    --arg last_status "$last_status" \
    '.[$gid] = (.[$gid] // {}) | .[$gid][$sid] = {
      next_run: (if $next_run == "" then null else $next_run end),
      last_attempt: (if $last_attempt == "" then null else $last_attempt end),
      last_status: (if $last_status == "" then null else $last_status end)
    }')
  watch_state_write "$state"
}

watch_log() {
  local msg="$1"
  research_ensure_dirs
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$msg" >> "$WATCH_LOG"
}

plan_parse_steps() {
  local plan_path="$1"
  local goal_id="${2:-}"
  if [ ! -f "$plan_path" ]; then
    echo '[]'
    return 0
  fi
  python3 - "$plan_path" "$goal_id" <<'PY'
import json, re, sys

plan_path, goal_id = sys.argv[1], sys.argv[2]
with open(plan_path) as f:
    lines = f.readlines()

steps = []
in_steps = False
checkbox_n = 0
numbered_n = 0

stub_re = re.compile(r'^### (step-\d+): \[(pending|done)\] (.+)$')
checkbox_re = re.compile(r'^- \[ \] (.+)$')
heading_re = re.compile(r'^## Step (\d+): (.+)$')
numbered_re = re.compile(r'^\d+\. (.+)$')

for line in lines:
    s = line.rstrip('\n')
    if s.strip() == '## Steps':
        in_steps = True
        continue
    if in_steps and s.startswith('## ') and s.strip() != '## Steps':
        in_steps = False

    m = stub_re.match(s)
    if m:
        steps.append({
            'goal_id': goal_id,
            'step_id': m.group(1),
            'question': m.group(3).strip(),
            'status': m.group(2),
        })
        continue

    if in_steps:
        m = checkbox_re.match(s)
        if m:
            checkbox_n += 1
            steps.append({
                'goal_id': goal_id,
                'step_id': f'step-{checkbox_n}',
                'question': m.group(1).strip(),
                'status': 'pending',
            })
            continue
        m = numbered_re.match(s)
        if m:
            numbered_n += 1
            steps.append({
                'goal_id': goal_id,
                'step_id': f'step-{numbered_n}',
                'question': m.group(1).strip(),
                'status': 'pending',
            })
            continue

    m = heading_re.match(s)
    if m:
        steps.append({
            'goal_id': goal_id,
            'step_id': f'step-{m.group(1)}',
            'question': m.group(2).strip(),
            'status': 'pending',
        })

print(json.dumps(steps))
PY
}

goal_completed_step_ids() {
  local goal_id="$1"
  research_ensure_dirs
  if [ ! -d "$RUNS_DIR" ] || ! compgen -G "$RUNS_DIR/*.json" >/dev/null; then
    echo '[]'
    return 0
  fi
  jq -s --arg gid "$goal_id" '
    [.[] | select(.goal_id == $gid and .step_id != null and .step_id != "" and .failed != true) | .step_id] | unique
  ' "$RUNS_DIR"/*.json 2>/dev/null || echo '[]'
}

run_dominant_provider() {
  local run_json="$1"
  local workdir
  workdir=$(echo "$run_json" | jq -r '.workdir // empty')
  if [ -z "$workdir" ] || [ ! -f "$workdir/cost-summary.json" ]; then
    echo "unknown"
    return 0
  fi
  local fallbacks
  fallbacks=$(jq '[.events[]? | select(.event == "fallback")] | length' "$workdir/cost-summary.json" 2>/dev/null || echo 0)
  if [ "${fallbacks:-0}" -gt 0 ]; then
    echo "serper-fallback"
  else
    echo "exa"
  fi
}

run_get() {
  local run_id="$1"
  local rf="$RUNS_DIR/${run_id}.json"
  if [ ! -f "$rf" ]; then
    return 1
  fi
  jq '.' "$rf"
}

feedback_record() {
  local run_id="$1"
  local rating="$2"
  local comment="${3:-}"
  local goal_id="${4:-standalone}"
  local provider="${5:-unknown}"
  local now
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  feedback_append "$(jq -n \
    --arg run_id "$run_id" \
    --arg goal_id "$goal_id" \
    --argjson rating "$rating" \
    --arg comment "$comment" \
    --arg provider "$provider" \
    --arg ts "$now" \
    '{
      run_id: $run_id,
      goal_id: $goal_id,
      rating: $rating,
      comment: $comment,
      provider: $provider,
      ts: $ts
    }')"
}

iso_to_epoch() {
  local iso="$1"
  python3 - "$iso" <<'PY'
import sys
from datetime import datetime, timezone

raw = sys.argv[1].strip()
try:
    if raw.count("-") >= 4 and "T" in raw:
        d, t = raw.split("T", 1)
        t = t.replace("-", ":")
        dt = datetime.fromisoformat(f"{d}T{t}").replace(tzinfo=timezone.utc)
    else:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    print(int(dt.timestamp()))
except Exception:
    print(0)
PY
}

goal_last_run_epoch() {
  local goal_json="$1"
  local max_epoch=0
  local run_id ts epoch
  while IFS= read -r run_id; do
    [ -z "$run_id" ] && continue
    local rf="$RUNS_DIR/${run_id}.json"
    if [ -f "$rf" ]; then
      ts=$(jq -r '.timestamp // empty' "$rf")
      if [ -n "$ts" ]; then
        epoch=$(iso_to_epoch "$ts")
      else
        epoch=$(iso_to_epoch "$run_id")
      fi
    else
      epoch=$(iso_to_epoch "$run_id")
    fi
    if [ "${epoch:-0}" -gt "$max_epoch" ]; then
      max_epoch=$epoch
    fi
  done < <(echo "$goal_json" | jq -r '.runs[]? // empty')
  echo "$max_epoch"
}

goal_days_since_last_run() {
  local goal_json="$1"
  local now last_epoch days
  now=$(date +%s)
  last_epoch=$(goal_last_run_epoch "$goal_json")
  if [ "${last_epoch:-0}" -eq 0 ]; then
    local created
    created=$(echo "$goal_json" | jq -r '.created_at // empty')
    if [ -n "$created" ]; then
      last_epoch=$(iso_to_epoch "$created")
    fi
  fi
  if [ "${last_epoch:-0}" -eq 0 ]; then
    echo 999
    return 0
  fi
  days=$(( (now - last_epoch) / 86400 ))
  echo "$days"
}

goal_feedback_avg() {
  local goal_id="$1"
  local avg
  avg=$(feedback_read_json | jq -r --arg gid "$goal_id" '
    [.[] | select(.goal_id == $gid) | .rating] as $r
    | if ($r | length) > 0 then ($r | add / length) else 3.0 end
  ')
  echo "$avg"
}

normalize_priority() {
  local p="$1"
  awk -v p="${p:-3}" 'BEGIN { printf "%.6f", (p - 1) / 4 }'
}

normalize_rating() {
  local avg="$1"
  awk -v a="${avg:-3}" 'BEGIN { printf "%.6f", (a - 1) / 4 }'
}

run_provider_class() {
  local run_json="$1"
  local workdir fallbacks serper_used exa_used
  workdir=$(echo "$run_json" | jq -r '.workdir // empty')
  if [ -z "$workdir" ] || [ ! -f "$workdir/cost-summary.json" ]; then
    local stored
    stored=$(echo "$run_json" | jq -r '.provider // empty' 2>/dev/null)
    case "$stored" in
      serper-fallback) echo "exa-fallback" ;;
      serper) echo "serper-only" ;;
      exa) echo "exa" ;;
      *) echo "unknown" ;;
    esac
    return 0
  fi
  fallbacks=$(jq '[.events[]? | select(.event == "fallback")] | length' "$workdir/cost-summary.json" 2>/dev/null || echo 0)
  serper_used=$(jq '[.events[]? | select(.detail.provider? == "serper" or .detail.provider? == "serper-fallback")] | length' "$workdir/cost-summary.json" 2>/dev/null || echo 0)
  exa_used=$(jq '[.events[]? | select(.detail.provider? == "exa")] | length' "$workdir/cost-summary.json" 2>/dev/null || echo 0)

  if [ "${exa_used:-0}" -eq 0 ] && [ "${serper_used:-0}" -gt 0 ]; then
    echo "serper-only"
  elif [ "${fallbacks:-0}" -gt 0 ]; then
    echo "exa-fallback"
  elif [ "${exa_used:-0}" -gt 0 ] || [ "${fallbacks:-0}" -eq 0 ]; then
    echo "exa"
  else
    echo "unknown"
  fi
}

run_query_type() {
  local run_json="$1"
  local qt question
  qt=$(echo "$run_json" | jq -r '.query_type // empty')
  if [ -n "$qt" ] && [ "$qt" != "null" ]; then
    echo "$qt"
    return 0
  fi
  question=$(echo "$run_json" | jq -r '.question // ""' | tr '[:upper:]' '[:lower:]')
  case "$question" in
    compare:*|comparison:*) echo "compare" ;;
    how:*) echo "how" ;;
    what:*) echo "what" ;;
    why:*) echo "why" ;;
    *) echo "general" ;;
  esac
}

question_length_bucket() {
  local q="$1"
  local n
  n=$(echo "$q" | wc -w | tr -d ' ')
  if [ "${n:-0}" -lt 10 ]; then
    echo "short"
  elif [ "${n:-0}" -le 30 ]; then
    echo "medium"
  else
    echo "long"
  fi
}

goal_question_exists_substr() {
  local candidate="$1"
  local lc cand existing
  lc=$(echo "$candidate" | tr '[:upper:]' '[:lower:]')
  while IFS= read -r existing; do
    [ -z "$existing" ] && continue
    cand=$(echo "$existing" | tr '[:upper:]' '[:lower:]')
    if [[ "$lc" == *"$cand"* ]] || [[ "$cand" == *"$lc"* ]]; then
      return 0
    fi
  done < <(goals_read_json | jq -r '.[].question // empty')
  return 1
}