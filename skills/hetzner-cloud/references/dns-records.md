# DNS records (Hetzner DNS)

## RRSet naming

- Apex/root: `--name @` (normalized to empty string in API).
- Subdomain: `--name mail` → `mail.example.com`.
- FQDN in values is usually without trailing dot unless required by record type.

## Supported types

A, AAAA, CAA, CNAME, DS, HINFO, HTTPS, MX, NS, PTR, RP, SOA, SRV, SVCB, TLSA, TXT

SOA and NS are protected — require `--force` to change via CLI.

## Common mailcow records (intelliserve.se)

| Purpose | Command |
|---------|---------|
| Mail host A | `record set --zone intelliserve.se --name mail --type A --value 167.233.38.175` |
| MX | `record set --zone intelliserve.se --name @ --type MX --value "10 mail.intelliserve.se"` |
| SPF | `record add --zone intelliserve.se --name @ --type TXT --value "v=spf1 mx ~all"` |
| DKIM | `record add --zone intelliserve.se --name dkim._domainkey --type TXT --value "<from mailcow admin>"` |
| DMARC | `record add --zone intelliserve.se --name _dmarc --type TXT --value "v=DMARC1; p=quarantine; rua=mailto:..."` |

Get DKIM TXT from Mailcow admin → Configuration → DNS → domain.

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
```
