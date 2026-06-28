"""Shared helpers for hetzner-cloud CLI."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any

from hcloud import Client
from hcloud.actions.domain import ActionFailedException, ActionTimeoutException
from hcloud.actions.client import BoundAction

APP_NAME = "openclaw"
APP_VERSION = "1.0.0"

PROTECTED_RR_TYPES = frozenset({"SOA", "NS"})


class CliError(Exception):
    """User-facing CLI error with optional hint."""

    def __init__(self, message: str, hint: str | None = None):
        super().__init__(message)
        self.message = message
        self.hint = hint


class GlobalOpts:
    json_out: bool = False
    yes: bool = False
    dry_run: bool = False
    default_zone: str | None = None


OPTS = GlobalOpts()


def get_client() -> Client:
    token = os.environ.get("HCLOUD_TOKEN", "").strip()
    if not token:
        raise CliError(
            "HCLOUD_TOKEN is not set",
            hint="Create an API token in Hetzner Cloud Console → Security → API tokens",
        )
    return Client(
        token=token,
        application_name=APP_NAME,
        application_version=APP_VERSION,
    )


def require_yes(action: str) -> None:
    if not OPTS.yes:
        raise CliError(
            f"Refusing to {action} without --yes",
            hint="Re-run with --yes to confirm",
        )


def dry_run_payload(payload: dict[str, Any]) -> None:
    emit_ok({"dry_run": True, **payload})


def normalize_record_name(name: str) -> str:
    if name in ("@", ""):
        return ""
    return name.rstrip(".")


def zone_name(opts_zone: str | None) -> str:
    name = (opts_zone or OPTS.default_zone or os.environ.get("HCLOUD_DEFAULT_ZONE", "")).strip()
    if not name:
        raise CliError(
            "Zone name required",
            hint="Pass --zone or set HCLOUD_DEFAULT_ZONE",
        )
    return name


def resolve_server(client: Client, ref: str):
    if ref.isdigit():
        return client.servers.get_by_id(int(ref))
    server = client.servers.get_by_name(ref)
    if server is None:
        raise CliError(f"Server not found: {ref}")
    return server


def resolve_zone(client: Client, name: str):
    try:
        return client.zones.get(name)
    except Exception as exc:
        raise CliError(f"Zone not found: {name}", hint=str(exc)) from exc


def resolve_volume(client: Client, ref: str):
    if ref.isdigit():
        return client.volumes.get_by_id(int(ref))
    volume = client.volumes.get_by_name(ref)
    if volume is None:
        raise CliError(f"Volume not found: {ref}")
    return volume


def resolve_firewall(client: Client, ref: str):
    if ref.isdigit():
        return client.firewalls.get_by_id(int(ref))
    fw = client.firewalls.get_by_name(ref)
    if fw is None:
        raise CliError(f"Firewall not found: {ref}")
    return fw


def resolve_network(client: Client, ref: str):
    if ref.isdigit():
        return client.networks.get_by_id(int(ref))
    net = client.networks.get_by_name(ref)
    if net is None:
        raise CliError(f"Network not found: {ref}")
    return net


def resolve_ssh_key(client: Client, ref: str):
    if ref.isdigit():
        return client.ssh_keys.get_by_id(int(ref))
    key = client.ssh_keys.get_by_name(ref)
    if key is None:
        raise CliError(f"SSH key not found: {ref}")
    return key


def resolve_floating_ip(client: Client, ref: str):
    if ref.isdigit():
        return client.floating_ips.get_by_id(int(ref))
    ip = client.floating_ips.get_by_name(ref)
    if ip is None:
        raise CliError(f"Floating IP not found: {ref}")
    return ip


def wait_action(action: BoundAction) -> dict[str, Any]:
    try:
        action.wait_until_finished()
    except ActionTimeoutException as exc:
        raise CliError("Action timed out", hint=f"action_id={exc.action.id}") from exc
    except ActionFailedException as exc:
        raise CliError(
            "Action failed",
            hint=exc.action.error or f"action_id={exc.action.id}",
        ) from exc
    return action_to_dict(action)


def _serialize(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return _serialize(asdict(value))
    if hasattr(value, "__dict__"):
        data = {}
        for key in dir(value):
            if key.startswith("_"):
                continue
            try:
                attr = getattr(value, key)
            except Exception:
                continue
            if callable(attr):
                continue
            data[key] = _serialize(attr)
        return data
    return str(value)


def zone_to_dict(zone) -> dict[str, Any]:
    return {
        "id": zone.id,
        "name": zone.name,
        "mode": zone.mode,
        "status": zone.status,
        "ttl": zone.ttl,
        "record_count": zone.record_count,
        "registrar": zone.registrar,
        "labels": zone.labels or {},
    }


def rrset_to_dict(rrset) -> dict[str, Any]:
    records = []
    for rec in rrset.records or []:
        records.append({"value": rec.value, "comment": rec.comment})
    return {
        "id": rrset.id,
        "name": rrset.name,
        "type": rrset.type,
        "ttl": rrset.ttl,
        "records": records,
        "labels": rrset.labels or {},
    }


def server_to_dict(server) -> dict[str, Any]:
    ipv4 = None
    if server.public_net and server.public_net.ipv4:
        ipv4 = server.public_net.ipv4.ip
    ipv6 = None
    if server.public_net and server.public_net.ipv6:
        ipv6 = server.public_net.ipv6.ip
    return {
        "id": server.id,
        "name": server.name,
        "status": server.status,
        "server_type": server.server_type.name if server.server_type else None,
        "datacenter": server.datacenter.name if server.datacenter else None,
        "ipv4": ipv4,
        "ipv6": ipv6,
        "labels": server.labels or {},
    }


def volume_to_dict(volume) -> dict[str, Any]:
    return {
        "id": volume.id,
        "name": volume.name,
        "size": volume.size,
        "status": volume.status,
        "location": volume.location.name if volume.location else None,
        "server": volume.server.id if volume.server else None,
        "labels": volume.labels or {},
    }


def firewall_to_dict(fw) -> dict[str, Any]:
    rules = []
    for rule in fw.rules or []:
        rules.append(
            {
                "direction": rule.direction,
                "protocol": rule.protocol,
                "port": rule.port,
                "source_ips": rule.source_ips,
                "destination_ips": rule.destination_ips,
                "description": rule.description,
            }
        )
    return {
        "id": fw.id,
        "name": fw.name,
        "rules": rules,
        "applied_to": _serialize(fw.applied_to),
        "labels": fw.labels or {},
    }


def network_to_dict(net) -> dict[str, Any]:
    return {
        "id": net.id,
        "name": net.name,
        "ip_range": net.ip_range,
        "subnets": _serialize(net.subnets),
        "routes": _serialize(net.routes),
        "labels": net.labels or {},
    }


def ssh_key_to_dict(key) -> dict[str, Any]:
    return {
        "id": key.id,
        "name": key.name,
        "fingerprint": key.fingerprint,
        "public_key": key.public_key,
        "labels": key.labels or {},
    }


def floating_ip_to_dict(ip) -> dict[str, Any]:
    return {
        "id": ip.id,
        "name": ip.name,
        "ip": ip.ip,
        "type": ip.type,
        "server": ip.server.id if ip.server else None,
        "home_location": ip.home_location.name if ip.home_location else None,
        "labels": ip.labels or {},
    }


def action_to_dict(action: BoundAction) -> dict[str, Any]:
    return {
        "id": action.id,
        "command": action.command,
        "status": action.status,
        "progress": action.progress,
        "started": _serialize(action.started),
        "finished": _serialize(action.finished),
        "error": action.error,
    }


def image_to_dict(image) -> dict[str, Any]:
    return {
        "id": image.id,
        "name": image.name,
        "description": image.description,
        "type": image.type,
        "status": image.status,
        "os_flavor": image.os_flavor,
        "os_version": image.os_version,
    }


def server_type_to_dict(st) -> dict[str, Any]:
    return {
        "id": st.id,
        "name": st.name,
        "cores": st.cores,
        "memory": st.memory,
        "disk": st.disk,
        "architecture": st.architecture,
    }


def emit_ok(data: Any) -> None:
    if OPTS.json_out:
        print(json.dumps({"ok": True, "data": data}, indent=2, default=str))
    else:
        if isinstance(data, list):
            for item in data:
                print(json.dumps(item, indent=2, default=str))
        elif isinstance(data, dict):
            print(json.dumps(data, indent=2, default=str))
        else:
            print(data)


def emit_error(err: CliError | Exception) -> None:
    if isinstance(err, CliError):
        payload = {"ok": False, "error": err.message}
        if err.hint:
            payload["hint"] = err.hint
    else:
        payload = {"ok": False, "error": str(err)}
    if OPTS.json_out:
        print(json.dumps(payload, indent=2))
    else:
        print(f"✗ {payload['error']}", file=sys.stderr)
        if payload.get("hint"):
            print(f"  hint: {payload['hint']}", file=sys.stderr)
    sys.exit(1)
