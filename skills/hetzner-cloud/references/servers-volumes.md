# Servers and volumes

## List / inspect

```bash
bin/hcloud-cli server list --json
bin/hcloud-cli server get vps-agent-1 --json
bin/hcloud-cli type --json | jq '.data[] | select(.name|test("cx|cpx"))'
bin/hcloud-cli image ubuntu --json
```

## Create server

```bash
bin/hcloud-cli server create my-app \
  --type cx23 \
  --image ubuntu-24.04 \
  --location fsn1 \
  --ssh-key my-laptop \
  --json
```

- `--location`: `fsn1`, `nbg1`, `hel1`, etc.
- `--image`: name or numeric ID.
- `--no-start` to create stopped.
- Root password printed to stderr on create (capture securely).

## Power / resize

```bash
bin/hcloud-cli server poweroff my-app
bin/hcloud-cli server poweron my-app
bin/hcloud-cli server reboot my-app
bin/hcloud-cli server resize my-app --type cpx31 --upgrade-disk --yes
```

## Reverse DNS (PTR)

Required for mail deliverability when sending from the VPS IP.

```bash
bin/hcloud-cli server rdns get vps-agent-1 --json
bin/hcloud-cli server rdns set vps-agent-1 --ip 167.233.38.175 --ptr mail.intelliserve.se
bin/hcloud-cli server rdns reset vps-agent-1 --ip 167.233.38.175 --yes
```

## Volumes

```bash
bin/hcloud-cli volume create data-vol 10 fsn1 --json
bin/hcloud-cli volume attach data-vol my-app --automount
bin/hcloud-cli volume detach data-vol
bin/hcloud-cli volume resize data-vol 20 --yes
```

## Delete

Always `--dry-run` then `--yes`:

```bash
bin/hcloud-cli server delete old-box --dry-run
bin/hcloud-cli server delete old-box --yes
```
