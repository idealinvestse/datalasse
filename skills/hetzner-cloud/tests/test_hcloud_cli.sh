#!/usr/bin/env bash
# Read-only smoke tests for hetzner-cloud CLI.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI="$ROOT/bin/hcloud-cli"

if [ -z "${HCLOUD_TOKEN:-}" ]; then
  echo "SKIP: HCLOUD_TOKEN not set"
  exit 0
fi

echo "== status =="
"$CLI" status --json | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['ok']"

echo "== zone list =="
"$CLI" zone list --json | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['ok']"

if [ -n "${HCLOUD_DEFAULT_ZONE:-}" ]; then
  echo "== record list ($HCLOUD_DEFAULT_ZONE) =="
  "$CLI" record list --zone "$HCLOUD_DEFAULT_ZONE" --json | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['ok']"
fi

echo "== server list =="
"$CLI" server list --json | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['ok']"

echo "OK: hetzner-cloud smoke tests passed"
