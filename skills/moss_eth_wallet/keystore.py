"""Encrypted keystore for ETH root EOA + scoped session key.

Uses Fernet (AES-256) + PBKDF2-HMAC-SHA256 (480k iterations) — identical to BTC wallet.
Root mnemonic NEVER stored cleartext.
Session (privkey + scope) also encrypted at rest.

Storage:
  ~/.moss/wallet/eth/keystore.enc   (root)
  ~/.moss/wallet/eth/session.enc    (session key + scope)
  ~/.moss/wallet/eth/config.json
  ~/.moss/wallet/eth/audit.log
"""
from __future__ import annotations

import base64
import getpass
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

WALLET_BASE = Path.home() / ".moss" / "wallet" / "eth"
KEYSTORE_FILE = WALLET_BASE / "keystore.enc"
SESSION_FILE = WALLET_BASE / "session.enc"
CONFIG_FILE = WALLET_BASE / "config.json"
AUDIT_FILE = WALLET_BASE / "audit.log"

PBKDF2_ITERATIONS = 480000
SALT_LEN = 16


def _get_wallet_dir() -> Path:
    WALLET_BASE.mkdir(parents=True, exist_ok=True)
    try:
        WALLET_BASE.chmod(0o700)
    except PermissionError:
        pass
    return WALLET_BASE


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key = kdf.derive(passphrase.encode("utf-8"))
    return base64.urlsafe_b64encode(key)


def encrypt_mnemonic(mnemonic: str, passphrase: str) -> dict:
    """Encrypt root mnemonic. Returns JSON-serializable dict."""
    salt = os.urandom(SALT_LEN)
    key = _derive_key(passphrase, salt)
    f = Fernet(key)
    token = f.encrypt(mnemonic.encode("utf-8"))
    return {
        "version": 1,
        "salt": base64.b64encode(salt).decode("ascii"),
        "encrypted": base64.b64encode(token).decode("ascii"),
    }


def decrypt_mnemonic(data: dict, passphrase: str) -> str:
    """Decrypt root mnemonic. Raises ValueError on bad passphrase."""
    try:
        salt = base64.b64decode(data["salt"])
        token = base64.b64decode(data["encrypted"])
        key = _derive_key(passphrase, salt)
        f = Fernet(key)
        mnemonic = f.decrypt(token).decode("utf-8")
        return mnemonic.strip()
    except (InvalidToken, KeyError, TypeError, ValueError) as e:
        raise ValueError("Invalid passphrase or corrupted keystore") from e


def encrypt_session(privkey_hex: str, address: str, scope: dict, passphrase: str) -> dict:
    """Encrypt session private key + scope."""
    salt = os.urandom(SALT_LEN)
    key = _derive_key(passphrase, salt)
    f = Fernet(key)
    payload = json.dumps({
        "privkey": privkey_hex,
        "address": address,
        "scope": scope,
    }).encode("utf-8")
    token = f.encrypt(payload)
    return {
        "version": 1,
        "type": "eth-session",
        "salt": base64.b64encode(salt).decode("ascii"),
        "encrypted": base64.b64encode(token).decode("ascii"),
    }


def decrypt_session(data: dict, passphrase: str) -> dict:
    """Return {"privkey": "0x..", "address": "0x..", "scope": {...}}"""
    try:
        salt = base64.b64decode(data["salt"])
        token = base64.b64decode(data["encrypted"])
        key = _derive_key(passphrase, salt)
        f = Fernet(key)
        plain = f.decrypt(token).decode("utf-8")
        return json.loads(plain)
    except (InvalidToken, KeyError, TypeError, ValueError) as e:
        raise ValueError("Invalid passphrase or corrupted session keystore") from e


def get_passphrase(prompt: str = "Enter wallet passphrase: ") -> str:
    env = os.environ.get("MOSSWALLET_PASSPHRASE")
    if env:
        return env
    pw = getpass.getpass(prompt)
    if not pw:
        raise ValueError("Passphrase cannot be empty")
    return pw


def confirm_passphrase() -> str:
    env = os.environ.get("MOSSWALLET_PASSPHRASE")
    if env:
        if not env:
            raise ValueError("Passphrase cannot be empty")
        return env
    while True:
        p1 = getpass.getpass("Enter new passphrase (to encrypt wallet): ")
        if not p1:
            print("Passphrase cannot be empty.")
            continue
        p2 = getpass.getpass("Confirm passphrase: ")
        if p1 != p2:
            print("Passphrases do not match. Try again.")
            continue
        return p1


def load_keystore() -> Optional[dict]:
    _get_wallet_dir()
    if not KEYSTORE_FILE.exists():
        return None
    try:
        with open(KEYSTORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_keystore(data: dict) -> Path:
    _get_wallet_dir()
    with open(KEYSTORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    try:
        KEYSTORE_FILE.chmod(0o600)
    except PermissionError:
        pass
    return KEYSTORE_FILE


def load_session() -> Optional[dict]:
    _get_wallet_dir()
    if not SESSION_FILE.exists():
        return None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_session(data: dict) -> Path:
    _get_wallet_dir()
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    try:
        SESSION_FILE.chmod(0o600)
    except PermissionError:
        pass
    return SESSION_FILE


def load_config() -> dict:
    _get_wallet_dir()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                cfg.setdefault("network", "holesky")
                cfg.setdefault("enforcer", None)
                cfg.setdefault("delegated", False)
                return cfg
        except Exception:
            pass
    return {"network": "holesky", "enforcer": None, "delegated": False, "created_at": None}


def save_config(cfg: dict) -> Path:
    _get_wallet_dir()
    cfg = dict(cfg)
    if "created_at" not in cfg or not cfg.get("created_at"):
        cfg["created_at"] = datetime.now(timezone.utc).isoformat()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    try:
        CONFIG_FILE.chmod(0o600)
    except PermissionError:
        pass
    return CONFIG_FILE


def write_audit(action: str, details: str = "") -> None:
    _get_wallet_dir()
    ts = datetime.now(timezone.utc).isoformat()
    line = f"{ts} | {action} | {details}\n"
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    try:
        AUDIT_FILE.chmod(0o600)
    except PermissionError:
        pass


def is_keystore_present() -> bool:
    return KEYSTORE_FILE.exists()


def is_session_present() -> bool:
    return SESSION_FILE.exists()
