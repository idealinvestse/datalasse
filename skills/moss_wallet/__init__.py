"""moss_wallet skill public API."""
from __future__ import annotations

from skills.moss_wallet.keystore import (
    encrypt_mnemonic,
    decrypt_mnemonic,
    get_passphrase,
    confirm_passphrase,
    load_keystore,
    save_keystore,
    load_config,
    save_config,
    set_network,
    get_current_network,
    bump_receive_index,
    write_audit,
    is_keystore_present,
    KEYSTORE_FILE,
    WALLET_BASE,
)
from skills.moss_wallet.hd import (
    generate_mnemonic,
    validate_mnemonic,
    derive_address,
    derive_first_addresses,
)
from skills.moss_wallet.balance import (
    fetch_balance,
    fetch_balances,
    fetch_utxos,
    sats_to_btc,
    btc_to_sats,
)
from skills.moss_wallet.psbt import (
    build_unsigned_psbt,
    estimate_vsize,
    select_utxos,
)
from skills.moss_wallet.utils import (
    validate_address,
    normalize_network,
    is_testnet_network,
)

__all__ = [
    "generate_mnemonic",
    "validate_mnemonic",
    "derive_address",
    "derive_first_addresses",
    "encrypt_mnemonic",
    "decrypt_mnemonic",
    "get_passphrase",
    "confirm_passphrase",
    "load_keystore",
    "save_keystore",
    "load_config",
    "save_config",
    "set_network",
    "get_current_network",
    "bump_receive_index",
    "write_audit",
    "is_keystore_present",
    "fetch_balance",
    "fetch_balances",
    "fetch_utxos",
    "build_unsigned_psbt",
    "validate_address",
    "sats_to_btc",
    "btc_to_sats",
    "WALLET_BASE",
]
