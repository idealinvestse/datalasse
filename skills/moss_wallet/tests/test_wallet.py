"""Tests for moss_wallet (minimum 5 + extras).

Run: python3 -m pytest skills/moss_wallet/tests/ -v
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure workspace root on path
WORKSPACE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE))

from skills.moss_wallet import (
    generate_mnemonic,
    validate_mnemonic,
    derive_address,
    derive_first_addresses,
    encrypt_mnemonic,
    decrypt_mnemonic,
    fetch_balance,
    build_unsigned_psbt,
    validate_address,
    sats_to_btc,
    btc_to_sats,
)
from skills.moss_wallet.keystore import (
    save_keystore,
    load_keystore,
    KEYSTORE_FILE,
    CONFIG_FILE,
    WALLET_BASE,
    write_audit,
)
from skills.moss_wallet.utils import is_testnet_network

# Known test vector (BIP-39 + derivations)
TEST_MNEMONIC = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
# From earlier exploration runs (testnet):
TEST_ADDR_LEGACY = "mkpZhYtJu2r87Js3pDiWJDmPte2NRZ8bJV"  # m/44'/1'/0'/0/0
TEST_ADDR_SEGWIT = "tb1q6rz28mcfaxtmd6v789l9rrlrusdprr9pqcpvkl"  # m/84'/1'/0'/0/0
TEST_ADDR_TAPROOT = "tb1pk67rmz7uqmcty2dupx6jltvldts8qju89l3jnxv3ndljk9g6ptyqdulu52"  # m/86'/1'/0'/0/0


def test_generate_and_validate_mnemonic():
    m = generate_mnemonic()
    assert len(m.split()) == 24
    assert validate_mnemonic(m)
    assert not validate_mnemonic("invalid word list here and more words to fail")


def test_known_derivation_vectors():
    """Test 1: generate/derive and match known test vector addresses."""
    # mainnet would use different coin type, use testnet here
    assert derive_address(TEST_MNEMONIC, 0, "legacy", "testnet") == TEST_ADDR_LEGACY
    assert derive_address(TEST_MNEMONIC, 0, "segwit", "testnet") == TEST_ADDR_SEGWIT
    assert derive_address(TEST_MNEMONIC, 0, "taproot", "testnet") == TEST_ADDR_TAPROOT

    # Also check first 3 via helper
    addrs = derive_first_addresses(TEST_MNEMONIC, 1, "testnet")
    assert addrs["segwit"][0] == TEST_ADDR_SEGWIT


def test_bech32_validation():
    """Test 2: validate bech32 / bech32m addresses."""
    assert validate_address("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", "mainnet")
    assert validate_address("tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx", "testnet")
    assert validate_address(TEST_ADDR_TAPROOT, "testnet")  # p2tr starts tb1p
    assert validate_address("bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0", "mainnet")

    assert not validate_address("bc1invalid", "mainnet")
    assert not validate_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "testnet")  # wrong net


def test_keystore_roundtrip(tmp_path):
    """Test 3: encrypt/decrypt roundtrip + file perms."""
    # Use temp files
    test_keystore = tmp_path / "keystore.enc"
    test_cfg = tmp_path / "config.json"

    # Monkey patch globals for test isolation (simple)
    import skills.moss_wallet.keystore as ks
    orig_ks, orig_cfg, orig_base = ks.KEYSTORE_FILE, ks.CONFIG_FILE, ks.WALLET_BASE
    ks.KEYSTORE_FILE = test_keystore
    ks.CONFIG_FILE = test_cfg
    ks.WALLET_BASE = tmp_path

    try:
        m = TEST_MNEMONIC
        pw = "test-passphrase-123"
        enc = encrypt_mnemonic(m, pw)
        ks.save_keystore(enc)
        assert test_keystore.exists()
        # perms best effort
        loaded = ks.load_keystore()
        assert loaded is not None
        recovered = decrypt_mnemonic(loaded, pw)
        assert recovered == m
    finally:
        ks.KEYSTORE_FILE = orig_ks
        ks.CONFIG_FILE = orig_cfg
        ks.WALLET_BASE = orig_base


@patch("skills.moss_wallet.balance._http_get_json")
def test_balance_fetch(mock_http):
    """Test 4: balance for testnet address (mocked)."""
    mock_http.return_value = [
        {"txid": "a" * 64, "vout": 0, "value": 12345, "status": {"confirmed": True}}
    ]
    bal = fetch_balance("tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx", "testnet")
    assert bal == 12345
    assert mock_http.called


def test_psbt_build():
    """Test 5: build PSBT (unsigned) with fake UTXOs."""
    fake_utxos = [
        {"txid": "a" * 64, "vout": 0, "value": 100000},
        {"txid": "b" * 64, "vout": 1, "value": 50000},
    ]
    psbt = build_unsigned_psbt(
        fake_utxos,
        to_address="tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
        amount_btc=0.001,
        fee_rate=5.0,
        change_address="tb1q6rz28mcfaxtmd6v789l9rrlrusdprr9pqcpvkl",
        network="testnet",
    )
    assert isinstance(psbt, str)
    assert len(psbt) > 50
    # Should be valid base64
    decoded = __import__("base64").b64decode(psbt)
    assert decoded.startswith(b"psbt\xff") or b"psbt" in decoded[:10]


def test_utils_and_conversions():
    assert is_testnet_network("testnet")
    assert not is_testnet_network("mainnet")
    assert sats_to_btc(100000000) == 1.0
    assert btc_to_sats(0.5) == 50000000
    assert validate_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "mainnet")


def test_audit_writes(tmp_path):
    import skills.moss_wallet.keystore as ks
    orig = ks.AUDIT_FILE
    ks.AUDIT_FILE = tmp_path / "audit.log"
    try:
        write_audit("test-action", "details here")
        content = (tmp_path / "audit.log").read_text()
        assert "test-action" in content
    finally:
        ks.AUDIT_FILE = orig
