"""
mainauction.py

Orchestration layer between Flask (HTTP layer)
and blockchain interaction modules located in remote_controls.
"""

from __future__ import annotations

from pathlib import Path

from .remote_controls import (
    place_bid,
    get_auction_state,
    create_auction,
    load_auction_contract,
    BackendAPIError,
)


# Repo root: trust/ (backend is inside it)
REPO_ROOT = Path(__file__).resolve().parents[1]


# ----------------------------------------------------------
# Configuration
# ----------------------------------------------------------

# NOTE:
# These used to be required when mainauction.py handled
# Web3 initialization directly. That responsibility has
# moved to the remote_controls layer (auction_loader).

# _RPC_URL = "http://127.0.0.1:8545"
# _DEFAULT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"


_DEFAULT_ABI_PATH = (
    REPO_ROOT
    / "Hardhat testing Node"
    / "artifacts"
    / "contracts"
    / "SimpleAuction.sol"
    / "SimpleAuction.json"
)


# ----------------------------------------------------------
# Legacy configuration loader (no longer used)
# ----------------------------------------------------------

# def _get_config() -> tuple[str, Path, str]:
#     """
#     Legacy helper for initializing Web3 + contract.
#     This logic was moved into remote_controls modules.
#     """
#
#     rpc_url = os.getenv("HARDHAT_RPC_URL", _RPC_URL)
#     abi_path = Path(os.getenv("SIMPLE_AUCTION_ABI_PATH", str(_DEFAULT_ABI_PATH)))
#     address = os.getenv("SIMPLE_AUCTION_ADDRESS", _DEFAULT_ADDRESS)
#     return rpc_url, abi_path, address


# ----------------------------------------------------------
# Legacy chain initialization (no longer used)
# ----------------------------------------------------------

# def _init_chain():
#     """
#     Legacy chain initialization.
#     Replaced by auction_loader.load_auction_contract().
#     """
#
#     rpc_url, abi_path, address = _get_config()
#
#     if not abi_path.exists():
#         raise BackendAPIError(
#             code="ABI_NOT_FOUND",
#             message="Contract ABI file not found.",
#             http_status=500,
#             details=(f"ABI not found at: {abi_path}"),
#         )
#
#     # Old Web3 setup logic lived here
#     # It has been moved to remote_controls modules.


# ----------------------------------------------------------
# Auction Operations
# ----------------------------------------------------------

def submit_bid(auction_address: str, user_bid: float) -> dict:
    """
    Submit a bid to a specific auction contract.
    """

    if user_bid <= 0:
        raise BackendAPIError(
            code="INVALID_BID",
            message="Bid amount must be positive.",
            http_status=400,
            details=f"Received bid: {user_bid}",
        )

    w3, contract, account = load_auction_contract(
        auction_address,
        str(_DEFAULT_ABI_PATH)
    )

    try:
        return place_bid(w3, contract, account, user_bid)

    except Exception as e:
        raise BackendAPIError(
            code="BID_FAILED",
            message="Bid transaction failed.",
            http_status=500,
            details=str(e),
        ) from e


def get_state(auction_address: str) -> dict:
    """
    Retrieve current state of a specific auction contract.
    """

    w3, contract, _account = load_auction_contract(
        auction_address,
        str(_DEFAULT_ABI_PATH)
    )

    try:
        return get_auction_state(w3, contract)

    except Exception as e:
        raise BackendAPIError(
            code="CHAIN_CALL_FAILED",
            message="Failed to fetch on-chain state.",
            http_status=500,
            details=str(e),
        ) from e


def create_new_auction(duration_seconds: int) -> dict:
    """
    Create a new auction using the AuctionFactory contract.
    """

    if duration_seconds <= 0:
        raise BackendAPIError(
            code="INVALID_DURATION",
            message="Auction duration must be positive.",
            http_status=400,
            details=f"Received duration: {duration_seconds}",
        )

    try:
        return create_auction(duration_seconds)

    except Exception as e:
        raise BackendAPIError(
            code="AUCTION_CREATION_FAILED",
            message="Failed to create auction.",
            http_status=500,
            details=str(e),
        ) from e