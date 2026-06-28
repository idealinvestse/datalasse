#!/usr/bin/env python3
"""Hetzner Cloud CLI for OpenClaw hetzner-cloud skill."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from hcloud.firewalls.domain import FirewallRule  # noqa: E402
from hcloud.images import Image  # noqa: E402
from hcloud.locations import Location  # noqa: E402
from hcloud.networks.domain import NetworkSubnet, NetworkRoute  # noqa: E402
from hcloud.server_types import ServerType  # noqa: E402
from hcloud.firewalls.domain import FirewallResource  # noqa: E402
from hcloud.zones.domain import ZoneRecord  # noqa: E402

from _common import (  # noqa: E402
    OPTS,
    PROTECTED_RR_TYPES,
    CliError,
    action_to_dict,
    dry_run_payload,
    emit_error,
    emit_ok,
    firewall_to_dict,
    floating_ip_to_dict,
    get_client,
    get_token,
    image_to_dict,
    list_projects,
    network_to_dict,
    normalize_record_name,
    require_yes,
    resolve_firewall,
    resolve_floating_ip,
    resolve_network,
    resolve_server,
    resolve_ssh_key,
    resolve_volume,
    resolve_zone,
    rrset_to_dict,
    server_to_dict,
    server_type_to_dict,
    ssh_key_to_dict,
    volume_to_dict,
    wait_action,
    zone_name,
    zone_to_dict,
)


def _add_globals(p: argparse.ArgumentParser) -> None:
    p.add_argument("--json", action="store_true", help="JSON output")
    p.add_argument("--yes", action="store_true", help="Confirm destructive operations")
    p.add_argument("--dry-run", action="store_true", help="Show intent without writes")
    p.add_argument("--zone", help="Default DNS zone (overrides HCLOUD_DEFAULT_ZONE)")
    p.add_argument(
        "--project",
        help=(
            "Hetzner Cloud project to target. Each project has its own API "
            "token (registered in ~/.config/moss/hcloud-projects.env). "
            "Overrides HCLOUD_PROJECT_NAME / HCLOUD_DEFAULT_PROJECT."
        ),
    )


def _parse_record_values(rtype: str, values: list[str]) -> list[ZoneRecord]:
    records = []
    for raw in values:
        # Hetzner DNS requires TXT record values to be fully wrapped in
        # double quotes — wrap automatically if not already quoted.
        if rtype.upper() == "TXT":
            if not (raw.startswith('"') and raw.endswith('"')):
                raw = f'"{raw}"'
        records.append(ZoneRecord(value=raw))
    return records


def _check_protected(rtype: str, force: bool) -> None:
    if rtype.upper() in PROTECTED_RR_TYPES and not force:
        raise CliError(
            f"Refusing to modify protected RR type {rtype.upper()} without --force",
        )


def cmd_status(_args: argparse.Namespace) -> None:
    token, project_name = get_token()
    client = get_client()
    zones = client.zones.get_all()
    servers = client.servers.get_all()
    emit_ok(
        {
            "authenticated": True,
            "project": project_name,
            "token_chars": len(token),
            "zones": len(zones),
            "servers": len(servers),
            "available_projects": list_projects(),
        }
    )


def cmd_zone(args: argparse.Namespace) -> None:
    client = get_client()
    action = args.zone_action

    if action == "list":
        zones = client.zones.get_all()
        emit_ok([zone_to_dict(z) for z in zones])
        return

    if action == "get":
        zone = resolve_zone(client, args.name)
        emit_ok(zone_to_dict(zone))
        return

    if action == "create":
        payload = {"name": args.name, "mode": args.mode, "ttl": args.ttl}
        if OPTS.dry_run:
            dry_run_payload({"action": "zone.create", **payload})
            return
        zone = client.zones.create(name=args.name, mode=args.mode, ttl=args.ttl)
        emit_ok(zone_to_dict(zone))
        return

    if action == "delete":
        zone = resolve_zone(client, args.name)
        if OPTS.dry_run:
            dry_run_payload({"action": "zone.delete", "name": zone.name})
            return
        require_yes(f"delete zone {zone.name}")
        client.zones.delete(zone)
        emit_ok({"deleted": zone.name})
        return

    if action == "export":
        zone = resolve_zone(client, args.name)
        result = client.zones.export_zonefile(zone)
        if OPTS.json_out:
            emit_ok({"zone": zone.name, "zonefile": result.zonefile})
        else:
            print(result.zonefile)
        return

    if action == "import":
        zone = resolve_zone(client, args.name)
        zonefile = Path(args.file).read_text(encoding="utf-8")
        if OPTS.dry_run:
            dry_run_payload({"action": "zone.import", "name": zone.name, "bytes": len(zonefile)})
            return
        require_yes(f"import zonefile into {zone.name} (replaces all RRSets)")
        action_result = client.zones.import_zonefile(zone, zonefile)
        emit_ok({"action": wait_action(action_result), "zone": zone.name})
        return

    raise CliError(f"Unknown zone action: {action}")


def cmd_record(args: argparse.Namespace) -> None:
    client = get_client()
    action = args.record_action
    zname = zone_name(args.zone)
    zone = resolve_zone(client, zname)
    rname = normalize_record_name(args.name) if args.name is not None else None
    rtype = args.type.upper() if args.type else None

    if action == "list":
        kwargs = {}
        if rname is not None:
            kwargs["name"] = rname
        if rtype:
            kwargs["type"] = [rtype]
        rrsets = client.zones.get_rrset_all(zone, **kwargs)
        emit_ok([rrset_to_dict(r) for r in rrsets])
        return

    if action == "get":
        if rname is None or not rtype:
            raise CliError("--name and --type required for record get")
        rrset = client.zones.get_rrset(zone, rname, rtype)
        emit_ok(rrset_to_dict(rrset))
        return

    if action in ("create", "set", "add", "remove"):
        if rname is None or not rtype:
            raise CliError("--name and --type required")
        if not args.value:
            raise CliError("At least one --value required")
        _check_protected(rtype, args.force)
        records = _parse_record_values(rtype, args.value)
        payload = {
            "zone": zname,
            "name": rname or "@",
            "type": rtype,
            "values": args.value,
            "ttl": args.ttl,
        }
        if OPTS.dry_run:
            dry_run_payload({"action": f"record.{action}", **payload})
            return

        if action == "create":
            try:
                client.zones.get_rrset(zone, rname, rtype)
                raise CliError(
                    "RRSet already exists; use record set/add instead",
                )
            except Exception:
                pass
            result = client.zones.create_rrset(
                zone,
                name=rname,
                type=rtype,
                ttl=args.ttl,
                records=records,
            )
            emit_ok(rrset_to_dict(result.rrset))
            return

        try:
            rrset = client.zones.get_rrset(zone, rname, rtype)
        except Exception as exc:
            if action == "set":
                result = client.zones.create_rrset(
                    zone,
                    name=rname,
                    type=rtype,
                    ttl=args.ttl,
                    records=records,
                )
                emit_ok(rrset_to_dict(result.rrset))
                return
            raise CliError("RRSet not found", hint=str(exc)) from exc

        if action == "set":
            act = client.zones.set_rrset_records(rrset, records)
            if args.ttl is not None:
                client.zones.change_rrset_ttl(rrset, args.ttl)
            emit_ok({"action": wait_action(act), "rrset": rrset_to_dict(rrset)})
            return

        if action == "add":
            act = client.zones.add_rrset_records(rrset, records, ttl=args.ttl)
            emit_ok({"action": wait_action(act), "rrset": rrset_to_dict(rrset)})
            return

        if action == "remove":
            act = client.zones.remove_rrset_records(rrset, records)
            emit_ok({"action": wait_action(act), "rrset": rrset_to_dict(rrset)})
            return

    if action == "delete":
        if not rname or not rtype:
            raise CliError("--name and --type required for record delete")
        _check_protected(rtype, args.force)
        rrset = client.zones.get_rrset(zone, rname, rtype)
        if OPTS.dry_run:
            dry_run_payload({"action": "record.delete", "zone": zname, "rrset": rrset_to_dict(rrset)})
            return
        require_yes(f"delete RRSet {rname or '@'} {rtype} in {zname}")
        client.zones.delete_rrset(rrset)
        emit_ok({"deleted": {"name": rname, "type": rtype, "zone": zname}})
        return

    raise CliError(f"Unknown record action: {action}")


def cmd_server(args: argparse.Namespace) -> None:
    client = get_client()
    action = args.server_action

    if action == "list":
        servers = client.servers.get_all()
        emit_ok([server_to_dict(s) for s in servers])
        return

    if action == "get":
        server = resolve_server(client, args.name)
        emit_ok(server_to_dict(server))
        return

    if action == "create":
        payload = {
            "name": args.name,
            "type": args.type,
            "image": args.image,
            "location": args.location,
            "ssh_keys": args.ssh_key or [],
        }
        if OPTS.dry_run:
            dry_run_payload({"action": "server.create", **payload})
            return
        ssh_keys = [resolve_ssh_key(client, k) for k in (args.ssh_key or [])]
        kwargs = {
            "name": args.name,
            "server_type": ServerType(name=args.type),
            "image": Image(name=args.image) if not args.image.isdigit() else Image(id=int(args.image)),
            "ssh_keys": ssh_keys or None,
            "user_data": args.user_data,
            "labels": json.loads(args.labels) if args.labels else None,
            "start_after_create": not args.no_start,
        }
        if args.location:
            kwargs["location"] = Location(name=args.location)
        response = client.servers.create(**kwargs)
        if response.action:
            wait_action(response.action)
        if response.root_password and not OPTS.json_out:
            print(f"root password: {response.root_password}", file=sys.stderr)
        emit_ok(server_to_dict(response.server))
        return

    if action == "delete":
        server = resolve_server(client, args.name)
        if OPTS.dry_run:
            dry_run_payload({"action": "server.delete", "server": server_to_dict(server)})
            return
        require_yes(f"delete server {server.name}")
        act = client.servers.delete(server)
        emit_ok({"action": wait_action(act), "deleted": server.name})
        return

    if action in ("poweron", "poweroff", "reboot"):
        server = resolve_server(client, args.name)
        if OPTS.dry_run:
            dry_run_payload({"action": f"server.{action}", "server": server.name})
            return
        fn = {"poweron": server.power_on, "poweroff": server.power_off, "reboot": server.reboot}[action]
        emit_ok({"action": wait_action(fn()), "server": server.name})
        return

    if action == "resize":
        server = resolve_server(client, args.name)
        if OPTS.dry_run:
            dry_run_payload(
                {
                    "action": "server.resize",
                    "server": server.name,
                    "type": args.type,
                    "upgrade_disk": args.upgrade_disk,
                }
            )
            return
        require_yes(f"resize server {server.name} to {args.type}")
        act = server.change_type(ServerType(name=args.type), upgrade_disk=args.upgrade_disk)
        emit_ok({"action": wait_action(act), "server": server.name})
        return

    raise CliError(f"Unknown server action: {action}")


def cmd_server_rdns(args: argparse.Namespace) -> None:
    client = get_client()
    sub = args.rdns_action
    server = resolve_server(client, args.name)

    if sub == "get":
        ptrs = []
        if server.public_net and server.public_net.ipv4:
            ptrs.append(
                {
                    "ip": server.public_net.ipv4.ip,
                    "dns_ptr": server.public_net.ipv4.dns_ptr,
                }
            )
        if server.public_net and server.public_net.ipv6:
            ptrs.append(
                {
                    "ip": server.public_net.ipv6.ip,
                    "dns_ptr": server.public_net.ipv6.dns_ptr,
                }
            )
        emit_ok({"server": server.name, "rdns": ptrs})
        return

    if sub == "set":
        if not args.ip or not args.ptr:
            raise CliError("--ip and --ptr required for rdns set")
        if OPTS.dry_run:
            dry_run_payload({"action": "server.rdns.set", "server": server.name, "ip": args.ip, "ptr": args.ptr})
            return
        act = server.change_dns_ptr(args.ip, args.ptr)
        emit_ok({"action": wait_action(act), "server": server.name, "ip": args.ip, "ptr": args.ptr})
        return

    if sub == "reset":
        if not args.ip:
            raise CliError("--ip required for rdns reset")
        if OPTS.dry_run:
            dry_run_payload({"action": "server.rdns.reset", "server": server.name, "ip": args.ip})
            return
        require_yes(f"reset rDNS for {args.ip} on {server.name}")
        act = server.change_dns_ptr(args.ip, None)
        emit_ok({"action": wait_action(act), "server": server.name, "ip": args.ip})
        return

    raise CliError(f"Unknown rdns action: {sub}")


def cmd_volume(args: argparse.Namespace) -> None:
    client = get_client()
    action = args.volume_action

    if action == "list":
        emit_ok([volume_to_dict(v) for v in client.volumes.get_all()])
        return

    if action == "get":
        emit_ok(volume_to_dict(resolve_volume(client, args.name)))
        return

    if action == "create":
        payload = {"name": args.name, "size": args.size, "location": args.location}
        if OPTS.dry_run:
            dry_run_payload({"action": "volume.create", **payload})
            return
        vol = client.volumes.create(
            name=args.name,
            size=args.size,
            location=Location(name=args.location),
            labels=json.loads(args.labels) if args.labels else None,
            automount=args.automount,
        )
        if vol.action:
            wait_action(vol.action)
        emit_ok(volume_to_dict(vol.volume))
        return

    if action == "attach":
        volume = resolve_volume(client, args.name)
        server = resolve_server(client, args.server)
        if OPTS.dry_run:
            dry_run_payload({"action": "volume.attach", "volume": volume.name, "server": server.name})
            return
        act = volume.attach(server, automount=args.automount)
        emit_ok({"action": wait_action(act), "volume": volume.name, "server": server.name})
        return

    if action == "detach":
        volume = resolve_volume(client, args.name)
        if OPTS.dry_run:
            dry_run_payload({"action": "volume.detach", "volume": volume.name})
            return
        act = volume.detach()
        emit_ok({"action": wait_action(act), "volume": volume.name})
        return

    if action == "delete":
        volume = resolve_volume(client, args.name)
        if OPTS.dry_run:
            dry_run_payload({"action": "volume.delete", "volume": volume.name})
            return
        require_yes(f"delete volume {volume.name}")
        act = client.volumes.delete(volume)
        emit_ok({"action": wait_action(act), "deleted": volume.name})
        return

    if action == "resize":
        volume = resolve_volume(client, args.name)
        if OPTS.dry_run:
            dry_run_payload({"action": "volume.resize", "volume": volume.name, "size": args.size})
            return
        require_yes(f"resize volume {volume.name} to {args.size}GB")
        act = volume.resize(args.size)
        emit_ok({"action": wait_action(act), "volume": volume.name, "size": args.size})
        return

    raise CliError(f"Unknown volume action: {action}")


def cmd_firewall(args: argparse.Namespace) -> None:
    client = get_client()
    action = args.firewall_action

    if action == "list":
        emit_ok([firewall_to_dict(f) for f in client.firewalls.get_all()])
        return

    if action == "get":
        emit_ok(firewall_to_dict(resolve_firewall(client, args.name)))
        return

    if action == "create":
        rules = []
        if args.rules_file:
            raw = json.loads(Path(args.rules_file).read_text(encoding="utf-8"))
            for item in raw:
                rules.append(FirewallRule(**item))
        if OPTS.dry_run:
            dry_run_payload({"action": "firewall.create", "name": args.name, "rules": len(rules)})
            return
        fw = client.firewalls.create(name=args.name, rules=rules or None)
        emit_ok(firewall_to_dict(fw))
        return

    if action == "apply":
        fw = resolve_firewall(client, args.name)
        server = resolve_server(client, args.server)
        if OPTS.dry_run:
            dry_run_payload({"action": "firewall.apply", "firewall": fw.name, "server": server.name})
            return
        acts = fw.apply_to_resources(
            [FirewallResource(type=FirewallResource.TYPE_SERVER, server=server)]
        )
        emit_ok({"actions": [wait_action(a) for a in acts], "firewall": fw.name, "server": server.name})
        return

    if action == "delete":
        fw = resolve_firewall(client, args.name)
        if OPTS.dry_run:
            dry_run_payload({"action": "firewall.delete", "firewall": fw.name})
            return
        require_yes(f"delete firewall {fw.name}")
        act = client.firewalls.delete(fw)
        emit_ok({"action": wait_action(act), "deleted": fw.name})
        return

    raise CliError(f"Unknown firewall action: {action}")


def cmd_network(args: argparse.Namespace) -> None:
    client = get_client()
    action = args.network_action

    if action == "list":
        emit_ok([network_to_dict(n) for n in client.networks.get_all()])
        return

    if action == "get":
        emit_ok(network_to_dict(resolve_network(client, args.name)))
        return

    if action == "create":
        if OPTS.dry_run:
            dry_run_payload({"action": "network.create", "name": args.name, "ip_range": args.ip_range})
            return
        net = client.networks.create(name=args.name, ip_range=args.ip_range)
        emit_ok(network_to_dict(net))
        return

    if action == "delete":
        net = resolve_network(client, args.name)
        if OPTS.dry_run:
            dry_run_payload({"action": "network.delete", "network": net.name})
            return
        require_yes(f"delete network {net.name}")
        act = client.networks.delete(net)
        emit_ok({"action": wait_action(act), "deleted": net.name})
        return

    if action == "add-subnet":
        net = resolve_network(client, args.name)
        subnet = NetworkSubnet(type=args.subnet_type, network_zone=args.network_zone, ip_range=args.ip_range)
        if OPTS.dry_run:
            dry_run_payload({"action": "network.add-subnet", "network": net.name, "ip_range": args.ip_range})
            return
        act = net.add_subnet(subnet)
        emit_ok({"action": wait_action(act), "network": net.name})
        return

    if action == "add-route":
        net = resolve_network(client, args.name)
        route = NetworkRoute(destination=args.destination, gateway=args.gateway)
        if OPTS.dry_run:
            dry_run_payload(
                {"action": "network.add-route", "network": net.name, "destination": args.destination}
            )
            return
        act = net.add_route(route)
        emit_ok({"action": wait_action(act), "network": net.name})
        return

    raise CliError(f"Unknown network action: {action}")


def cmd_ssh_key(args: argparse.Namespace) -> None:
    client = get_client()
    action = args.ssh_key_action

    if action == "list":
        emit_ok([ssh_key_to_dict(k) for k in client.ssh_keys.get_all()])
        return

    if action == "get":
        emit_ok(ssh_key_to_dict(resolve_ssh_key(client, args.name)))
        return

    if action == "create":
        public_key = args.public_key
        if args.public_key_file:
            public_key = Path(args.public_key_file).read_text(encoding="utf-8").strip()
        if not public_key:
            raise CliError("--public-key or --public-key-file required")
        if OPTS.dry_run:
            dry_run_payload({"action": "ssh-key.create", "name": args.name})
            return
        key = client.ssh_keys.create(name=args.name, public_key=public_key)
        emit_ok(ssh_key_to_dict(key))
        return

    if action == "delete":
        key = resolve_ssh_key(client, args.name)
        if OPTS.dry_run:
            dry_run_payload({"action": "ssh-key.delete", "name": key.name})
            return
        require_yes(f"delete ssh key {key.name}")
        client.ssh_keys.delete(key)
        emit_ok({"deleted": key.name})
        return

    raise CliError(f"Unknown ssh-key action: {action}")


def cmd_floating_ip(args: argparse.Namespace) -> None:
    client = get_client()
    action = args.floating_ip_action

    if action == "list":
        emit_ok([floating_ip_to_dict(i) for i in client.floating_ips.get_all()])
        return

    if action == "get":
        emit_ok(floating_ip_to_dict(resolve_floating_ip(client, args.name)))
        return

    if action == "create":
        if OPTS.dry_run:
            dry_run_payload(
                {
                    "action": "floating-ip.create",
                    "type": args.type,
                    "home_location": args.home_location,
                }
            )
            return
        ip = client.floating_ips.create(
            type=args.type,
            home_location=Location(name=args.home_location),
            name=args.name,
            description=args.description,
        )
        if ip.action:
            wait_action(ip.action)
        emit_ok(floating_ip_to_dict(ip.floating_ip))
        return

    if action == "assign":
        ip = resolve_floating_ip(client, args.name)
        server = resolve_server(client, args.server)
        if OPTS.dry_run:
            dry_run_payload({"action": "floating-ip.assign", "ip": ip.name or ip.ip, "server": server.name})
            return
        act = ip.assign(server)
        emit_ok({"action": wait_action(act), "ip": ip.ip, "server": server.name})
        return

    if action == "unassign":
        ip = resolve_floating_ip(client, args.name)
        if OPTS.dry_run:
            dry_run_payload({"action": "floating-ip.unassign", "ip": ip.name or ip.ip})
            return
        act = ip.unassign()
        emit_ok({"action": wait_action(act), "ip": ip.ip})
        return

    if action == "delete":
        ip = resolve_floating_ip(client, args.name)
        if OPTS.dry_run:
            dry_run_payload({"action": "floating-ip.delete", "ip": ip.name or ip.ip})
            return
        require_yes(f"delete floating IP {ip.ip}")
        act = client.floating_ips.delete(ip)
        emit_ok({"action": wait_action(act), "deleted": ip.ip})
        return

    raise CliError(f"Unknown floating-ip action: {action}")


def cmd_image(args: argparse.Namespace) -> None:
    client = get_client()
    images = client.images.get_all()
    if args.name:
        images = [i for i in images if i.name == args.name or str(i.id) == args.name]
    emit_ok([image_to_dict(i) for i in images])


def cmd_type_list(_args: argparse.Namespace) -> None:
    client = get_client()
    emit_ok([server_type_to_dict(t) for t in client.server_types.get_all()])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hetzner Cloud CLI for OpenClaw")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="Auth check and resource counts")
    p_status.set_defaults(func=cmd_status)

    p_zone = sub.add_parser("zone", help="DNS zone operations")
    zone_sub = p_zone.add_subparsers(dest="zone_action", required=True)
    zlist = zone_sub.add_parser("list")
    zlist.set_defaults(func=cmd_zone)
    zget = zone_sub.add_parser("get")
    zget.add_argument("name")
    zget.set_defaults(func=cmd_zone)
    zcreate = zone_sub.add_parser("create")
    zcreate.add_argument("name")
    zcreate.add_argument("--mode", default="primary", choices=["primary", "secondary"])
    zcreate.add_argument("--ttl", type=int, default=3600)
    zcreate.set_defaults(func=cmd_zone)
    zdel = zone_sub.add_parser("delete")
    zdel.add_argument("name")
    zdel.set_defaults(func=cmd_zone)
    zexp = zone_sub.add_parser("export")
    zexp.add_argument("name")
    zexp.set_defaults(func=cmd_zone)
    zimp = zone_sub.add_parser("import")
    zimp.add_argument("name")
    zimp.add_argument("file")
    zimp.set_defaults(func=cmd_zone)

    p_rec = sub.add_parser("record", help="DNS record (RRSet) operations")
    rec_sub = p_rec.add_subparsers(dest="record_action", required=True)
    for act in ("list", "get", "create", "set", "add", "remove", "delete"):
        rp = rec_sub.add_parser(act)
        rp.add_argument("--zone")
        rp.add_argument("--name")
        rp.add_argument("--type")
        rp.add_argument("--value", action="append", default=[])
        rp.add_argument("--ttl", type=int)
        rp.add_argument("--force", action="store_true")
        rp.set_defaults(func=cmd_record)

    p_srv = sub.add_parser("server", help="Server operations")
    srv_sub = p_srv.add_subparsers(dest="server_action", required=True)
    sl = srv_sub.add_parser("list")
    sl.set_defaults(func=cmd_server)
    sg = srv_sub.add_parser("get")
    sg.add_argument("name")
    sg.set_defaults(func=cmd_server)
    sc = srv_sub.add_parser("create")
    sc.add_argument("name")
    sc.add_argument("--type", required=True)
    sc.add_argument("--image", required=True)
    sc.add_argument("--location")
    sc.add_argument("--ssh-key", action="append")
    sc.add_argument("--user-data")
    sc.add_argument("--labels")
    sc.add_argument("--no-start", action="store_true")
    sc.set_defaults(func=cmd_server)
    sd = srv_sub.add_parser("delete")
    sd.add_argument("name")
    sd.set_defaults(func=cmd_server)
    for act in ("poweron", "poweroff", "reboot"):
        sp = srv_sub.add_parser(act)
        sp.add_argument("name")
        sp.set_defaults(func=cmd_server)
    sr = srv_sub.add_parser("resize")
    sr.add_argument("name")
    sr.add_argument("--type", required=True)
    sr.add_argument("--upgrade-disk", action="store_true")
    sr.set_defaults(func=cmd_server)
    rdns_sub = srv_sub.add_parser("rdns", help="Reverse DNS (PTR) operations")
    rdns_actions = rdns_sub.add_subparsers(dest="rdns_action", required=True)
    for act in ("get", "set", "reset"):
        rdp = rdns_actions.add_parser(act)
        rdp.add_argument("name")
        rdp.add_argument("--ip")
        rdp.add_argument("--ptr")
        rdp.set_defaults(func=cmd_server_rdns, server_action="rdns")

    p_vol = sub.add_parser("volume", help="Volume operations")
    vol_sub = p_vol.add_subparsers(dest="volume_action", required=True)
    for act, extra in [
        ("list", []),
        ("get", [("name", {}),]),
        ("create", [("name", {}), ("size", {"type": int, "required": True}), ("location", {"required": True}), ("--automount", {"action": "store_true"}), ("--labels", {})]),
        ("attach", [("name", {}), ("server", {}), ("--automount", {"action": "store_true"})]),
        ("detach", [("name", {})]),
        ("delete", [("name", {})]),
        ("resize", [("name", {}), ("size", {"type": int})]),
    ]:
        vp = vol_sub.add_parser(act)
        if act == "get":
            vp.add_argument("name")
        elif act == "create":
            vp.add_argument("name")
            vp.add_argument("size", type=int)
            vp.add_argument("location")
            vp.add_argument("--automount", action="store_true")
            vp.add_argument("--labels")
        elif act in ("attach", "detach", "delete", "resize"):
            vp.add_argument("name")
            if act == "attach":
                vp.add_argument("server")
                vp.add_argument("--automount", action="store_true")
            if act == "resize":
                vp.add_argument("size", type=int)
        vp.set_defaults(func=cmd_volume)

    p_fw = sub.add_parser("firewall", help="Firewall operations")
    fw_sub = p_fw.add_subparsers(dest="firewall_action", required=True)
    for act in ("list",):
        fwp = fw_sub.add_parser(act)
        fwp.set_defaults(func=cmd_firewall)
    fwg = fw_sub.add_parser("get")
    fwg.add_argument("name")
    fwg.set_defaults(func=cmd_firewall)
    fwc = fw_sub.add_parser("create")
    fwc.add_argument("name")
    fwc.add_argument("--rules-file")
    fwc.set_defaults(func=cmd_firewall)
    fwa = fw_sub.add_parser("apply")
    fwa.add_argument("name")
    fwa.add_argument("server")
    fwa.set_defaults(func=cmd_firewall)
    fwd = fw_sub.add_parser("delete")
    fwd.add_argument("name")
    fwd.set_defaults(func=cmd_firewall)

    p_net = sub.add_parser("network", help="Private network operations")
    net_sub = p_net.add_subparsers(dest="network_action", required=True)
    nl = net_sub.add_parser("list")
    nl.set_defaults(func=cmd_network)
    ng = net_sub.add_parser("get")
    ng.add_argument("name")
    ng.set_defaults(func=cmd_network)
    nc = net_sub.add_parser("create")
    nc.add_argument("name")
    nc.add_argument("ip_range")
    nc.set_defaults(func=cmd_network)
    nd = net_sub.add_parser("delete")
    nd.add_argument("name")
    nd.set_defaults(func=cmd_network)
    nas = net_sub.add_parser("add-subnet")
    nas.add_argument("name")
    nas.add_argument("ip_range")
    nas.add_argument("--subnet-type", default="cloud")
    nas.add_argument("--network-zone", default="eu-central")
    nas.set_defaults(func=cmd_network)
    nar = net_sub.add_parser("add-route")
    nar.add_argument("name")
    nar.add_argument("destination")
    nar.add_argument("gateway")
    nar.set_defaults(func=cmd_network)

    p_key = sub.add_parser("ssh-key", help="SSH key operations")
    key_sub = p_key.add_subparsers(dest="ssh_key_action", required=True)
    kl = key_sub.add_parser("list")
    kl.set_defaults(func=cmd_ssh_key)
    kg = key_sub.add_parser("get")
    kg.add_argument("name")
    kg.set_defaults(func=cmd_ssh_key)
    kc = key_sub.add_parser("create")
    kc.add_argument("name")
    kc.add_argument("--public-key")
    kc.add_argument("--public-key-file")
    kc.set_defaults(func=cmd_ssh_key)
    kd = key_sub.add_parser("delete")
    kd.add_argument("name")
    kd.set_defaults(func=cmd_ssh_key)

    p_fip = sub.add_parser("floating-ip", help="Floating IP operations")
    fip_sub = p_fip.add_subparsers(dest="floating_ip_action", required=True)
    fi_l = fip_sub.add_parser("list")
    fi_l.set_defaults(func=cmd_floating_ip)
    fi_g = fip_sub.add_parser("get")
    fi_g.add_argument("name")
    fi_g.set_defaults(func=cmd_floating_ip)
    fi_c = fip_sub.add_parser("create")
    fi_c.add_argument("--type", default="ipv4", choices=["ipv4", "ipv6"])
    fi_c.add_argument("--home-location", required=True)
    fi_c.add_argument("--name")
    fi_c.add_argument("--description")
    fi_c.set_defaults(func=cmd_floating_ip)
    fi_a = fip_sub.add_parser("assign")
    fi_a.add_argument("name")
    fi_a.add_argument("server")
    fi_a.set_defaults(func=cmd_floating_ip)
    fi_u = fip_sub.add_parser("unassign")
    fi_u.add_argument("name")
    fi_u.set_defaults(func=cmd_floating_ip)
    fi_d = fip_sub.add_parser("delete")
    fi_d.add_argument("name")
    fi_d.set_defaults(func=cmd_floating_ip)

    p_img = sub.add_parser("image", help="List images")
    p_img.add_argument("name", nargs="?")
    p_img.set_defaults(func=cmd_image)

    p_type = sub.add_parser("type", help="List server types")
    p_type.set_defaults(func=cmd_type_list)

    return parser


def main() -> None:
    pre = argparse.ArgumentParser(add_help=False)
    _add_globals(pre)
    pre_args, argv = pre.parse_known_args()

    parser = build_parser()
    args = parser.parse_args(argv)
    for key in ("json", "yes", "dry_run", "zone", "project"):
        setattr(args, key, getattr(pre_args, key) or getattr(args, key, None))

    OPTS.json_out = args.json
    OPTS.yes = args.yes
    OPTS.dry_run = args.dry_run
    OPTS.default_zone = args.zone
    OPTS.project = args.project
    try:
        args.func(args)
    except CliError as exc:
        emit_error(exc)
    except Exception as exc:
        emit_error(exc)


if __name__ == "__main__":
    main()
