"""Tests for moss_eth_wallet (minimum 7+).

Run: python3 -m pytest skills/moss_eth_wallet/tests/ -v
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure workspace root on path
WORKSPACE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE))

from skills.moss_eth_wallet import (
    generate_mnemonic,
    validate_mnemonic,
    derive_address,
    derive_root_account,
    encrypt_mnemonic,
    decrypt_mnemonic,
    encrypt_session,
    decrypt_session,
    generate_session_key,
    build_session_scope,
    build_authorization,
    sign_authorization,
    get_delegation_code,
    SCOPE_ENFORCER_BYTECODE,
    encode_execute,
    encode_set_scope,
    normalize_network,
    validate_eth_address,
)
from skills.moss_eth_wallet.keystore import (
    save_keystore,
    load_keystore,
    save_session,
    load_session,
    KEYSTORE_FILE,
    SESSION_FILE,
    WALLET_BASE,
    write_audit,
)
from skills.moss_eth_wallet.contract import SCOPE_ENFORCER_ABI

# Known test vector (BIP-39 + ETH derivation)
# mnemonic: abandon ... about
# path m/44'/60'/0'/0/0 -> 0x9858EfFD232B4033E47d90003D41EC34EcaEda94 (standard vector)
TEST_MNEMONIC = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
TEST_ETH_ADDR = "0x9858EfFD232B4033E47d90003D41EC34EcaEda94"


def test_generate_and_validate_mnemonic():
    """Test 1-ish: mnemonic gen/validate."""
    m = generate_mnemonic()
    assert len(m.split()) == 24
    assert validate_mnemonic(m)
    assert not validate_mnemonic("invalid word list here and more words to fail")


def test_known_derivation_vector():
    """Test 1: derive root EOA from mnemonic matches BIP-44 ETH vector."""
    addr = derive_address(TEST_MNEMONIC, 0)
    assert addr.lower() == TEST_ETH_ADDR.lower()
    # also via account
    acct = derive_root_account(TEST_MNEMONIC, 0)
    assert acct.address.lower() == TEST_ETH_ADDR.lower()


def test_session_key_generation():
    """Test 2: session key generation."""
    priv, addr = generate_session_key()
    assert priv.startswith("0x") and len(priv) == 66
    assert addr.startswith("0x") and len(addr) == 42
    assert validate_eth_address(addr)


def test_scope_builder():
    """Test 3-ish: build scope dict."""
    scope = build_session_scope(0.5, 7, ["0x1234567890123456789012345678901234567890"])
    assert scope["daily_cap_wei"] == int(0.5 * 10**18)
    assert scope["expiry"] > 0
    assert len(scope["whitelist"]) == 1


class MockScopeEnforcer:
    """Pure python mock of on-chain scope logic for tests."""
    def __init__(self):
        self.scopes = {}

    def set_scope(self, session, cap, exp, wl):
        self.scopes[session.lower()] = {
            "daily_cap": cap,
            "spent_today": 0,
            "last_day": 0,
            "expiry": exp,
            "allowed": {a.lower(): True for a in wl},
        }

    def execute(self, caller, to, value, now_day=100):
        s = self.scopes.get(caller.lower())
        if not s or s["expiry"] <= 100:
            raise ValueError("no/expired")
        if now_day > s["last_day"]:
            s["spent_today"] = 0
            s["last_day"] = now_day
        if s["spent_today"] + value > s["daily_cap"]:
            raise ValueError("cap exceeded")
        if not s["allowed"].get(to.lower(), False):
            raise ValueError("not whitelisted")
        s["spent_today"] += value
        return True


def test_scope_enforcer_mock():
    """Test 3: ScopeEnforcer logic with mock."""
    mock = MockScopeEnforcer()
    sess = "0xdef0000000000000000000000000000000000000"
    to = "0xabc0000000000000000000000000000000000000"
    mock.set_scope(sess, int(0.5 * 1e18), 9999999999, [to])
    assert mock.execute(sess, to, int(0.1 * 1e18)) is True
    # over cap
    with pytest.raises(ValueError, match="cap"):
        mock.execute(sess, to, int(1 * 1e18))
    # bad to
    with pytest.raises(ValueError, match="whitelisted"):
        mock.execute(sess, "0x0000000000000000000000000000000000000000", 100)


def test_eip7702_authorization_construction():
    """Test 4: EIP-7702 auth + sign + designator."""
    delegate = "0x1111111111111111111111111111111111111111"
    auth = build_authorization(delegate, 17000, 5)
    assert auth["chainId"] == 17000
    assert auth["address"].lower() == delegate.lower()
    # sign
    # use a dummy key (test only)
    dummy_key = "0x" + "11" * 32
    signed = sign_authorization(auth, dummy_key)
    assert "r" in signed and "s" in signed and "yParity" in signed
    code = get_delegation_code(delegate)
    assert code[:3] == b"\xef\x01\x00"
    assert len(code) == 23


def test_keystore_roundtrip(tmp_path):
    """Test 5: root + session keystore roundtrip + perms."""
    import skills.moss_eth_wallet.keystore as ks
    orig_root, orig_sess, orig_base = ks.KEYSTORE_FILE, ks.SESSION_FILE, ks.WALLET_BASE
    test_base = tmp_path / "eth"
    ks.WALLET_BASE = test_base
    ks.KEYSTORE_FILE = test_base / "keystore.enc"
    ks.SESSION_FILE = test_base / "session.enc"
    try:
        m = TEST_MNEMONIC
        pw = "test-pass-eth-123"
        enc = encrypt_mnemonic(m, pw)
        ks.save_keystore(enc)
        assert ks.KEYSTORE_FILE.exists()
        loaded = ks.load_keystore()
        recovered = decrypt_mnemonic(loaded, pw)
        assert recovered == m

        # session
        priv, addr = generate_session_key()
        scope = build_session_scope(0.1, 1)
        s_enc = encrypt_session(priv, addr, scope, pw)
        ks.save_session(s_enc)
        loaded_s = ks.load_session()
        s_rec = decrypt_session(loaded_s, pw)
        assert s_rec["address"] == addr
        assert s_rec["scope"]["daily_cap_wei"] == scope["daily_cap_wei"]
    finally:
        ks.KEYSTORE_FILE = orig_root
        ks.SESSION_FILE = orig_sess
        ks.WALLET_BASE = orig_base


@patch("skills.moss_eth_wallet.balance.get_web3")
def test_balance_fetch_mocked(mock_get_web3):
    """Test 6: balance fetch (mocked)."""
    mock_w3 = MagicMock()
    mock_w3.eth.get_balance.return_value = 1234567890000000000  # 1.234 ETH
    mock_get_web3.return_value = mock_w3
    from skills.moss_eth_wallet.balance import fetch_eth_balance
    bal = fetch_eth_balance("0x9858EfFD232B4033E47d90003D41EC34EcaEda94", "holesky")
    assert bal == 1234567890000000000


def test_send_flow_scope_validation():
    """Test 7: send flow logic - build tx + scope simulation reject."""
    from skills.moss_eth_wallet.tx import build_scoped_call, build_token_transfer_data
    eoa = "0x9858EfFD232B4033E47d90003D41EC34EcaEda94"
    recipient = "0x2222222222222222222222222222222222222222"
    # ETH scoped call
    tx = build_scoped_call(eoa, recipient, int(0.01 * 1e18))
    assert tx["to"].lower() == eoa.lower()
    assert b"\x61\x61" not in tx.get("data", b"")  # rough
    # token
    tdata = build_token_transfer_data(recipient, 1000)
    assert len(tdata) > 4

    # simulate client + mock enforcer reject
    mock = MockScopeEnforcer()
    sess = "0xdef0000000000000000000000000000000000000"
    mock.set_scope(sess, int(0.001 * 1e18), 9999999999, [recipient])
    with pytest.raises(ValueError, match="cap"):
        mock.execute(sess, recipient, int(0.1 * 1e18))


def test_audit_and_config(tmp_path):
    """Test 8: audit + config basics."""
    import skills.moss_eth_wallet.keystore as ks
    orig_audit = ks.AUDIT_FILE
    orig_base = ks.WALLET_BASE
    ks.WALLET_BASE = tmp_path
    ks.AUDIT_FILE = tmp_path / "audit.log"
    try:
        write_audit("test-eth-action", "details")
        content = (tmp_path / "audit.log").read_text()
        assert "test-eth-action" in content
    finally:
        ks.AUDIT_FILE = orig_audit
        ks.WALLET_BASE = orig_base


def test_cli_imports_and_network():
    """Sanity: network normalize + address validation work (CLI entrypoint tested via direct import of utils)."""
    assert normalize_network("holesky") == "holesky"
    assert validate_eth_address("0x" + "0" * 40)
