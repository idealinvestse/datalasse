---
name: moss-eth-wallet
description: "EIP-7702 self-custody ETH/ERC-20 wallet for Moss agent. Root EOA offline (encrypted), VPS holds only scoped session key with on-chain daily cap + whitelist + TTL. CLI mirrors moss-wallet (BTC)."
---

# moss-eth-wallet

EIP-7702 scoped delegation wallet. Root key never lives in cleartext on the VPS. Session key on VPS is heavily constrained on-chain.

**Security model**: Root mnemonic encrypted (Fernet + PBKDF2 480k). Session key (separate encrypted file) can only spend within on-chain enforced rules inside the delegated ScopeEnforcer contract. No auto-broadcasts.

## Architecture
- Root EOA (BIP-39 + m/44'/60'/0'/0/0)
- One-time EIP-7702 delegation (root signs) → EOA code becomes ScopeEnforcer
- Session key signs `execute(to, value, data)` calls on the EOA address
- ScopeEnforcer enforces: sender is current session, not expired, dailyCap, to in whitelist

## Setup

```bash
pip install web3 eth-account --break-system-packages
# cryptography + mnemonic already installed (from BTC wallet)
```

## Storage (~/.moss/wallet/eth/)

- keystore.enc (0600) — encrypted root mnemonic
- session.enc (0600) — encrypted session privkey + scope
- config.json (0600) — network, enforcer address etc.
- audit.log (0600)

Root mnemonic **never** on disk cleartext.

## CLI: bin/moss-wallet-eth

All commands support `--network holesky|sepolia|mainnet` (default holesky) and `--confirm`/`-y`.

Key commands:
- `init`
- `restore`
- `addresses`
- `balance [--token ADDR]`
- `delegate [--confirm]`
- `session-issue --daily-cap 0.5 --ttl 7d [--whitelist 0x..] [--confirm]`
- `session-revoke [--confirm]`
- `send --to 0x.. --amount 0.01 [--token 0xERC] [--confirm]`
- `scope [--set ...] [--confirm]`
- `export-backup [--confirm]`
- `status`

**Important**: `delegate`, `session-issue`, `scope` (increasing) and root admin actions require the root passphrase. Regular `send` uses only the session key.

Testnet strongly recommended. Use public Holesky faucets to fund the root EOA for the one-time delegation tx.

## ScopeEnforcer

See `contracts/ScopeEnforcer.sol`. Minimal contract compiled to bytecode embedded in `contract.py`.

To rebuild bytecode (one time):
```bash
# Option A: python + solcx (extra)
python3 -c '
from solcx import compile_source, install_solc
install_solc("0.8.27")
...
'
# Option B: docker/solc or system solc, then paste hex into contract.py
```

## Tests

```bash
python3 -m pytest skills/moss_eth_wallet/tests/ -v
```

## Usage example (Holesky)

```bash
bin/moss-wallet-eth init --network holesky
bin/moss-wallet-eth session-issue --daily-cap 0.1 --ttl 7d --confirm
bin/moss-wallet-eth delegate --confirm   # fund root first
bin/moss-wallet-eth balance
bin/moss-wallet-eth send --to 0xRecipient --amount 0.001 --confirm
```

## Out of scope (v1)

- Multi-session advanced ACLs
- Paymasters / gas sponsorship
- Hardware wallets
- Mainnet production use without extra audits
- BTC (use separate moss-wallet)

See the plan.md for full design and verification.
