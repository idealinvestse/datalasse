# DNS records (Hetzner DNS)

## RRSet naming

- Apex/root: `--name @` (normalized to literal `@` for the Hetzner API).
- Subdomain: `--name mail` → `mail.example.com`.
- FQDN in values is usually without trailing dot unless required by record type.

## Supported types

A, AAAA, CAA, CNAME, DS, HINFO, HTTPS, MX, NS, PTR, RP, SOA, SRV, SVCB, TLSA, TXT

SOA and NS are protected — require `--force` to change via CLI.

## TXT value escaping

Hetzner DNS requires TXT record values to be wrapped in double quotes
(`"value"`). The CLI auto-wraps TXT `--value` args that are not already quoted.

## Common mailcow records (intelliserve.se)

| Purpose | Command |
|---------|---------|
| Mail host A | `record set --zone intelliserve.se --name mail --type A --value 167.233.38.175` |
| MX | `record set --zone intelliserve.se --name @ --type MX --value "10 mail.intelliserve.se"` |
| SPF | `record add --zone intelliserve.se --name @ --type TXT --value 'v=spf1 mx a -all'` |
| DMARC | `record add --zone intelliserve.se --name _dmarc --type TXT --value 'v=DMARC1; p=reject; rua=mailto:postmaster@intelliserve.se; adkim=s; aspf=s'` |

Get DKIM TXT from Mailcow admin → Configuration → DNS → domain, or via API:
`curl -H "X-API-Key: $MAILCOW_API_KEY" https://mail.intelliserve.se/api/v1/get/dkim/intelliserve.se`.

### DKIM > 255 chars (RFC 1035 split)

DKIM TXT records usually exceed 255 chars per string (RSA-2048 base64 ~ 392
chars). The API rejects single-string TXT > 255 chars. Split the base64 portion
into ≤252 char chunks and submit as a single TXT record with multiple
space-separated quoted strings:

```bash
# See scripts/mailcow_dkim_apply.py for a complete helper.
python3 -c '
import re, sys
dkim = "<paste mailcow dkim_txt>"
m = re.match(r"(v=DKIM1;[^p]*p=)(.+)", dkim)
prefix, b64 = m.group(1), m.group(2)
parts = [f"\"{prefix}\""] + [f"\"{b64[i:i+252]}\"" for i in range(0, len(b64), 252)]
print(" ".join(parts))
' > /tmp/dkim_joined.txt
ZONE_ID=$(hcloud-cli zone list | jq -r '.[] | select(.name=="intelliserve.se") | .id')
python3 scripts/mailcow_dkim_apply.py /tmp/dkim_joined.txt
```

The helper reads the joined TXT (already wrapped in quotes), POSTs to
`/v1/zones/$ZONE_ID/rrsets` with `name=dkim._domainkey`, `type=TXT`, single
record whose value is the joined multi-string TXT.

## MX / multi-value records

- Repeat `--value` for multiple records in one RRSet: `--value "10 mx1" --value "20 mx2"`.
- `record add` appends; `record set` replaces all values in the RRSet.

## Zone import/export

```bash
bin/hcloud-cli zone export intelliserve.se > zone.backup.txt
bin/hcloud-cli zone import intelliserve.se zone.backup.txt --yes
```

Import replaces all RRSets — backup first.

## Verification

```bash
bin/hcloud-cli record list --zone intelliserve.se --json
dig +short mail.intelliserve.se A
dig +short intelliserve.se MX
dig +short @1.1.1.1 intelliserve.se TXT
dig +short @1.1.1.1 _dmarc.intelliserve.se TXT
dig +short @1.1.1.1 dkim._domainkey.intelliserve.se TXT
```

For external deliverability, also verify **PTR / rDNS** matches the FQDN:
`dig +short -x <mail-server-ip>` should return `mail.intelliserve.se.`.
Set via Hetzner Cloud Console → Servers → rDNS (requires a token with access
to the project containing the server).
