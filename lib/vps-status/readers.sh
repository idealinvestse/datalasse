#!/usr/bin/env bash
# lib/vps-status/readers.sh
# Data collection functions for vps-status.
# All read_* are side-effect minimal; they populate globals or print machine lines.
# Pure bash + awk + allowed coreutils. Fail gracefully.

# Globals populated by readers (simple, portable)
HOSTNAME=""
KERNEL=""
OS_PRETTY=""
UPTIME_PRETTY=""
UPTIME_S=""
BOOT_AT=""
LOAD_1=""
LOAD_5=""
LOAD_15=""
NPROC=""

# CPU
CPU_TOTAL_PCT="0"
declare -a CPU_CORES_PCT=()
CPU_PSI_SOME=""
CPU_PSI_FULL=""

# Memory (kB)
MEM_TOTAL_KB=""
MEM_USED_KB=""
MEM_FREE_KB=""
MEM_AVAIL_KB=""
MEM_BUFFERS_KB=""
MEM_CACHED_KB=""
SWAP_TOTAL_KB=""
SWAP_USED_KB=""
MEM_PSI_SOME=""
MEM_PSI_FULL=""

# PSI IO
IO_PSI_SOME=""
IO_PSI_FULL=""

# Disks: array of "mount|used|size|pct|type"
declare -a DISK_ENTRIES=()

# Net: array of "iface|rx_bytes|tx_bytes|rx_p|tx_p|err|drop"
declare -a NET_ENTRIES=()
NET_IPV4=""
NET_GW=""

# Procs
declare -a PROCS_CPU=()  # "pid|user|pcpu|pmem|etime|comm"
declare -a PROCS_MEM=()

# Services
SVC_ACTIVE=""
SVC_FAILED=""
declare -a SVC_FAILED_LIST=()

# Snapshot
SNAPSHOT_AT=""

# json_escape string
json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\t'/\\t}"
  s="${s//$'\n'/\\n}"
  printf '%s' "$s"
}

# Read basic host info
read_host() {
  HOSTNAME="$(hostname 2>/dev/null || echo 'unknown')"
  KERNEL="$(uname -r 2>/dev/null || echo 'unknown')"
  if [[ -f /etc/os-release ]]; then
    OS_PRETTY="$(. /etc/os-release; echo "${PRETTY_NAME:-$NAME}")"
  else
    OS_PRETTY="unknown"
  fi
  SNAPSHOT_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date +%s)"
}

read_uptime() {
  UPTIME_PRETTY="$(uptime -p 2>/dev/null || echo 'up ?')"
  local up
  up="$(cat /proc/uptime 2>/dev/null | awk '{print $1}')"
  UPTIME_S="${up:-0}"
  local btime
  btime="$(awk '/btime/ {print $2}' /proc/stat 2>/dev/null)"
  if [[ -n "$btime" ]]; then
    BOOT_AT="$(date -u -d "@$btime" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "$btime")"
  else
    BOOT_AT=""
  fi
}

read_loadavg() {
  local line
  line="$(cat /proc/loadavg 2>/dev/null || echo '0 0 0 0/0 0')"
  read -r LOAD_1 LOAD_5 LOAD_15 _ <<< "$line"
  NPROC="$(nproc 2>/dev/null || echo 1)"
}

