---
name: hetzner-cloud
description: "Manage Hetzner Cloud via hcloud-python: DNS zones/records, servers, volumes, firewalls, networks, rDNS."
metadata:
  {
    "openclaw":
      {
        "emoji": "☁️",
        "requires": { "bins": ["python3"], "env": ["HCLOUD_TOKEN"] },
        "primaryEnv": "HCLOUD_TOKEN",
      },
  }
---

# Hetzner Cloud

Manage Hetzner Cloud resources from the workspace using the official `hcloud` Python library. Prefer the bundled CLI for deterministic JSON output and safety gates.

## Setup

```bash
cd skills/hetzner-cloud
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export HCLOUD_TOKEN="..."          # Hetzner Cloud Console → Security → API tokens
export HCLOUD_DEFAULT_ZONE=intelliserve.se   # optional default for DNS commands
```

Or use `bin/hcloud-cli` (auto-uses `.venv` when present).

## Quick start

```bash
CLI=skills/hetzner-cloud/bin/hcloud-cli

# Auth + inventory
$CLI status --json
$CLI zone list --json
$CLI server list --json

# DNS (mailcow / intelliserve.se)
$CLI record list --zone intelliserve.se --json
$CLI record set --zone intelliserve.se --name mail --type A --value 167.233.38.175
$CLI record set --zone intelliserve.se --name @ --type MX --value "10 mail.intelliserve.se"
$CLI record add  --zone intelliserve.se --name @ --type TXT --value "v=spf1 mx ~all"

# Reverse DNS for mail
$CLI server rdns set vps-agent-1 --ip 167.233.38.175 --ptr mail.intelliserve.se
```

## CLI reference

Global flags: `--json`, `--yes`, `--dry-run`, `--zone <name>`.

| Group | Commands |
|-------|----------|
| Core | `status` |
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
- Never commit `HCLOUD_TOKEN`. Store in `openclaw.json` `env.vars` or export inline.
- Confirm before bulk DNS changes; prefer `record list` first.

## JSON output

Success: `{"ok": true, "data": ...}`. Failure: `{"ok": false, "error": "...", "hint": "..."}`.

## When to use

- DNS for domains hosted in Hetzner DNS (mailcow SPF/DKIM/DMARC, A/MX/CNAME).
- VPS lifecycle on Hetzner Cloud (same host or additional servers).
- rDNS/PTR for outbound mail reputation.
- Firewalls, private networks, volumes, floating IPs.

## Deep dives

- `references/dns-records.md` — RRSet naming, mailcow checklist
- `references/servers-volumes.md` — create/attach, rDNS
- `references/firewalls-networks.md` — firewall rules JSON, subnets/routes
