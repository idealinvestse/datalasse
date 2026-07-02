"""moss_eth_wallet skill public API (EIP-7702 scoped wallet for Moss)."""

from __future__ import annotations

# Keystore (root + session)
from skills.moss_eth_wallet.keystore import (
    encrypt_mnemonic,
    decrypt_mnemonic,
    get_passphrase,
    confirm_passphrase,
    load_keystore,
    save_keystore,
    load_config,
    save_config,
    write_audit,
    is_keystore_present,
    encrypt_session,
    decrypt_session,
    load_session,
    save_session,
    is_session_present,
    WALLET_BASE,
    KEYSTORE_FILE,
    SESSION_FILE,
)

# HD / derivation
from skills.moss_eth_wallet.hd import (
    generate_mnemonic,
    validate_mnemonic,
    derive_address,
    derive_root_account,
)

# Utils
from skills.moss_eth_wallet.utils import (
    normalize_network,
    is_test_network,
    to_checksum,
    validate_eth_address,
    get_rpc_urls,
)

# Balance / RPC
from skills.moss_eth_wallet.balance import (
    fetch_eth_balance,
    fetch_erc20_balance,
    format_ether,
)

# EIP-7702 + session + contract
from skills.moss_eth_wallet.eip7702 import (
    build_authorization,
    sign_authorization,
    get_delegation_code,
    is_delegated,
)
from skills.moss_eth_wallet.contract import (
    SCOPE_ENFORCER_ABI,
    SCOPE_ENFORCER_BYTECODE,
    encode_execute,
    encode_set_scope,
    encode_revoke,
)
from skills.moss_eth_wallet.session import (
    generate_session_key,
    build_session_scope,
    serialize_session,
    parse_session,
)

# Tx building (later modules)
# from skills.moss_eth_wallet.tx import build_scoped_tx ...

__all__ = [
    "generate_mnemonic",
    "validate_mnemonic",
    "derive_address",
    "derive_root_account",
    "encrypt_mnemonic",
    "decrypt_mnemonic",
    "get_passphrase",
    "confirm_passphrase",
    "load_keystore",
    "save_keystore",
    "load_config",
    "save_config",
    "write_audit",
    "is_keystore_present",
    "encrypt_session",
    "decrypt_session",
    "load_session",
    "save_session",
    "is_session_present",
    "WALLET_BASE",
    "normalize_network",
    "is_test_network",
    "to_checksum",
    "validate_eth_address",
    "get_rpc_urls",
    "fetch_eth_balance",
    "fetch_erc20_balance",
    "format_ether",
    "build_authorization",
    "sign_authorization",
    "get_delegation_code",
    "is_delegated",
    "SCOPE_ENFORCER_ABI",
    "SCOPE_ENFORCER_BYTECODE",
    "encode_execute",
    "encode_set_scope",
    "encode_revoke",
    "generate_session_key",
    "build_session_scope",
]