# CPU: sample /proc/stat twice for % (total + per-core)
# populates CPU_TOTAL_PCT and CPU_CORES_PCT[]
read_proc_stat() {
  CPU_TOTAL_PCT="0"
  CPU_CORES_PCT=()
  local stat1 stat2
  stat1="$(cat /proc/stat 2>/dev/null)"
  sleep 0.25
  stat2="$(cat /proc/stat 2>/dev/null)"

  # total cpu line
  local idle1 busy1 total1 idle2 busy2 total2
  idle1=$(echo "$stat1" | awk '/^cpu / {print $5}')
  busy1=$(echo "$stat1" | awk '/^cpu / {print $2+$3+$4+$6+$7+$8}')
  total1=$((busy1 + idle1))
  idle2=$(echo "$stat2" | awk '/^cpu / {print $5}')
  busy2=$(echo "$stat2" | awk '/^cpu / {print $2+$3+$4+$6+$7+$8}')
  total2=$((busy2 + idle2))
  if (( total2 > total1 )); then
    CPU_TOTAL_PCT=$(awk "BEGIN {p = ($busy2 - $busy1) * 100.0 / ($total2 - $total1); printf \"%.1f\", p}")
  fi

  # per-core
  local i=0
  while read -r core user nice sys idle iowait irq softirq _; do
    [[ "$core" =~ ^cpu[0-9] ]] || continue
    # use previous sample? Re-parse stat1/stat2 per core
    # Simpler: re-read lines
    :
  done < <(echo "$stat1" | grep '^cpu[0-9]')

  # Better: parse cores from stat2/stat1 pairs
  CPU_CORES_PCT=()
  for coreline in $(echo "$stat1" | awk '/^cpu[0-9]/ {print $1}'); do
    local c1 c2
    c1=$(echo "$stat1" | awk -v c="$coreline" '$1==c {print $2+$3+$4+$6+$7+$8 " " $5}')
    c2=$(echo "$stat2" | awk -v c="$coreline" '$1==c {print $2+$3+$4+$6+$7+$8 " " $5}')
    local b1 i1 b2 i2 t1 t2 p
    read -r b1 i1 <<< "$c1"
    read -r b2 i2 <<< "$c2"
    t1=$((b1 + i1))
    t2=$((b2 + i2))
    if (( t2 > t1 )); then
      p=$(awk "BEGIN {printf \"%.1f\", ($b2-$b1)*100.0/($t2-$t1)}")
    else
      p="0.0"
    fi
    CPU_CORES_PCT+=("$p")
  done
}

