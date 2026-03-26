"""
mainauction.py

Orchestration layer between Flask (HTTP layer)
and blockchain interaction modules located in remote_controls.
"""

from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

from db.PostgresDB import PostgresDB
from .remote_controls import (
    place_bid,
    get_auction_state,
    create_auction,
    load_auction_contract,
    BackendAPIError,
)

# Temporary mapping for PROJ-97
# Legacy fallback for local testing.
# PROJ-89 moves state retrieval toward DB-backed contract lookup.

db = PostgresDB()
db.connect()
_AUCTION_REGISTRY = db.get_auction_registry()  # {auction_id: contract_address}
db.close()

_NEXT_AUCTION_ID = max(_AUCTION_REGISTRY.keys(), default=0) + 1

_RPC_URL = "http://127.0.0.1:8545"
_DEFAULT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
_DEFAULT_ABI_PATH = (
    REPO_ROOT
    / "Hardhat testing Node"
    / "artifacts"
    / "contracts"
    / "SimpleAuction.sol"
    / "SimpleAuction.json"
)

# Temporary mapping for PROJ-97
# Maps auction_id → contract_address
# TODO: Replace with database lookup when auctions are stored in SQL
_AUCTION_REGISTRY = {
    1: "0xa16E02E87b7454126E5E10d957A927A7F5B5d2be",
    2: "0xB7A5bd0345EF1Cc5E66bf61BdeC17D2461fBd968",
    3: "0xeEBe00Ac0756308ac4AaBfD76c05c4F3088B8883",
}

_NEXT_AUCTION_ID = max(_AUCTION_REGISTRY.keys(), default=0) + 1


def _get_config():
    """
    Return backend chain configuration.

    Returns:
        tuple[str, Path, str]:
            rpc_url, abi_path, default_address
    """
    return _RPC_URL, _DEFAULT_ABI_PATH, _DEFAULT_ADDRESS


def create_and_register_auction(duration_seconds: int) -> dict:
    """
    Create a new auction on-chain and register it locally.

    Returns:
        dict:
            {
                "auction_id": int,
                "auction_address": str,
                "tx_hash": str
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

    try:
        result = create_auction(duration_seconds)
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


def submit_bid(auction_id: int, user_bid: float) -> dict:
    """
    Submit a bid for a registered auction.

    Parameters:
        auction_id (int): Local backend auction ID
        user_bid (float): Bid amount in ETH
    """
    if user_bid <= 0:
        raise BackendAPIError(
            code="INVALID_BID",
            message="Bid amount must be positive.",
            http_status=400,
            details=f"Received bid: {user_bid}",
        )

    address = _AUCTION_REGISTRY.get(auction_id)
    if not address:
        raise BackendAPIError(
            code="AUCTION_NOT_FOUND",
            message="Auction not found.",
            http_status=404,
            details=f"No contract address found for auction_id={auction_id}",
        )

    _rpc_url, abi_path, _default_address = _get_config()

    try:
        w3, contract, account = load_auction_contract(
            auction_address=address,
            abi_path=str(abi_path),
        )
    except Exception as e:
        raise BackendAPIError(
            code="CONTRACT_LOAD_FAILED",
            message="Failed to load auction contract.",
            http_status=500,
            details=str(e),
        ) from e

    try:
        return place_bid(w3, contract, account, user_bid)

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

    _rpc_url, abi_path, _default_address = _get_config()

    try:
        w3, contract, _account = load_auction_contract(
            auction_address=address,
            abi_path=str(abi_path),
        )
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


def create_new_auction(duration_seconds: int) -> dict:
    """
    Backward-compatible wrapper.

    Prefer create_and_register_auction() for the current controller flow.
    """
    return create_and_register_auction(duration_seconds)