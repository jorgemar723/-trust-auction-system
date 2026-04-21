"""
wallet.py
 
Purpose:
    Blockchain READ interaction layer for wallet balance queries.
 
    This module is responsible for fetching ETH balances from the
    Ethereum node, with an optional USD conversion using the live
    ETH/USD price.
 
    It does NOT:
        - Handle HTTP requests
        - Handle user input
        - Manage application flow
        - Send transactions
 
    It is called by:
        backend.mainauction (get_eth_balance — used for bid validation)
        Flask routes         (get_wallet_balance — used for balance display)
 
System Position:
 
    Flask (HTTP layer)
        ↓
    backend.mainauction / Flask routes
        ↓
    wallet.py  ← THIS FILE (wallet balance remote)
        ↓
    Hardhat / Ethereum node
"""
 
from web3 import Web3
from db.PostgresDB import PostgresDB
from src.services.pricing_service import get_current_eth_usd_price
 
 
def get_eth_balance(w3, wallet_address: str) -> float:
    """
    Fetch the ETH balance for a wallet address.
 
    Used internally by mainauction.py to validate a bid against the
    bidder's available funds before sending the transaction.
 
    Parameters:
        w3 (Web3):             Active Web3 connection.
        wallet_address (str):  Wallet address to query.
 
    Returns:
        float: Balance in ETH.
    """
    balance_wei = w3.eth.get_balance(wallet_address)
    return float(w3.from_wei(balance_wei, "ether"))
 
 
def get_wallet_balance(user_id: int) -> dict | None:
    """
    Look up a user's wallet address and return their current balance
    in both ETH and USD.
 
    Parameters:
        user_id (int): Internal user ID used to look up the wallet address.
 
    Returns:
        dict:
            {
                "address": str,         # Wallet address
                "eth":     float | None,  # Balance in ETH
                "usd":     float | None,  # Balance in USD (None if price unavailable)
            }
        None: If no wallet address is found for the user.
    """
    db = PostgresDB()
    db.connect()
    wallet_address = db.get_wallet_address_by_user_id(user_id)
    db.close()
 
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
        "eth":     balance_eth,
        "usd":     balance_usd,
    }