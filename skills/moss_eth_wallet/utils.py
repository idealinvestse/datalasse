"""Utilities for ETH wallet: networks, addresses, RPC config."""
from __future__ import annotations

from typing import Literal

from eth_utils import to_checksum_address, is_address  # provided by eth-account/web3

Network = Literal["holesky", "sepolia", "mainnet"]

# Reliable public RPCs (2026) — Holesky has good Pectra support
RPC_URLS: dict[str, list[str]] = {
    "holesky": [
        "https://ethereum-holesky-rpc.publicnode.com",
        "https://rpc.holesky.ethpandaops.io",
        "https://holesky.drpc.org",
    ],
    "sepolia": [
        "https://ethereum-sepolia-rpc.publicnode.com",
        "https://rpc.sepolia.org",
    ],
    "mainnet": [
        "https://ethereum-rpc.publicnode.com",
        "https://eth.llamarpc.com",
    ],
}


def normalize_network(network: str) -> Network:
    n = network.lower().strip()
    if n in ("holesky", "hole", "h"):
        return "holesky"
    if n in ("sepolia", "sep", "s"):
        return "sepolia"
    if n in ("mainnet", "main", "eth"):
        return "mainnet"
    raise ValueError(f"Unsupported network: {network}. Use holesky|sepolia|mainnet")


def is_test_network(network: str) -> bool:
    return normalize_network(network) != "mainnet"


def to_checksum(addr: str) -> str:
    if not addr:
        raise ValueError("Empty address")
    return to_checksum_address(addr)


def validate_eth_address(addr: str) -> bool:
    try:
        return bool(is_address(addr))
    except Exception:
        return False


def get_rpc_urls(network: str) -> list[str]:
    net = normalize_network(network)
    return RPC_URLS.get(net, RPC_URLS["holesky"])


def short_addr(addr: str) -> str:
    if len(addr) <= 12:
        return addr
    return addr[:6] + "..." + addr[-4:]
