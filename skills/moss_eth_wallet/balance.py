"""Balance helpers for ETH + ERC-20 using web3."""
from __future__ import annotations

from eth_utils import to_checksum_address
from web3 import Web3

from skills.moss_eth_wallet.rpc import get_web3
from skills.moss_eth_wallet.utils import to_checksum

# Minimal ERC-20 ABI for balanceOf + decimals + symbol
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
]


def fetch_eth_balance(address: str, network: str = "holesky") -> int:
    """Return balance in wei (int)."""
    w3 = get_web3(network)
    return w3.eth.get_balance(to_checksum_address(address))


def fetch_erc20_balance(token: str, address: str, network: str = "holesky") -> tuple[int, int, str]:
    """Return (balance_wei, decimals, symbol)."""
    w3 = get_web3(network)
    token = to_checksum(token)
    owner = to_checksum(address)
    contract = w3.eth.contract(address=token, abi=ERC20_ABI)
    bal = contract.functions.balanceOf(owner).call()
    try:
        dec = contract.functions.decimals().call()
    except Exception:
        dec = 18
    try:
        sym = contract.functions.symbol().call()
    except Exception:
        sym = "ERC20"
    return int(bal), int(dec), str(sym)


def format_ether(wei: int) -> str:
    return Web3.from_wei(wei, "ether")  # type: ignore[attr-defined]
