"""Session key generation + scope helpers (client + on-chain grant prep)."""
from __future__ import annotations

import os
import time
from typing import Any

from eth_account import Account
from eth_utils import to_checksum_address

from skills.moss_eth_wallet.utils import to_checksum


def generate_session_key() -> tuple[str, str]:
    """Return (privkey_hex, address)."""
    acct = Account.create()
    priv = "0x" + acct.key.hex()
    return priv, acct.address


def build_session_scope(
    daily_cap_eth: float,
    ttl_days: int,
    whitelist: list[str] | None = None,
) -> dict[str, Any]:
    """Return scope dict suitable for storage + on-chain grant."""
    now = int(time.time())
    exp = now + int(ttl_days * 86400)
    cap_wei = int(daily_cap_eth * 10**18)
    wl = [to_checksum(a) for a in (whitelist or [])]
    return {
        "daily_cap_wei": cap_wei,
        "expiry": exp,
        "whitelist": wl,
        "created_at": now,
    }


def serialize_session(privkey: str, address: str, scope: dict) -> dict:
    return {"privkey": privkey, "address": to_checksum(address), "scope": scope}


def parse_session(data: dict) -> tuple[str, str, dict]:
    """Return priv, addr, scope."""
    return data["privkey"], data["address"], data["scope"]
