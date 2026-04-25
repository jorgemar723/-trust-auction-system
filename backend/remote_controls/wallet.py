"""
wallet.py

Purpose:
    Blockchain READ interaction layer for wallet balance queries.
"""

from web3 import Web3

from db.repositories.user_repository import UserRepository
from src.services.pricing_service import get_current_eth_usd_price


def get_eth_balance(w3, wallet_address: str) -> float:
    balance_wei = w3.eth.get_balance(wallet_address)
    return float(w3.from_wei(balance_wei, "ether"))


def get_wallet_balance(user_id: int) -> dict | None:
    user_repo = UserRepository()
    wallet_address = user_repo.get_wallet_address_by_user_id(user_id)

    if not wallet_address:
        return None

    try:
        w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
        balance_wei = w3.eth.get_balance(wallet_address)
        balance_eth = round(float(w3.from_wei(balance_wei, "ether")), 2)
    except Exception:
        balance_eth = None

    try:
        eth_price = get_current_eth_usd_price()
    except Exception:
        eth_price = None

    balance_usd = (
        round(balance_eth * eth_price, 2)
        if balance_eth is not None and eth_price is not None
        else None
    )

    return {
        "address": wallet_address,
        "eth": balance_eth,
        "usd": balance_usd,
    }