"""
mainauction.py

Purpose:
    Example orchestration layer between the HTTP interface (Flask)
    and the blockchain interaction modules (bidding + state).

IMPORTANT:
    This file serves as a reference implementation demonstrating
    how to call the various blockchain remotes (bidding.py and state.py).

    If you already have an existing main auction controller,
    you may either:

        1. Integrate your existing logic into this file, OR
        2. Import and call the remote functions from your own controller.

    The goal is simply to show how the remotes are intended to be used.

Responsibilities:
    - Initialize Web3 connection
    - Load deployed smart contract
    - Expose high-level functions:
        submit_bid()
        get_state()

This module does NOT:
    - Handle HTTP requests directly
    - Parse user input
    - Contain UI logic

System Architecture:

    Flask (HTTP layer)
        ↓
    mainauction (controller layer — integration point)
        ↓
    bidding.py (write remote)
    state.py (read remote)
        ↓
    Hardhat / Ethereum node
"""
from __future__ import annotations

import os
from pathlib import Path

from db.PostgresDB import PostgresDB
from .bidding import connect_web3, load_contract, place_bid
from .state import get_auction_state
from .errors import BackendAPIError
from .factory import create_auction
from .auction_loader import load_auction_contract

# Temporary mapping for PROJ-97
# Legacy fallback for local testing.
# PROJ-89 moves state retrieval toward DB-backed contract lookup.
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
    _REPO_ROOT
    / "Hardhat testing Node"
    / "artifacts"
    / "contracts"
    / "SimpleAuction.sol"
    / "SimpleAuction.json"
)


def _get_config() -> tuple[str, Path, str]:
    rpc_url = os.getenv("HARDHAT_RPC_URL", _RPC_URL)
    abi_path = Path(os.getenv("SIMPLE_AUCTION_ABI_PATH", str(_DEFAULT_ABI_PATH)))
    address = os.getenv("SIMPLE_AUCTION_ADDRESS", _DEFAULT_ADDRESS)
    return rpc_url, abi_path, address

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

    # 5. Accounts (Hardhat typically provides unlocked accounts)
    if not w3.eth.accounts:
        raise BackendAPIError(
            code="NO_UNLOCKED_ACCOUNTS",
            message="No unlocked accounts available from RPC.",
            http_status=503,
            details="No unlocked accounts available from this RPC"
        )

    account = w3.eth.accounts[0]
    return w3, contract, account

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

    w3, contract, account = _init_chain()
    
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

