"""
mainauction.py
 
Orchestration layer between Flask (HTTP layer)
and blockchain interaction modules located in remote_controls.
"""
 
from __future__ import annotations
from src.services.pricing_service import get_current_eth_usd_price
from db.PostgresDB import PostgresDB
 
from .remote_controls import (
    place_bid,
    get_auction_state,
    create_auction,
    load_auction_contract,
    BackendAPIError,
)
 
db = PostgresDB()
db.connect()
_AUCTION_REGISTRY = db.get_auction_registry()  # {auction_id: contract_address}
db.close()
 
_NEXT_AUCTION_ID = max(_AUCTION_REGISTRY.keys(), default=0) + 1
 
 
def create_and_register_auction(
    duration_seconds: int,
    wallet_address: str,
    starting_bid: float,
    confirmation_window: int = 259200,  # default: 3 days in seconds
) -> dict:
    """
    Create a new auction on-chain and register it locally.
 
    Args:
        duration_seconds:    How long the auction runs.
        wallet_address:      Seller's wallet address.
        starting_bid:        Minimum opening bid in ETH.
        confirmation_window: Seconds the buyer has to confirm receipt after the
                             auction ends before the seller can claim timeout.
                             Defaults to 3 days (259200 seconds).
 
    Returns:
        dict:
            {
                "auction_id":          int,
                "auction_address":     str,
                "tx_hash":             str,
                "confirmation_window": int,
            }
    """
    global _NEXT_AUCTION_ID
 
    if duration_seconds <= 0:
        raise BackendAPIError(
            code="INVALID_DURATION",
            message="Auction duration must be positive.",
            http_status=400,
            details=f"Received duration: {duration_seconds}",
        )
 
    if starting_bid <= 0:
        raise BackendAPIError(
            code="INVALID_STARTING_BID",
            message="Starting bid must be positive.",
            http_status=400,
            details=f"Received starting_bid: {starting_bid}",
        )
 
    if not wallet_address:
        raise BackendAPIError(
            code="MISSING_WALLET",
            message="User does not have a wallet address configured.",
            http_status=400,
            details="wallet_address is None or empty",
        )
 
    if confirmation_window <= 0:
        raise BackendAPIError(
            code="INVALID_CONFIRMATION_WINDOW",
            message="Confirmation window must be positive.",
            http_status=400,
            details=f"Received confirmation_window: {confirmation_window}",
        )
 
    try:
        result = create_auction(
            duration_seconds,
            wallet_address,
            starting_bid,
            confirmation_window,    # ← passed through to factory.py
        )
        auction_address = result["auction_address"]
 
        auction_id = _NEXT_AUCTION_ID
        _AUCTION_REGISTRY[auction_id] = auction_address
        _NEXT_AUCTION_ID += 1
 
        return {
            "auction_id":           auction_id,
            "auction_address":      auction_address,
            "tx_hash":              result["tx_hash"],
            "confirmation_window":  confirmation_window,
        }
 
    except Exception as e:
        raise BackendAPIError(
            code="AUCTION_CREATION_FAILED",
            message="Failed to create auction.",
            http_status=500,
            details=str(e),
        ) from e
 
 
def submit_bid(auction_id: int, user_bid: float, wallet_address: str) -> dict:
    if user_bid <= 0:
        raise BackendAPIError(
            code="INVALID_BID",
            message="Bid amount must be positive.",
            http_status=400,
            details=f"Received bid: {user_bid}",
        )
 
    if not wallet_address:
        raise BackendAPIError(
            code="MISSING_WALLET",
            message="User does not have a wallet address configured.",
            http_status=400,
            details="wallet_address is None or empty",
        )
 
    db = PostgresDB()
    db.connect()
    address = db.get_contract_address_by_auction_id(auction_id)
    db.close()
 
    if not address:
        raise BackendAPIError(
            code="AUCTION_NOT_FOUND",
            message="Auction not found.",
            http_status=404,
            details=f"No contract address found for auction_id={auction_id}",
        )
 
    w3, contract, _account = load_auction_contract(address)
 
    try:
        return place_bid(w3, contract, wallet_address, user_bid)
    except Exception as e:
        raise BackendAPIError(
            code="BID_FAILED",
            message="Bid transaction failed.",
            http_status=500,
            details=str(e),
        ) from e
 
 
def get_state(auction_id: int) -> dict:
    db = PostgresDB()
    db.connect()
    address = db.get_contract_address_by_auction_id(auction_id)
    db.close()
 
    if not address:
        raise BackendAPIError(
            code="AUCTION_NOT_FOUND",
            message="Auction not found.",
            http_status=404,
            details=f"No contract address found for auction_id={auction_id}",
        )
 
    try:
        w3, contract, _account = load_auction_contract(address)
    except Exception as e:
        raise BackendAPIError(
            code="CONTRACT_LOAD_FAILED",
            message="Failed to load auction contract.",
            http_status=500,
            details=str(e),
        ) from e
 
    try:
        state = get_auction_state(w3, contract, address)
 
        eth_price = get_current_eth_usd_price()
 
        highest_bid_eth = state.get("highest_bid_eth")
 
        if eth_price is not None and highest_bid_eth is not None:
            try:
                highest_bid_usd = highest_bid_eth * eth_price
            except Exception:
                highest_bid_usd = None
        else:
            highest_bid_usd = None
 
        state["highest_bid_usd"] = highest_bid_usd
 
        return state
 
    except Exception as e:
        raise BackendAPIError(
            code="CHAIN_CALL_FAILED",
            message="Failed to fetch on-chain state.",
            http_status=500,
            details=str(e),
        ) from e
 
 
def create_new_auction(duration_seconds: int, wallet_address: str, starting_bid: float) -> dict:
    """
    Backward-compatible wrapper.
 
    Prefer create_and_register_auction() for the current controller flow.
    """
    return create_and_register_auction(duration_seconds, wallet_address, starting_bid)
 