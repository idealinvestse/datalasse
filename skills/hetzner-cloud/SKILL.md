---
name: hetzner-cloud
description: "Manage Hetzner Cloud via hcloud-python: DNS zones/records, servers, volumes, firewalls, networks, rDNS. Supports multiple Hetzner Cloud projects via --project flag."
metadata:
  {
    "openclaw":
      {
        "emoji": "☁️",
        "requires": { "bins": ["python3"], "env": ["HCLOUD_TOKEN"] },
        "primaryEnv": "HCLOUD_PROJECT_NAME",
      },
  }
---

# Hetzner Cloud

Manage Hetzner Cloud resources from the workspace using the official `hcloud` Python library. Prefer the bundled CLI for deterministic JSON output and safety gates. Supports **multiple Hetzner Cloud projects** (each API token is bound to one project).

## Setup

```bash
cd skills/hetzner-cloud
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Option A — multi-project registry (recommended)
cat > ~/.config/moss/hcloud-projects.env <<EOF
HCLOUD_PROJECT_DNS='...'      # intelliserve-prod (DNS zones)
HCLOUD_PROJECT_VPS='...'      # vps-agent-1 project (servers + rDNS)
HCLOUD_DEFAULT_PROJECT='dns'
EOF
chmod 600 ~/.config/moss/hcloud-projects.env

# Option B — legacy single-token mode
export HCLOUD_TOKEN="..."     # Hetzner Cloud Console → Security → API tokens
export HCLOUD_DEFAULT_ZONE=intelliserve.se
```

Or use `bin/hcloud-cli` (auto-uses `.venv` when present).

## Multi-project usage

Each Hetzner Cloud API token is bound to **one project** (per Hetzner docs). To target different projects:

```bash
CLI=skills/hetzner-cloud/bin/hcloud-cli

# Explicit — most common
$CLI --project=dns zone list --json
$CLI --project=vps server list --json

# Or via env var (one-shot)
HCLOUD_PROJECT_NAME=vps $CLI server list

# Default project (from HCLOUD_DEFAULT_PROJECT) used when --project omitted
$CLI status --json
# → { "authenticated": true, "project": "dns", "zones": 8, "servers": 0, ... }

# See what's available
$CLI status --json | jq '.available_projects'
# → ["dns", "vps"]
```

## Quick start

```bash
CLI=skills/hetzner-cloud/bin/hcloud-cli

# Auth + inventory
$CLI status --json
$CLI zone list --json
$CLI server list --json

# DNS (mailcow / intelliserve.se) — default project
$CLI record list --zone intelliserve.se --json
$CLI record set --zone intelliserve.se --name mail --type A --value 167.233.38.175
$CLI record set --zone intelliserve.se --name @ --type MX --value "10 mail.intelliserve.se"
$CLI record add  --zone intelliserve.se --name @ --type TXT --value "v=spf1 mx ~all"

# Reverse DNS for mail — vps project (owns the server)
$CLI --project=vps server rdns set vps-agent-1 --ip 167.233.38.175 --ptr mail.intelliserve.se
```

## CLI reference

Global flags: `--json`, `--yes`, `--dry-run`, `--zone <name>`, `--project <name>`.

| Group | Commands |
|-------|----------|
| Core | `status` (shows active project + available_projects) |
| DNS zones | `zone list\|get\|create\|delete\|export\|import` |
| DNS records | `record list\|get\|create\|set\|add\|remove\|delete` |
| Servers | `server list\|get\|create\|delete\|poweron\|poweroff\|reboot\|resize` |
| rDNS | `server rdns get\|set\|reset <name>` |
| Volumes | `volume list\|get\|create\|attach\|detach\|delete\|resize` |
| Firewalls | `firewall list\|get\|create\|apply\|delete` |
| Networks | `network list\|get\|create\|delete\|add-subnet\|add-route` |
| SSH keys | `ssh-key list\|get\|create\|delete` |
| Floating IPs | `floating-ip list\|get\|create\|assign\|unassign\|delete` |
| Helpers | `image [name]`, `type` |

Record flags: `--name` (use `@` for apex), `--type`, `--value` (repeatable), `--ttl`, `--force` (SOA/NS).

Server create: `--type cx23 --image ubuntu-24.04 --location fsn1 --ssh-key mykey`.

## Safety

- Destructive ops require `--yes` (`zone delete`, `record delete`, `server delete`, etc.).
- `--dry-run` prints intent without API writes.
- SOA/NS records need `--force` to modify/delete.
- Never commit tokens. Store in `~/.config/moss/hcloud-projects.env` (mode 600) or `openclaw.json` `env.vars`.
- Confirm before bulk DNS changes; prefer `record list` first.
- Multi-project: a wrong `--project` will silently 404 on resources that exist in another project. `status` shows the active project + token length to make this obvious.

## JSON output

Success: `{"ok": true, "data": ...}`. Failure: `{"ok": false, "error": "...", "hint": "..."}`.

## When to use

- DNS for domains hosted in Hetzner DNS (mailcow SPF/DKIM/DMARC, A/MX/CNAME).
- VPS lifecycle on Hetzner Cloud (same host or additional servers).
- rDNS/PTR for outbound mail reputation.
- Firewalls, private networks, volumes, floating IPs.
- Multiple Hetzner Cloud projects (org has separate prod/staging/dev, or DNS on one project + servers on another).

## Deep dives

- `references/dns-records.md` — RRSet naming, mailcow checklist, DKIM >255 char split
- `references/servers-volumes.md` — create/attach, rDNS, multi-project rDNS
- `references/firewalls-networks.md` — firewall rules JSON, subnets/routes
