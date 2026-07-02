"""Transaction building for scoped sends and admin actions.

- Normal spend: session signs tx to EOA with data = execute(recipient, value, b'')
- Token spend: data = execute(token, 0, transfer_calldata)
- Admin (grant/revoke): root signs direct tx to EOA with setScope/revoke data
"""
from __future__ import annotations

from typing import Any

from eth_account import Account
from eth_utils import to_checksum_address
from web3 import Web3

from skills.moss_eth_wallet.contract import (
    SCOPE_ENFORCER_ABI,
    encode_execute,
    encode_set_scope,
    encode_revoke,
)
from skills.moss_eth_wallet.rpc import get_nonce, get_web3
from skills.moss_eth_wallet.utils import normalize_network, to_checksum


def build_scoped_call(
    eoa_addr: str,
    to: str,
    value_wei: int,
    data: bytes = b"",
) -> dict:
    """Return tx dict: to=EOA, data=execute(to,value,data), value=0."""
    call_data = encode_execute(to, value_wei, data)
    return {
        "to": to_checksum(eoa_addr),
        "value": 0,
        "data": call_data,
    }


def build_token_transfer_data(recipient: str, amount_wei: int) -> bytes:
    """Minimal ERC20 transfer(address,uint256) selector + encode."""
    from eth_abi import encode
    selector = bytes.fromhex("a9059cbb")
    args = encode(["address", "uint256"], [to_checksum(recipient), amount_wei])
    return selector + args


def estimate_gas(w3: Web3, tx: dict, from_addr: str) -> int:
    tx = dict(tx)
    tx["from"] = to_checksum(from_addr)
    try:
        return w3.eth.estimate_gas(tx)
    except Exception:
        return 120_000  # safe default for simple execute


def sign_and_serialize(
    w3: Web3,
    tx: dict,
    private_key: str,
    chain_id: int | None = None,
    gas_limit: int | None = None,
    gas_price_gwei: float | None = None,
) -> str:
    """Sign tx and return raw hex (ready for sendRaw). Does not broadcast."""
    if chain_id is None:
        chain_id = w3.eth.chain_id
    tx = dict(tx)
    tx["chainId"] = chain_id
    tx["nonce"] = get_nonce(w3, tx.get("from") or Account.from_key(private_key).address)
    if gas_limit is None:
        gas_limit = estimate_gas(w3, tx, tx.get("from", Account.from_key(private_key).address))
    tx["gas"] = gas_limit
    if gas_price_gwei is None:
        # simple legacy for broad compat on testnets
        tx["gasPrice"] = w3.eth.gas_price
    else:
        tx["gasPrice"] = Web3.to_wei(gas_price_gwei, "gwei")
    signed = Account.sign_transaction(tx, private_key)
    return signed.raw_transaction.hex()


def build_grant_tx(eoa: str, session: str, cap_wei: int, expiry: int, wl: list[str]) -> dict:
    data = encode_set_scope(session, cap_wei, expiry, wl)
    return {"to": to_checksum(eoa), "value": 0, "data": data}


def build_revoke_tx(eoa: str, session: str) -> dict:
    data = encode_revoke(session)
    return {"to": to_checksum(eoa), "value": 0, "data": data}
