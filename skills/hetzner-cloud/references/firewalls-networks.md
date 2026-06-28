# Firewalls and networks

## Firewalls

List and inspect:

```bash
bin/hcloud-cli firewall list --json
bin/hcloud-cli firewall get my-fw --json
```

Create with rules file (JSON array):

```json
[
  {
    "direction": "in",
    "protocol": "tcp",
    "port": "22",
    "source_ips": ["0.0.0.0/0", "::/0"],
    "description": "SSH"
  },
  {
    "direction": "in",
    "protocol": "tcp",
    "port": "443",
    "source_ips": ["0.0.0.0/0", "::/0"],
    "description": "HTTPS"
  }
]
```

```bash
bin/hcloud-cli firewall create web-fw --rules-file rules.json
bin/hcloud-cli firewall apply web-fw my-server
```

Delete: `bin/hcloud-cli firewall delete web-fw --yes`

## Private networks

```bash
bin/hcloud-cli network create internal 10.0.0.0/16 --json
bin/hcloud-cli network add-subnet internal 10.0.1.0/24 --network-zone eu-central
bin/hcloud-cli network add-route internal 0.0.0.0/0 10.0.0.1
```

Attach server to network via Hetzner API/console or server create options (see hcloud docs for `networks` parameter on create).

## Floating IPs

```bash
bin/hcloud-cli floating-ip create --type ipv4 --home-location fsn1 --name web-ip --json
bin/hcloud-cli floating-ip assign web-ip my-server
bin/hcloud-cli floating-ip unassign web-ip
```

## Mail ports note

Hetzner blocks outbound TCP/25 on new cloud servers by default. Request unblock via support before running mailcow SMTP. Inbound 25/587/993/443 still need firewall rules if using Hetzner Cloud Firewall.
