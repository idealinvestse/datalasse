#!/usr/bin/env python3
"""Apply DKIM TXT record to Hetzner DNS (handles 255-char TXT string split)."""
import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    token = os.environ["HCLOUD_TOKEN"]
    zone_id = os.environ["ZONE_ID"]
    dkim_txt_path = sys.argv[1]
    with open(dkim_txt_path, "r", encoding="utf-8") as fh:
        dkim_value = fh.read().strip()

    # Hetzner DNS API: TXT record value with multiple character strings (RFC 1035).
    # Use a single record value that contains all the strings space-separated.
    payload = {
        "name": "dkim._domainkey",
        "type": "TXT",
        "ttl": 86400,
        "records": [{"value": dkim_value, "comment": "DKIM for intelliserve.se (from mailcow)"}],
    }
    req = urllib.request.Request(
        f"https://api.hetzner.cloud/v1/zones/{zone_id}/rrsets",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req)
        out = json.loads(resp.read())
        rrset = out.get("rrset", {})
        print(f"OK: rrset.id={rrset.get('id')!r}")
        print(f"    records: {len(rrset.get('records', []))}")
        print(f"    action.status={out.get('action', {}).get('status')}")
        return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"ERROR {e.code}: {body[:500]}")
        return 1


if __name__ == "__main__":
    sys.exit(main())