"""
mainauction.py

Orchestration layer between Flask (HTTP layer)
and blockchain interaction modules located in remote_controls.
"""

from __future__ import annotations

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


def create_and_register_auction(duration_seconds: int, wallet_address: str) -> dict:
    """
    Create a new auction on-chain and register it locally.

    Returns:
        dict:
            {
                "auction_id": int,
                "auction_address": str,
                "tx_hash": str,
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

    if not wallet_address:
        raise BackendAPIError(
            code="MISSING_WALLET",
            message="User does not have a wallet address configured.",
            http_status=400,
            details="wallet_address is None or empty",
        )

    try:
        result = create_auction(duration_seconds, wallet_address)
        auction_address = result["auction_address"]

        auction_id = _NEXT_AUCTION_ID
        _AUCTION_REGISTRY[auction_id] = auction_address
        _NEXT_AUCTION_ID += 1

        return {
            "auction_id": auction_id,
            "auction_address": auction_address,
            "tx_hash": result["tx_hash"],
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
        return get_auction_state(w3, contract, address)
    except Exception as e:
        raise BackendAPIError(
            code="CHAIN_CALL_FAILED",
            message="Failed to fetch on-chain state.",
            http_status=500,
            details=str(e),
        ) from e


def create_new_auction(duration_seconds: int, wallet_address: str) -> dict:
    """
    Backward-compatible wrapper.

    Prefer create_and_register_auction() for the current controller flow.
    """
    return create_and_register_auction(duration_seconds, wallet_address)