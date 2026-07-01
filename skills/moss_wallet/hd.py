"""HD wallet derivation for Bitcoin using BIP-39 + BIP-44/84/86.

Supports:
- Legacy (P2PKH): m/44'/0'/0'/0/i   -> 1... (main) / m... (test)
- Native SegWit (P2WPKH): m/84'/0'/0'/0/i -> bc1q... / tb1q...
- Taproot (P2TR): m/86'/0'/0'/0/i -> bc1p... / tb1p...
"""
from __future__ import annotations

from mnemonic import Mnemonic
from bitcoinlib.keys import HDKey

from skills.moss_wallet.utils import is_testnet_network

MNEMONIC_STRENGTH = 256  # 24 words


def generate_mnemonic() -> str:
    """Generate a new 24-word BIP-39 english mnemonic."""
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=MNEMONIC_STRENGTH)


def validate_mnemonic(mnemonic: str) -> bool:
    """Validate BIP-39 mnemonic."""
    mnemo = Mnemonic("english")
    return mnemo.check(mnemonic.strip())


def mnemonic_to_seed(mnemonic: str) -> bytes:
    """Convert mnemonic to seed bytes (no passphrase for now)."""
    mnemo = Mnemonic("english")
    return mnemo.to_seed(mnemonic.strip())


def _network_code(network: str) -> str:
    """Map our 'mainnet'/'testnet' to bitcoinlib network codes."""
    return "testnet" if is_testnet_network(network) else "bitcoin"


def _coin_type(network: str) -> int:
    """BIP44 coin type: 0 main, 1 test."""
    return 1 if is_testnet_network(network) else 0


def derive_address(
    mnemonic: str,
    index: int = 0,
    address_type: str = "segwit",
    network: str = "mainnet",
) -> str:
    """Derive a receive address (change=0).

    address_type: "legacy" | "segwit" | "taproot"
    """
    if not validate_mnemonic(mnemonic):
        raise ValueError("Invalid mnemonic")
    seed = mnemonic_to_seed(mnemonic)
    net = _network_code(network)
    hdkey = HDKey.from_seed(seed, network=net)

    coin = _coin_type(network)
    if address_type == "legacy":
        path = f"m/44h/{coin}h/0h/0/{index}"
        child = hdkey.subkey_for_path(path)
        # Force base58 P2PKH style
        addr = child.address(encoding="base58")
    elif address_type == "segwit":
        path = f"m/84h/{coin}h/0h/0/{index}"
        child = hdkey.subkey_for_path(path)
        addr = child.address(script_type="p2wpkh")
    elif address_type == "taproot":
        path = f"m/86h/{coin}h/0h/0/{index}"
        child = hdkey.subkey_for_path(path)
        addr = child.address(script_type="p2tr")
    else:
        raise ValueError(f"Unknown address_type: {address_type}")

    return addr


def derive_first_addresses(
    mnemonic: str, count: int = 5, network: str = "mainnet"
) -> dict:
    """Return dict of first N addresses for all types."""
    addrs = {"legacy": [], "segwit": [], "taproot": []}
    for i in range(count):
        addrs["legacy"].append(derive_address(mnemonic, i, "legacy", network))
        addrs["segwit"].append(derive_address(mnemonic, i, "segwit", network))
        addrs["taproot"].append(derive_address(mnemonic, i, "taproot", network))
    return addrs


def get_xpub(mnemonic: str, network: str = "mainnet", account: int = 0) -> str:
    """Return xpub (or tpub) for account. Useful for future watch-only."""
    seed = mnemonic_to_seed(mnemonic)
    net = _network_code(network)
    coin = _coin_type(network)
    hdkey = HDKey.from_seed(seed, network=net)
    # Account level xpub for segwit as example: m/84h/coin/0h
    path = f"m/84h/{coin}h/{account}h"
    acct = hdkey.subkey_for_path(path)
    return acct.extended_public()  # type: ignore[attr-defined]
