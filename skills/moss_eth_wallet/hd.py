"""HD derivation for Ethereum (BIP-39 + BIP-44).

Uses eth-account (with unaudited hdwallet features).
Path: m/44'/60'/0'/0/0 for receive (standard).
"""
from __future__ import annotations

from mnemonic import Mnemonic
from eth_account import Account
from eth_account.hdaccount import HDPath  # type: ignore[attr-defined]

MNEMONIC_STRENGTH = 256  # 24 words


def generate_mnemonic() -> str:
    """Generate 24-word BIP-39 English mnemonic."""
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=MNEMONIC_STRENGTH)


def validate_mnemonic(mnemonic: str) -> bool:
    mnemo = Mnemonic("english")
    return mnemo.check(mnemonic.strip())


def mnemonic_to_seed(mnemonic: str) -> bytes:
    mnemo = Mnemonic("english")
    return mnemo.to_seed(mnemonic.strip())


def derive_root_account(mnemonic: str, index: int = 0) -> Account:
    """Return eth_account.Account for m/44'/60'/0'/0/{index}."""
    if not validate_mnemonic(mnemonic):
        raise ValueError("Invalid mnemonic")
    Account.enable_unaudited_hdwallet_features()
    # eth-account supports direct from_mnemonic with path
    path = f"m/44'/60'/0'/0/{index}"
    acct = Account.from_mnemonic(mnemonic, account_path=path)
    return acct


def derive_address(mnemonic: str, index: int = 0) -> str:
    """Return checksummed ETH address."""
    acct = derive_root_account(mnemonic, index)
    return acct.address


def derive_first_addresses(mnemonic: str, count: int = 5) -> list[str]:
    """Return first N receive addresses (index 0..N-1)."""
    addrs: list[str] = []
    for i in range(count):
        addrs.append(derive_address(mnemonic, i))
    return addrs
