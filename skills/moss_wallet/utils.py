"""Utilities: address validation, network helpers, audit, constants."""
from __future__ import annotations

import re
from typing import Literal

AddressType = Literal["legacy", "segwit", "taproot"]
Network = Literal["mainnet", "testnet"]

BECH32_MAIN = re.compile(r"^bc1[0-9a-z]{8,}$", re.IGNORECASE)
BECH32_TEST = re.compile(r"^tb1[0-9a-z]{8,}$", re.IGNORECASE)
LEGACY_MAIN = re.compile(r"^1[1-9A-HJ-NP-Za-km-z]{25,34}$")
LEGACY_TEST = re.compile(r"^[mn2][1-9A-HJ-NP-Za-km-z]{25,34}$")  # m/n for P2PKH test, 2 for P2SH


def is_testnet_network(network: str) -> bool:
    return str(network).lower() in ("testnet", "test")


def normalize_network(network: str) -> Network:
    n = str(network).lower()
    if n in ("mainnet", "main", "bitcoin"):
        return "mainnet"
    if n in ("testnet", "test", "tb"):
        return "testnet"
    raise ValueError(f"Unknown network: {network}")


def validate_address(address: str, network: str = "mainnet") -> bool:
    """Basic validation for supported address formats."""
    addr = address.strip()
    is_test = is_testnet_network(network)

    # Bech32 / bech32m (segwit + taproot)
    if (is_test and BECH32_TEST.match(addr)) or (not is_test and BECH32_MAIN.match(addr)):
        # bech32 or bech32m both start bc1/tb1 + alphanum
        # Taproot starts with p after version, but we accept both here (lib will have generated correctly)
        return len(addr) >= 14  # rough

    # Legacy P2PKH
    if (is_test and LEGACY_TEST.match(addr)) or (not is_test and LEGACY_MAIN.match(addr)):
        return True

    return False


def get_api_base(network: str) -> str:
    """Return base URL for public mempool.space style API (preferred)."""
    if is_testnet_network(network):
        return "https://mempool.space/testnet/api"
    return "https://mempool.space/api"


def get_fallback_api_base(network: str) -> str:
    if is_testnet_network(network):
        return "https://blockstream.info/testnet/api"
    return "https://blockstream.info/api"


def short_addr(addr: str) -> str:
    if len(addr) <= 12:
        return addr
    return addr[:6] + "..." + addr[-6:]