# Memory + swap + PSI mem
read_meminfo() {
  local line
  MEM_TOTAL_KB=$(awk '/MemTotal:/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)
  MEM_FREE_KB=$(awk '/MemFree:/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)
  MEM_AVAIL_KB=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo 2>/dev/null || echo "$MEM_FREE_KB")
  MEM_BUFFERS_KB=$(awk '/Buffers:/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)
  MEM_CACHED_KB=$(awk '/^Cached:/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)
  SWAP_TOTAL_KB=$(awk '/SwapTotal:/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)
  SWAP_USED_KB=$(( SWAP_TOTAL_KB - $(awk '/SwapFree:/ {print $2}' /proc/meminfo 2>/dev/null || echo 0) ))
  if (( SWAP_USED_KB < 0 )); then SWAP_USED_KB=0; fi

  # approx used = total - avail (or total - free - buff - cached)
  local used
  used=$(( MEM_TOTAL_KB - MEM_AVAIL_KB ))
  if (( used < 0 )); then used=0; fi
  MEM_USED_KB="$used"

  # PSI mem
  if [[ -r /proc/pressure/memory ]]; then
    MEM_PSI_SOME=$(awk '/^some/ {print $2" "$3" "$4}' /proc/pressure/memory 2>/dev/null | tr ' ' '\n' | awk -F= 'NR==1{print $2} NR==2{print $2} NR==3{print $2}' | paste -sd/ - || echo 'n/a')
    MEM_PSI_FULL=$(awk '/^full/ {print $2" "$3" "$4}' /proc/pressure/memory 2>/dev/null | tr ' ' '\n' | awk -F= 'NR==1{print $2} NR==2{print $2} NR==3{print $2}' | paste -sd/ - || echo 'n/a')
  else
    MEM_PSI_SOME="n/a"
    MEM_PSI_FULL="n/a"
  fi
}

# PSI cpu and io
read_pressure() {
  CPU_PSI_SOME="n/a"
  CPU_PSI_FULL="n/a"
  IO_PSI_SOME="n/a"
  IO_PSI_FULL="n/a"
  if [[ -r /proc/pressure/cpu ]]; then
    CPU_PSI_SOME=$(awk '/^some/ {gsub(/avg10=/,"",$2); gsub(/avg60=/,"",$3); gsub(/avg300=/,"",$4); print $2"/"$3"/"$4}' /proc/pressure/cpu 2>/dev/null || echo 'n/a')
    CPU_PSI_FULL=$(awk '/^full/ {gsub(/avg10=/,"",$2); gsub(/avg60=/,"",$3); gsub(/avg300=/,"",$4); print $2"/"$3"/"$4}' /proc/pressure/cpu 2>/dev/null || echo 'n/a')
  fi
  if [[ -r /proc/pressure/io ]]; then
    IO_PSI_SOME=$(awk '/^some/ {gsub(/avg10=/,"",$2); gsub(/avg60=/,"",$3); gsub(/avg300=/,"",$4); print $2"/"$3"/"$4}' /proc/pressure/io 2>/dev/null || echo 'n/a')
    IO_PSI_FULL=$(awk '/^full/ {gsub(/avg10=/,"",$2); gsub(/avg60=/,"",$3); gsub(/avg300=/,"",$4); print $2"/"$3"/"$4}' /proc/pressure/io 2>/dev/null || echo 'n/a')
  fi
}

# Disk: use df -hT, filter tmpfs/devtmpfs/efivarfs
read_disk() {
  DISK_ENTRIES=()
  local line
  while IFS= read -r line; do
    # skip header
    [[ "$line" =~ ^Filesystem ]] && continue
    local fs type size used avail pcent mount
    # df -hT output columns: Filesystem Type Size Used Avail Use% Mounted on
    read -r fs type size used avail pcent mount <<< "$line"
    [[ -z "$mount" ]] && continue
    if [[ "$type" =~ ^(tmpfs|devtmpfs|efivarfs)$ ]]; then
      continue
    fi
    # clean pcent
    pcent="${pcent%%%}"
    DISK_ENTRIES+=("$mount|$used|$size|$pcent|$type")
  done < <(df -hT 2>/dev/null | cat)
}

# Network: /proc/net/dev + ip
read_netdev() {
  NET_ENTRIES=()
  NET_IPV4=""
  NET_GW=""
  local line
  # parse /proc/net/dev using awk for reliability (rx:2-9, tx:10-17 after iface:)
  while IFS= read -r line; do
    [[ "$line" =~ ^[[:space:]]*Inter- ]] && continue
    [[ "$line" =~ ^[[:space:]]*face ]] && continue
    local parsed
    parsed=$(echo "$line" | awk '
      {
        iface=$1; sub(/:$/,"",iface);
        rx_b=$2; rx_p=$3; rx_e=$4; rx_d=$5;
        tx_b=$10; tx_p=$11; tx_e=$12; tx_d=$13;
        print iface "|" rx_b "|" tx_b "|" rx_p "|" tx_p "|" rx_e "|" rx_d "|" tx_e "|" tx_d
      }' )
    if [[ -n "$parsed" ]]; then
      NET_ENTRIES+=("$parsed")
    fi
  done < <(cat /proc/net/dev 2>/dev/null)

  # IPv4 public-ish + gw
  NET_IPV4=$(ip -4 -o addr show scope global 2>/dev/null | awk '{print $4}' | head -1 | cut -d/ -f1 || echo '')
  NET_GW=$(ip route 2>/dev/null | awk '/^default/ {print $3; exit}' || echo '')
}

# Procs: top N cpu and top N mem
read_procs() {
  PROCS_CPU=()
  PROCS_MEM=()
  local topn="${1:-8}"
  local line
  # CPU top (skip header)
  local count=0
  while IFS= read -r line; do
    [[ "$line" =~ ^[[:space:]]*PID ]] && continue
    [[ -z "$line" ]] && continue
    # pid user pcpu pmem etime comm (comm may have spaces but last field)
    local pid user pcpu pmem etime comm
    read -r pid user pcpu pmem etime comm <<< "$line"
    [[ -z "$pid" ]] && continue
    # sanitize comm to first word if multi
    comm="${comm%% *}"
    PROCS_CPU+=("$pid|$user|$pcpu|$pmem|$etime|$comm")
    count=$((count+1))
    (( count >= topn )) && break
  done < <(ps -eo pid,user,pcpu,pmem,etime,comm --sort=-pcpu 2>/dev/null | tail -n +2)

  # MEM top (independent sort)
  count=0
  while IFS= read -r line; do
    [[ "$line" =~ ^[[:space:]]*PID ]] && continue
    [[ -z "$line" ]] && continue
    local pid user pcpu pmem etime comm
    read -r pid user pcpu pmem etime comm <<< "$line"
    comm="${comm%% *}"
    PROCS_MEM+=("$pid|$user|$pcpu|$pmem|$etime|$comm")
    count=$((count+1))
    (( count >= topn )) && break
  done < <(ps -eo pid,user,pcpu,pmem,etime,comm --sort=-pmem 2>/dev/null | tail -n +2)
}

# Services: counts + failed list
read_services() {
  SVC_ACTIVE=""
  SVC_FAILED=""
  SVC_FAILED_LIST=()
  if ! command -v systemctl >/dev/null 2>&1; then
    SVC_ACTIVE="n/a"
    SVC_FAILED="n/a"
    return
  fi
  local active failed
  active=$(systemctl list-units --type=service --state=running --no-legend --no-pager 2>/dev/null | wc -l | tr -d ' ')
  failed=$(systemctl list-units --type=service --state=failed --no-legend --no-pager 2>/dev/null | wc -l | tr -d ' ')
  SVC_ACTIVE="${active:-0}"
  SVC_FAILED="${failed:-0}"
  if (( ${failed:-0} > 0 )); then
    while IFS= read -r u; do
      [[ -z "$u" ]] && continue
      local name
      name="$(echo "$u" | awk '{print $1}')"
      [[ -n "$name" ]] && SVC_FAILED_LIST+=("$name")
    done < <(systemctl list-units --type=service --state=failed --no-legend --no-pager 2>/dev/null | head -5)
  fi
}

# Collect all
collect_all() {
  read_host
  read_uptime
  read_loadavg
  read_proc_stat
  read_meminfo
  read_pressure
  read_disk
  read_netdev
  read_procs "${TOP_N:-8}"
  read_services
}

# Text render helpers (use colors if enabled)
render_header() {
  printf '%s\n' "$(colorize "=== VPS STATUS ===" ok)"
  printf 'host: %s  kernel: %s  os: %s\n' \
    "$(colorize "$HOSTNAME" ok)" "$KERNEL" "$OS_PRETTY"
  printf 'uptime: %s  (%.0fs)  boot: %s  snapshot: %s\n' \
    "$UPTIME_PRETTY" "$UPTIME_S" "$BOOT_AT" "$SNAPSHOT_AT"
}

render_cpu() {
  local load_warn=$(( NPROC ))
  local load_crit=$(( NPROC * 2 ))
  printf '%s\n' "$(colorize "=== CPU ===" ok)"
  local total_col
  total_col=$(color_pct "$CPU_TOTAL_PCT" 70 90)
  printf 'total: %s%%   ' "$total_col"
  local bar
  bar=$(make_bar "$CPU_TOTAL_PCT" 8)
  printf '%s\n' "$(colorize "$bar" "$(awk "BEGIN {if ($CPU_TOTAL_PCT>=90) print \"crit\"; else if ($CPU_TOTAL_PCT>=70) print \"warn\"; else print \"ok\"}")")"

  printf 'cores: '
  local i=0 c
  for c in "${CPU_CORES_PCT[@]:-}"; do
    [[ -z "$c" ]] && continue
    printf 'c%s:%s%% ' "$i" "$(color_pct "$c" 70 90)"
    i=$((i+1))
  done
  printf '\n'

  local lcol
  lcol=$(colorize "$LOAD_1 $LOAD_5 $LOAD_15" ok)
  if awk "BEGIN {exit !($LOAD_1 >= $load_crit)}"; then
    lcol=$(colorize "$LOAD_1 $LOAD_5 $LOAD_15" crit)
  elif awk "BEGIN {exit !($LOAD_1 >= $load_warn)}"; then
    lcol=$(colorize "$LOAD_1 $LOAD_5 $LOAD_15" warn)
  fi
  printf 'load: %s (nproc=%s)\n' "$lcol" "$NPROC"

  printf 'psi cpu: some=%s full=%s\n' "$CPU_PSI_SOME" "$CPU_PSI_FULL"
}

render_memory() {
  printf '%s\n' "$(colorize "=== MEMORY ===" ok)"
  local used_pct=0
  if (( MEM_TOTAL_KB > 0 )); then
    used_pct=$(awk "BEGIN {printf \"%.1f\", $MEM_USED_KB * 100.0 / $MEM_TOTAL_KB}")
  fi
  printf 'total: %s kB  used: %s (%s%%)  avail: %s  buff/cache: %s\n' \
    "$MEM_TOTAL_KB" "$MEM_USED_KB" "$(color_pct "$used_pct" 80 95)" "$MEM_AVAIL_KB" "$((MEM_BUFFERS_KB + MEM_CACHED_KB))"
  if (( SWAP_TOTAL_KB > 0 )); then
    local swap_pct
    swap_pct=$(awk "BEGIN {printf \"%.1f\", $SWAP_USED_KB * 100.0 / $SWAP_TOTAL_KB}")
    printf 'swap: total %s used %s (%s%%)\n' "$SWAP_TOTAL_KB" "$SWAP_USED_KB" "$(color_pct "$swap_pct" 80 95)"
  else
    printf 'swap: none\n'
  fi
  printf 'psi mem: some=%s full=%s\n' "$MEM_PSI_SOME" "$MEM_PSI_FULL"
}

render_disk() {
  printf '%s\n' "$(colorize "=== DISK ===" ok)"
  local entry
  for entry in "${DISK_ENTRIES[@]:-}"; do
    local mount used size pct type
    IFS='|' read -r mount used size pct type <<< "$entry"
    local col
    col=$(color_pct "$pct" 80 95)
    printf '%-12s %3s%%  %s/%s  %s\n' "$mount" "$col" "$used" "$size" "$type"
  done
  printf 'psi io: some=%s full=%s\n' "$IO_PSI_SOME" "$IO_PSI_FULL"
}

render_net() {
  printf '%s\n' "$(colorize "=== NETWORK ===" ok)"
  local entry
  for entry in "${NET_ENTRIES[@]:-}"; do
    local iface rx tx rxp txp err drop txerr txdrop
    IFS='|' read -r iface rx tx rxp txp err drop txerr txdrop <<< "$entry"
    # human bytes rough
    local rxh txh
    rxh=$(awk "BEGIN {b=$rx; if (b>1024*1024*1024) printf \"%.1fG\", b/1024/1024/1024; else if (b>1024*1024) printf \"%.1fM\", b/1024/1024; else printf \"%.0fK\", b/1024}")
    txh=$(awk "BEGIN {b=$tx; if (b>1024*1024*1024) printf \"%.1fG\", b/1024/1024/1024; else if (b>1024*1024) printf \"%.1fM\", b/1024/1024; else printf \"%.0fK\", b/1024}")
    printf '%-6s rx:%s(%s) tx:%s(%s) rx_err/drop:%s/%s tx_err/drop:%s/%s\n' "$iface" "$rxh" "$rxp" "$txh" "$txp" "$err" "$drop" "$txerr" "$txdrop"
  done
  printf 'ipv4: %s  gw: %s\n' "$NET_IPV4" "$NET_GW"
}

render_procs() {
  local n="${1:-8}"
  printf '%s\n' "$(colorize "=== PROCS (top $n CPU) ===" ok)"
  printf '%-6s %-8s %6s %6s %10s %s\n' PID USER CPU% MEM% ELAPSED CMD
  local p
  for p in "${PROCS_CPU[@]:0:$n}"; do
    local pid user pcpu pmem etime comm
    IFS='|' read -r pid user pcpu pmem etime comm <<< "$p"
    printf '%-6s %-8s %6s %6s %10s %s\n' "$pid" "$user" "$pcpu" "$pmem" "$etime" "$comm"
  done
  printf '%s\n' "$(colorize "=== PROCS (top $n MEM) ===" ok)"
  printf '%-6s %-8s %6s %6s %10s %s\n' PID USER CPU% MEM% ELAPSED CMD
  for p in "${PROCS_MEM[@]:0:$n}"; do
    local pid user pcpu pmem etime comm
    IFS='|' read -r pid user pcpu pmem etime comm <<< "$p"
    printf '%-6s %-8s %6s %6s %10s %s\n' "$pid" "$user" "$pcpu" "$pmem" "$etime" "$comm"
  done
}

render_services() {
  printf '%s\n' "$(colorize "=== SERVICES ===" ok)"
  local failcol actcol
  if (( ${SVC_FAILED:-0} > 0 )); then
    failcol=$(colorize "$SVC_FAILED" crit)
  else
    failcol=$(colorize "$SVC_FAILED" ok)
  fi
  actcol=$(colorize "$SVC_ACTIVE" ok)
  printf 'active: %s  failed: %s\n' "$actcol" "$failcol"
  if (( ${#SVC_FAILED_LIST[@]} > 0 )); then
    printf 'failed: %s\n' "$(colorize "${SVC_FAILED_LIST[*]}" crit)"
  fi
}

render_uptime() {
  # already in header mostly
  printf 'uptime: %s  boot_at: %s  snapshot: %s\n' "$UPTIME_PRETTY" "$BOOT_AT" "$SNAPSHOT_AT"
}

# Build JSON (manual, compact-ish but readable)
build_json() {
  local out="{"
  out+="\"host\":{"
  out+="\"hostname\":\"$(json_escape "$HOSTNAME")\","
  out+="\"kernel\":\"$(json_escape "$KERNEL")\","
  out+="\"os\":\"$(json_escape "$OS_PRETTY")\","
  out+="\"snapshot_at\":\"$(json_escape "$SNAPSHOT_AT")\""
  out+="},"

  out+="\"cpu\":{"
  out+="\"total_pct\":$CPU_TOTAL_PCT,"
  out+="\"cores\":[$(IFS=,; echo "${CPU_CORES_PCT[*]}")],"
  out+="\"load\":{\"1\":$LOAD_1,\"5\":$LOAD_5,\"15\":$LOAD_15,\"nproc\":$NPROC},"
  out+="\"psi\":{\"cpu_some\":\"$CPU_PSI_SOME\",\"cpu_full\":\"$CPU_PSI_FULL\"}"
  out+="},"

  out+="\"memory\":{"
  out+="\"total_kb\":$MEM_TOTAL_KB,"
  out+="\"used_kb\":$MEM_USED_KB,"
  out+="\"avail_kb\":$MEM_AVAIL_KB,"
  out+="\"buffers_kb\":$MEM_BUFFERS_KB,"
  out+="\"cached_kb\":$MEM_CACHED_KB,"
  out+="\"swap_total_kb\":$SWAP_TOTAL_KB,"
  out+="\"swap_used_kb\":$SWAP_USED_KB,"
  out+="\"psi\":{\"mem_some\":\"$MEM_PSI_SOME\",\"mem_full\":\"$MEM_PSI_FULL\"}"
  out+="},"

  out+="\"disk\":["
  local first=1
  local d
  for d in "${DISK_ENTRIES[@]:-}"; do
    local m u s p t
    IFS='|' read -r m u s p t <<< "$d"
    [[ $first -eq 0 ]] && out+=","
    out+="{\"mount\":\"$(json_escape "$m")\",\"used\":\"$u\",\"size\":\"$s\",\"pct\":$p,\"type\":\"$t\"}"
    first=0
  done
  out+="],"

  out+="\"net\":["
  first=1
  for d in "${NET_ENTRIES[@]:-}"; do
    local i rx tx rxp txp e dr te td
    IFS='|' read -r i rx tx rxp txp e dr te td <<< "$d"
    [[ $first -eq 0 ]] && out+=","
    out+="{\"iface\":\"$i\",\"rx_bytes\":$rx,\"tx_bytes\":$tx,\"rx_packets\":$rxp,\"tx_packets\":$txp,\"rx_err\":$e,\"rx_drop\":$dr,\"tx_err\":${te:-0},\"tx_drop\":${td:-0}}"
    first=0
  done
  out+="],"

  out+="\"processes\":{"
  out+="\"cpu\":["
  first=1
  local pr
  for pr in "${PROCS_CPU[@]:-}"; do
    local pid u pc pm et c
    IFS='|' read -r pid u pc pm et c <<< "$pr"
    [[ $first -eq 0 ]] && out+=","
    out+="{\"pid\":$pid,\"user\":\"$(json_escape "$u")\",\"pcpu\":$pc,\"pmem\":$pm,\"etime\":\"$et\",\"comm\":\"$(json_escape "$c")\"}"
    first=0
  done
  out+="],\"mem\":["
  first=1
  for pr in "${PROCS_MEM[@]:-}"; do
    local pid u pc pm et c
    IFS='|' read -r pid u pc pm et c <<< "$pr"
    [[ $first -eq 0 ]] && out+=","
    out+="{\"pid\":$pid,\"user\":\"$(json_escape "$u")\",\"pcpu\":$pc,\"pmem\":$pm,\"etime\":\"$et\",\"comm\":\"$(json_escape "$c")\"}"
    first=0
  done
  out+="]},"

  out+="\"psi\":{"
  out+="\"cpu_some\":\"$CPU_PSI_SOME\",\"cpu_full\":\"$CPU_PSI_FULL\","
  out+="\"mem_some\":\"$MEM_PSI_SOME\",\"mem_full\":\"$MEM_PSI_FULL\","
  out+="\"io_some\":\"$IO_PSI_SOME\",\"io_full\":\"$IO_PSI_FULL\""
  out+="},"

  # Services: emit "n/a" (quoted) when systemctl missing, else numeric.
  local svc_active_val svc_failed_val
  if [[ "${SVC_ACTIVE:-}" == "n/a" ]]; then
    svc_active_val='"n/a"'
  else
    svc_active_val="${SVC_ACTIVE:-0}"
  fi
  if [[ "${SVC_FAILED:-}" == "n/a" ]]; then
    svc_failed_val='"n/a"'
  else
    svc_failed_val="${SVC_FAILED:-0}"
  fi
  out+="\"services\":{\"active\":$svc_active_val,\"failed\":$svc_failed_val,\"failed_list\":["
  first=1
  for f in "${SVC_FAILED_LIST[@]:-}"; do
    [[ -z "$f" ]] && continue
    [[ $first -eq 0 ]] && out+=","
    out+="\"$(json_escape "$f")\""
    first=0
  done
  out+="]},"

  out+="\"uptime_s\":$UPTIME_S,"
  out+="\"boot_at\":\"$(json_escape "$BOOT_AT")\""
  out+="}"
  printf '%s' "$out"
}

# For section json sub
get_section_json() {
  local sec="$1"
  case "$sec" in
    cpu)  printf '%s' "$(build_json | python3 -c '
import sys,json
d=json.load(sys.stdin)
print(json.dumps(d.get("cpu", {})))
' 2>/dev/null || echo '{}')" ;;
    mem|memory) printf '%s' "$(build_json | python3 -c '
import sys,json
d=json.load(sys.stdin)
print(json.dumps(d.get("memory", {})))
' 2>/dev/null || echo '{}')" ;;
    disk) printf '%s' "$(build_json | python3 -c '
import sys,json
d=json.load(sys.stdin)
print(json.dumps(d.get("disk", [])))
' 2>/dev/null || echo '[]')" ;;
    net)  printf '%s' "$(build_json | python3 -c '
import sys,json
d=json.load(sys.stdin)
print(json.dumps(d.get("net", [])))
' 2>/dev/null || echo '[]')" ;;
    procs|processes) printf '%s' "$(build_json | python3 -c '
import sys,json
d=json.load(sys.stdin)
print(json.dumps(d.get("processes", {})))
' 2>/dev/null || echo '{}')" ;;
    psi)  printf '%s' "$(build_json | python3 -c '
import sys,json
d=json.load(sys.stdin)
print(json.dumps(d.get("psi", {})))
' 2>/dev/null || echo '{}')" ;;
    svc|services) printf '%s' "$(build_json | python3 -c '
import sys,json
d=json.load(sys.stdin)
print(json.dumps(d.get("services", {})))
' 2>/dev/null || echo '{}')" ;;
    uptime) printf '%s' "$(build_json | python3 -c '
import sys,json
d=json.load(sys.stdin)
print(json.dumps({"uptime_s": d.get("uptime_s"), "boot_at": d.get("boot_at")}))
' 2>/dev/null || echo '{}')" ;;
    *) build_json ;;
  esac
}
