"""Encrypted keystore for BTC HD wallet mnemonic.

Uses Fernet (AES-256) with PBKDF2-HMAC-SHA256 key derivation (480k iterations).
Mnemonic is NEVER stored in cleartext on disk.

Storage: ~/.moss/wallet/btc/keystore.enc (0600)
Optional: ~/.moss/wallet/btc/config.json (0600) for network + last_receive_index
"""
from __future__ import annotations

import base64
import getpass
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

WALLET_BASE = Path.home() / ".moss" / "wallet" / "btc"
KEYSTORE_FILE = WALLET_BASE / "keystore.enc"
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
    """Encrypt mnemonic. Returns dict suitable for JSON storage."""
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
    """Decrypt and return mnemonic string. Raises on bad passphrase or data."""
    try:
        salt = base64.b64decode(data["salt"])
        token = base64.b64decode(data["encrypted"])
        key = _derive_key(passphrase, salt)
        f = Fernet(key)
        mnemonic = f.decrypt(token).decode("utf-8")
        return mnemonic.strip()
    except (InvalidToken, KeyError, TypeError, ValueError) as e:
        raise ValueError("Invalid passphrase or corrupted keystore") from e


def get_passphrase(prompt: str = "Enter wallet passphrase: ") -> str:
    """Prompt for passphrase (no echo). Falls back to env var MOSSWALLET_PASSPHRASE."""
    env = os.environ.get("MOSSWALLET_PASSPHRASE")
    if env:
        return env
    pw = getpass.getpass(prompt)
    if not pw:
        raise ValueError("Passphrase cannot be empty")
    return pw


def confirm_passphrase() -> str:
    """Prompt twice for new passphrase and confirm match."""
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
    """Load encrypted data dict from disk or None if missing."""
    _get_wallet_dir()
    if not KEYSTORE_FILE.exists():
        return None
    try:
        with open(KEYSTORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_keystore(data: dict) -> Path:
    """Write encrypted data. Enforce 0600 perms."""
    _get_wallet_dir()
    with open(KEYSTORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    try:
        KEYSTORE_FILE.chmod(0o600)
    except PermissionError:
        pass
    return KEYSTORE_FILE


def load_config() -> dict:
    """Load public config (network, last_receive_index etc). Defaults to mainnet."""
    _get_wallet_dir()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if "network" not in cfg:
                    cfg["network"] = "mainnet"
                if "last_receive_index" not in cfg:
                    cfg["last_receive_index"] = 0
                return cfg
        except Exception:
            pass
    return {"network": "mainnet", "last_receive_index": 0, "created_at": None}


def save_config(cfg: dict) -> Path:
    """Save config with 0600 perms."""
    _get_wallet_dir()
    cfg = dict(cfg)  # copy
    if "created_at" not in cfg or not cfg["created_at"]:
        cfg["created_at"] = datetime.now(timezone.utc).isoformat()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    try:
        CONFIG_FILE.chmod(0o600)
    except PermissionError:
        pass
    return CONFIG_FILE


def set_network(network: str) -> dict:
    """Update network in config. network in ('mainnet', 'testnet')."""
    if network not in ("mainnet", "testnet"):
        raise ValueError("network must be mainnet or testnet")
    cfg = load_config()
    cfg["network"] = network
    save_config(cfg)
    return cfg


def get_current_network(testnet_flag: bool = False) -> str:
    """Resolve effective network: flag overrides config."""
    if testnet_flag:
        return "testnet"
    cfg = load_config()
    return cfg.get("network", "mainnet")


def bump_receive_index() -> int:
    """Increment and return new last_receive_index."""
    cfg = load_config()
    idx = int(cfg.get("last_receive_index", 0)) + 1
    cfg["last_receive_index"] = idx
    save_config(cfg)
    return idx


def write_audit(action: str, details: str = "") -> None:
    """Append timestamped audit line. Enforce 0600."""
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