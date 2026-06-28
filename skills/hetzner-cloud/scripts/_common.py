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
    project: str | None = None


OPTS = GlobalOpts()

# Path to multi-project token registry. Loaded on first use.
_PROJECTS_ENV_PATH = os.path.expanduser("~/.config/moss/hcloud-projects.env")
_projects_cache: dict[str, str] | None = None


def _load_projects() -> dict[str, str]:
    """Load the multi-project token registry.

    Reads `~/.config/moss/hcloud-projects.env` (mode 600) if it exists,
    parsing HCLOUD_PROJECT_<NAME>=TOKEN lines into a dict.

    Falls back gracefully (empty dict) if the file is missing.
    """
    global _projects_cache
    if _projects_cache is not None:
        return _projects_cache

    projects: dict[str, str] = {}
    if not os.path.exists(_PROJECTS_ENV_PATH):
        _projects_cache = projects
        return projects

    try:
        with open(_PROJECTS_ENV_PATH, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[len("export "):]
                if "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                # Strip surrounding quotes (single or double)
                if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
                    val = val[1:-1]
                if key.startswith("HCLOUD_PROJECT_") and key != "HCLOUD_PROJECT_NAME":
                    name = key[len("HCLOUD_PROJECT_"):].lower()
                    projects[name] = val
    except OSError as exc:
        raise CliError(
            f"Cannot read {_PROJECTS_ENV_PATH}",
            hint=str(exc),
        ) from exc

    _projects_cache = projects
    return projects


def list_projects() -> list[str]:
    """Return names of all registered projects."""
    return sorted(_load_projects().keys())


def get_token(project: str | None = None) -> tuple[str, str]:
    """Resolve (token, project_name) for the requested project.

    Lookup order:
    1. Explicit --project / HCLOUD_PROJECT_NAME
    2. HCLOUD_DEFAULT_PROJECT env var
    3. HCLOUD_TOKEN env var (legacy single-project mode)
    4. 'dns' if exactly one project is registered
    """
    projects = _load_projects()

    # 1. Explicit override
    if project is None:
        project = OPTS.project
    if project is None:
        project = os.environ.get("HCLOUD_PROJECT_NAME")
    if project is not None:
        name = project.lower()
        if name not in projects:
            raise CliError(
                f"Unknown project: {project!r}",
                hint=f"Available: {', '.join(list_projects()) or '(none registered)'}",
            )
        return projects[name], name

    # 2. HCLOUD_DEFAULT_PROJECT
    default = os.environ.get("HCLOUD_DEFAULT_PROJECT", "").strip().lower()
    if default and default in projects:
        return projects[default], default

    # 3. Legacy HCLOUD_TOKEN fallback
    legacy = os.environ.get("HCLOUD_TOKEN", "").strip()
    if legacy:
        return legacy, "<legacy>"

    # 4. Single registered project — use it as default
    if len(projects) == 1:
        only_name = next(iter(projects))
        return projects[only_name], only_name

    # 5. None registered — error
    raise CliError(
        "No project resolved",
        hint=(
            "Pass --project=<name>, set HCLOUD_PROJECT_NAME, or register a "
            f"token in {_PROJECTS_ENV_PATH}"
        ),
    )


def get_client(project: str | None = None) -> Client:
    """Return an authenticated hcloud.Client.

    Pass an explicit project name to target a specific Hetzner Cloud project.
    Without args, resolves via OPTS.project / HCLOUD_PROJECT_NAME /
    HCLOUD_DEFAULT_PROJECT / HCLOUD_TOKEN (legacy) / single-registered-project.
    """
    token, name = get_token(project)
    return Client(
        token=token,
        application_name=APP_NAME,
        application_version=APP_VERSION,
    )


def find_zone_owner(zone_name: str) -> str | None:
    """Return the project name that owns the given DNS zone, or None.

    Hetzner DNS zone names are globally unique across projects, so we probe
    each registered project until one returns the zone. Probes are cached
    per-zone-name for the lifetime of the process.
    """
    projects = _load_projects()
    if not projects:
        return None
    # Avoid resolving the project that already owns the requested project
    # (no-op pass-through in most calls).
    from functools import lru_cache  # local import: keep module load fast

    @lru_cache(maxsize=64)
    def _lookup(name: str) -> str | None:
        for proj_name, tok in projects.items():
            try:
                client = Client(
                    token=tok,
                    application_name=APP_NAME,
                    application_version=APP_VERSION,
                )
                client.zones.get(name)
                return proj_name
            except Exception:
                continue
        return None

    return _lookup(zone_name)


def require_yes(action: str) -> None:
    if not OPTS.yes:
        raise CliError(
            f"Refusing to {action} without --yes",
            hint="Re-run with --yes to confirm",
        )


def dry_run_payload(payload: dict[str, Any]) -> None:
    emit_ok({"dry_run": True, **payload})


def normalize_record_name(name: str) -> str:
    """Normalize a DNS RRSet name for the Hetzner DNS API.

    - "@" and "" both map to the zone apex ("@") — the Hetzner API expects the
      literal "@" for apex records when creating/modifying RRSets.
    - Otherwise strip any trailing dot.
    """
    if name in ("@", ""):
        return "@"
    return name.rstrip(".")


def zone_name(opts_zone: str | None) -> str:
    name = (opts_zone or OPTS.default_zone or os.environ.get("HCLOUD_DEFAULT_ZONE", "")).strip()
    if not name:
        raise CliError(
            "Zone name required",
            hint="Pass --zone or set HCLOUD_DEFAULT_ZONE",
        )
    return name


def resolve_zone(client: Client, name: str):
    try:
        return client.zones.get(name)
    except Exception as exc:
        # If this is a multi-project setup and the zone isn't in the current
        # project, try the other projects before giving up.
        if OPTS.project is None and os.environ.get("HCLOUD_PROJECT_NAME") is None:
            owner = find_zone_owner(name)
            if owner is not None:
                raise CliError(
                    f"Zone {name!r} not in current project, but found in --project={owner}",
                    hint=f"Re-run with --project={owner}",
                )
        raise CliError(f"Zone not found: {name}", hint=str(exc)) from exc


def resolve_server(client: Client, ref: str):
    if ref.isdigit():
        return client.servers.get_by_id(int(ref))
    server = client.servers.get_by_name(ref)
    if server is None:
        raise CliError(f"Server not found: {ref}")
    return server


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
