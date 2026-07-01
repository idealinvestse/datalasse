"""Balance and UTXO fetching via public Bitcoin APIs (no auth, read-only).

Uses mempool.space primary + blockstream.info fallback.
Returns satoshis internally; CLI converts to BTC.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from skills.moss_wallet.utils import get_api_base, get_fallback_api_base, is_testnet_network


def _http_get_json(url: str, timeout: int = 15) -> dict | list:
    req = urllib.request.Request(url, headers={"User-Agent": "moss-wallet/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read().decode("utf-8")
        return json.loads(data)


def fetch_utxos(address: str, network: str = "mainnet") -> list[dict]:
    """Fetch UTXOs for address. Returns list of {txid, vout, value (sats), ...}"""
    bases = [get_api_base(network), get_fallback_api_base(network)]
    last_err = None
    for base in bases:
        url = f"{base}/address/{address}/utxo"
        try:
            data = _http_get_json(url)
            # mempool returns list of dicts with txid, vout, value, status
            if isinstance(data, list):
                return data
            return []
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as e:
            last_err = e
            continue
    # All failed
    raise RuntimeError(f"Failed to fetch UTXOs for {address}: {last_err}")


def fetch_balance(address: str, network: str = "mainnet") -> int:
    """Return confirmed + unconfirmed balance in satoshis for a single address."""
    utxos = fetch_utxos(address, network)
    total = sum(int(u.get("value", 0)) for u in utxos)
    return total


def fetch_balances(addresses: list[str], network: str = "mainnet") -> dict[str, int]:
    """Map address -> balance (sats). Best effort; skips failing addresses."""
    result = {}
    for a in addresses:
        try:
            result[a] = fetch_balance(a, network)
        except Exception:
            result[a] = 0
    return result


def total_balance(balances: dict[str, int]) -> int:
    return sum(balances.values())


def sats_to_btc(sats: int) -> float:
    return sats / 100_000_000.0


def btc_to_sats(btc: float) -> int:
    return int(round(btc * 100_000_000))
