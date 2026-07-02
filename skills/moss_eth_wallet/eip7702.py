"""EIP-7702 delegation helpers using eth-account + web3 (v7+)."""
from __future__ import annotations

from typing import Any

from eth_account import Account
from eth_utils import to_checksum_address

DELEGATION_PREFIX = b"\xef\x01\x00"


def get_delegation_code(delegate_addr: str) -> bytes:
    """Return the 23-byte delegation designator (0xef0100 + 20-byte addr)."""
    addr = to_checksum_address(delegate_addr)
    return DELEGATION_PREFIX + bytes.fromhex(addr[2:])


def build_authorization(delegate_addr: str, chain_id: int, nonce: int) -> dict:
    """Build unsigned authorization dict for EIP-7702."""
    return {
        "chainId": chain_id,
        "address": to_checksum_address(delegate_addr),
        "nonce": nonce,
    }


def sign_authorization(auth: dict, private_key: str | bytes) -> dict:
    """Sign the authorization using root private key. Returns signed auth ready for tx."""
    signed = Account.sign_authorization(auth, private_key)
    # signed contains: address, chainId, nonce, yParity, r, s (or v in older)
    return {
        "chainId": signed.chain_id,
        "address": signed.address,
        "nonce": signed.nonce,
        "yParity": signed.y_parity,
        "r": signed.r,
        "s": signed.s,
    }


def is_delegated(w3: Any, address: str) -> bool:
    """True if account code starts with 0xef0100 (delegated via 7702)."""
    code = w3.eth.get_code(to_checksum_address(address))
    return code[:3] == DELEGATION_PREFIX if code else False
