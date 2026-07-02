"""Web3 RPC provider + basic helpers. Public endpoints, fallbacks, no keys."""
from __future__ import annotations

from typing import Any

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware  # for some testnets if needed

from skills.moss_eth_wallet.utils import get_rpc_urls, normalize_network


def get_web3(network: str = "holesky", timeout: int = 30) -> Web3:
    """Return a connected Web3 instance. Tries fallbacks."""
    urls = get_rpc_urls(network)
    last_err: Exception | None = None
    for url in urls:
        try:
            w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": timeout}))
            # Holesky/Sepolia sometimes need POA middleware in older setups, safe to add
            try:
                w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
            except Exception:
                pass
            if w3.is_connected():
                return w3
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Failed to connect to any RPC for {network}: {last_err}")


def get_chain_id(w3: Web3) -> int:
    return w3.eth.chain_id


def get_nonce(w3: Web3, address: str) -> int:
    return w3.eth.get_transaction_count(Web3.to_checksum_address(address))
