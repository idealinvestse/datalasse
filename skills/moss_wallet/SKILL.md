---
name: moss-wallet
description: "Self-custody Bitcoin HD wallet (BIP-39/44/84/86) for Moss. Encrypted at rest. CLI for addresses, balance, PSBT construction (no broadcast)."
---

# moss-wallet

Self-custody native Bitcoin Hierarchical Deterministic wallet.

**Security model**: Mnemonic encrypted with user passphrase (Fernet + PBKDF2). Private material only in RAM. PSBT only — never auto-broadcasts.

## Setup

```bash
pip install bitcoinlib mnemonic --break-system-packages
# cryptography is pre-installed
```

## CLI

`bin/moss-wallet` (executable)

All commands:

- `status`
- `init [--testnet]`
- `restore [--testnet]`
- `addresses [--type legacy|segwit|taproot] [--count N]`
- `balance`
- `receive [--type ...]`
- `send --to <addr> --amount <BTC> --fee-rate <sat/vB> [--confirm] [--psbt-file out.psbt]`
- `export-backup [--output file.txt] [--confirm]`

Global: `--testnet` (overrides stored network)

**Passphrase**: Prompted interactively (getpass). Or set `MOSSWALLET_PASSPHRASE` (use with care).

## Storage

- `~/.moss/wallet/btc/keystore.enc` (0600) — encrypted mnemonic
- `~/.moss/wallet/btc/config.json` (0600) — network + receive index
- `~/.moss/wallet/btc/audit.log` (0600)

Mnemonic **never** on disk in cleartext except during `init`/`restore` display and `export-backup`.

## Paper backup

Use `export-backup --confirm` and print the output securely. Delete the file after printing.

## Testnet recommended for first use

`bin/moss-wallet init --testnet`

## Verification

See plan verification steps. Run:

```bash
python3 -m pytest skills/moss_wallet/tests/ -v
bin/moss-wallet status
...
```

## Out of scope (v1)

Real sends, hardware, Lightning, ETH, full watch-only xpub mode.
