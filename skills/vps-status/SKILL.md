---
name: vps-status
description: "Compact color-coded Ubuntu VPS status (CPU/mem/disk/net/procs/PSI/services) with --json/--section/--watch. Read-only, no sudo."
metadata:
  {
    "openclaw":
      {
        "emoji": "🖥️"
      },
  }
---

# vps-status

Read-only local Ubuntu/Linux VPS resource snapshot in the style of `top`/`glances` (but using only safe /proc + coreutils).

## When to use
- Quick on-host health check or baseline for the VPS itself.
- In scripts or from `healthcheck` skill as a fast read-only step (`vps-status --json`).
- Interactive diagnosis of high CPU/load/memory/disk without installing glances or sensors.
- Periodic via `--watch` for live view during incidents.

## When NOT to use
- Remote hosts (ssh + this or use Prometheus/grafana for that).
- Long-term metrics storage or trending (use proper monitoring stack).
- When you need temperatures/sensors (no `sensors`; fails gracefully).
- Container/Docker discovery (out of scope on this host).
- Anything requiring writes, sudo, or network egress.

## CLI
```bash
bin/vps-status [options]
```

### Options
- `--json` — full (or section-filtered) JSON on stdout.
- `--section=NAME` — cpu|mem|disk|net|procs|psi|uptime|svc|all (default: all).
- `--top N` — top-N processes (default 8).
- `--no-color` — force plain text (also respects NO_COLOR and non-TTY).
- `--watch=SEC` — repeat every N seconds (Ctrl-C stops).
- `-h|--help`

### Exit codes
- 0: success / report produced
- 1: bad args or hard failure

### Output (text)
Color-coded (green=ok, yellow=warn, red=crit) with thresholds:
- CPU >70%/90%, mem>80%/95%, disk>80%/95%, load >nproc / >2*nproc, failed services.

Always includes header (hostname, kernel, OS, uptime, boot, snapshot).

### JSON structure
```json
{
  "host": {"hostname": "...", "kernel": "...", "os": "...", "snapshot_at": "..."},
  "cpu": {"total_pct": 12.3, "cores": [..], "load": {...}, "psi": {...}},
  "memory": {...},
  "disk": [{"mount": "/", "used": "4.7G", "size": "75G", "pct": 7, "type": "ext4"}, ...],
  "net": [...],
  "processes": {"cpu": [...], "mem": [...]},
  "psi": {...},
  "services": {"active": 26, "failed": 0, "failed_list": []},
  "uptime_s": 363709,
  "boot_at": "2026-..."
}
```

## Security & behavior
- **Read-only**: only reads /proc/*, /etc/os-release, runs `ps` `df` `ip` `systemctl` (user-visible units) `nproc` etc.
- Never requires sudo. Runs as root or unprivileged (limited systemctl output on non-root is handled gracefully).
- Fails gracefully: missing files/bins/data → "n/a", partial report, exit 0 where possible.
- Idempotent within sample window.
- No network, no secrets, no writes, no config changes.

## Examples
```bash
./bin/vps-status --section=cpu --no-color
./bin/vps-status --json | python3 -m json.tool
./bin/vps-status --top 3 --watch=2
```

## Integration
`skills/healthcheck` (or any orchestrator) can invoke `bin/vps-status --json` for a fast, local baseline step. No side effects.

## Requirements (runtime)
Only standard on Ubuntu: bash, cat, awk, ps (procps), df, ip, systemctl (for svc), nproc. No glances, no python required for normal use.
