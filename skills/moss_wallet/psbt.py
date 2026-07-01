"""PSBT (BIP-174) builder for unsigned transactions (read-only mode).

Builds base64 PSBT from UTXOs + destination + change.
Does NOT sign or broadcast. Private keys never enter PSBT in this mode.
"""
from __future__ import annotations

import base64
from typing import Any

from bitcoinlib.transactions import Transaction, Input, Output
from bitcoinlib.encoding import varstr

from skills.moss_wallet.balance import btc_to_sats, sats_to_btc
from skills.moss_wallet.utils import is_testnet_network


def estimate_vsize(num_inputs: int, num_outputs: int, is_segwit: bool = True) -> int:
    """Rough vsize estimate in vbytes for fee calc (segwit default)."""
    base = 10 + (num_inputs * 41) + (num_outputs * 31)
    if is_segwit:
        base += 2 + (num_inputs * 27)
    return max(base, 200)


def select_utxos(utxos: list[dict], needed_sats: int) -> list[dict]:
    """Simple largest-first selection."""
    sorted_utxos = sorted(utxos, key=lambda u: u.get("value", 0), reverse=True)
    selected = []
    total = 0
    for u in sorted_utxos:
        selected.append(u)
        total += int(u.get("value", 0))
        if total >= needed_sats:
            break
    if total < needed_sats:
        raise ValueError(f"Insufficient funds: have {total}, need {needed_sats}")
    return selected


def build_unsigned_psbt(
    utxos: list[dict],
    to_address: str,
    amount_btc: float,
    fee_rate: float,
    change_address: str,
    network: str = "mainnet",
) -> str:
    """Build and return base64-encoded unsigned PSBT."""
    amount_sats = btc_to_sats(amount_btc)
    est_vsize = estimate_vsize(2, 2, is_segwit=True)
    fee_sats = int(fee_rate * est_vsize)
    total_needed = amount_sats + fee_sats

    selected = select_utxos(utxos, total_needed)
    selected_value = sum(int(u.get("value", 0)) for u in selected)
    change_sats = selected_value - amount_sats - fee_sats
    if change_sats < 0:
        raise ValueError("Change negative after fee")

    net = "testnet" if is_testnet_network(network) else "bitcoin"

    t = Transaction(network=net)

    for u in selected:
        inp = Input(
            prev_txid=u["txid"],
            output_n=u["vout"],
            value=int(u.get("value", 0)),
            network=net,
        )
        t.inputs.append(inp)

    out_main = Output(amount_sats, address=to_address, network=net)
    t.outputs.append(out_main)

    if change_sats > 546:
        out_change = Output(change_sats, address=change_address, network=net)
        t.outputs.append(out_change)

    psbt_bytes = _build_minimal_unsigned_psbt_bytes(t, selected, net)
    return base64.b64encode(psbt_bytes).decode("ascii")


def _build_minimal_unsigned_psbt_bytes(tx: Transaction, selected_utxos: list[dict], network: str) -> bytes:
    """Minimal valid unsigned PSBT (starts with psbt magic)."""
    try:
        raw_tx = tx.raw() if hasattr(tx, "raw") and callable(getattr(tx, "raw", None)) else tx.serialize()
    except Exception:
        raw_tx = tx.serialize()
    if isinstance(raw_tx, str):
        raw_tx = bytes.fromhex(raw_tx)

    out = bytearray(b"psbt\xff")
    # Global unsigned tx (key 0)
    out += b"\x01\x00"
    out += varstr(raw_tx)
    out += b"\x00"

    for _ in tx.inputs:
        out += b"\x00"
    for _ in tx.outputs:
        out += b"\x00"

    return bytes(out)
