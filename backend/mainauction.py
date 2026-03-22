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

from .bidding import connect_web3, load_contract, place_bid
from .state import get_auction_state
from .errors import BackendAPIError
from .factory import create_auction
from .auction_loader import load_auction_contract

# Temporary mapping for PROJ-97
# Maps auction_id → contract_address
# TODO: Replace with database lookup when auctions are stored in SQL
_AUCTION_REGISTRY = {
    1: "0x5FbDB2315678afecb367f032d93F642f64180aa3",
    2: "0xCafac3dD18aC6c6e92c921884f9E4176737C052c",
}

_NEXT_AUCTION_ID = max(_AUCTION_REGISTRY.keys(), default=0) + 1

def create_and_register_auction(duration_seconds: int) -> dict:
    global _NEXT_AUCTION_ID

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

# Repo root: trust/ (backend/ is inside it)
_REPO_ROOT = Path(__file__).resolve().parents[1]

# Defaults (can be overridden with env vars)
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


# ----------------------------------------------------------
# Legacy configuration loader (no longer used)
# ----------------------------------------------------------

def _init_chain_for_address(address: str):
    rpc_url, abi_path, _default_address = _get_config()

    # 1. ABI existence (fast fail)
    if not abi_path.exists():
        raise BackendAPIError(
            code="ABI_NOT_FOUND",
            message="Contract ABI file not found.",
            http_status=500,
            details=(f"ABI not found at: {abi_path}"),
        )
        
    # 2. RPC reachable
    try:
        w3 = connect_web3(rpc_url)
    except Exception as e:
        raise BackendAPIError(
            code="RPC_UNREACHABLE",
            message="Hardhat node not reachable.",
            http_status=503,
            details=f"Hardhat node not reachable at {rpc_url}",
        ) from e
    
    # 3. Contract load (ABI/address)
    try:
        contract = load_contract(
            w3,
            abi_path=str(abi_path),
            contract_address=address,
        )
    except Exception as e:
        raise BackendAPIError(
            code="CONTRACT_LOAD_FAILED",
            message="Failed to load contract configuration.",
            http_status=500,
            details=f"Failed to load contract (ABI/address). Address={address}, ABI={abi_path}",
        ) from e
        
    # 4. Verify contract deployed at address
    try:
        code_bytes = w3.eth.get_code(address)
        if not code_bytes or len(code_bytes) == 0:
            raise BackendAPIError(
                code="CONTRACT_NOT_DEPLOYED",
                message="Contract not deployed at configured address.",
                http_status=500,
                details=f"Contract not deployed at {address}. Run deploy script against this node.",
            )
    except BackendAPIError:
        raise
    except Exception as e:
        raise BackendAPIError(
            code="CONTRACT_DEPLOY_CHECK_FAILED",
            message="Could not verify contract deployment.",
            http_status=500,
            details=f"Could not verify contract deployment at {address}",
        ) from e

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


def _init_chain():
    _rpc_url, _abi_path, address = _get_config()
    return _init_chain_for_address(address)


def submit_bid(user_bid: float) -> dict:
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
    
def get_state(auction_id: int) -> dict:
    address = _AUCTION_REGISTRY.get(auction_id)
    if not address:
        raise BackendAPIError(
            code="AUCTION_NOT_FOUND",
            message="Auction not found.",
            http_status=404,
            details=f"No contract address found for auction_id={auction_id}",
        )
    
    _rpc_url, abi_path, _default_address = _get_config()
        
    w3, contract, _account = load_auction_contract(
        auction_address=address,
        abi_path=str(abi_path),
    )

    
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