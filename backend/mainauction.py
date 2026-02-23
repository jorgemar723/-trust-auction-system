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

from .bidding import connect_web3, load_contract, place_bid
from .state import get_auction_state


# Repo root: trust/ (backend/ is inside it)
_REPO_ROOT = Path(__file__).resolve().parents[1]

# Defaults (can be overridden with env vars)
_RPC_URL = os.getenv("HARDHAT_RPC_URL", "http://127.0.0.1:8545")
_DEFAULT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"



# --- Initialize blockchain connection (runs once on module import) ---

# Connect to local Hardhat node
w3 = connect_web3()

# Load deployed contract instance
contract = load_contract(
    w3,
    abi_path="Hardhat testing Node/artifacts/contracts/SimpleAuction.sol/SimpleAuction.json",
    contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3"
)

# ABI path in the repo (note make sure the "Hardhat testing Node" folder is accounted for)
_DEFAULT_ABI_PATH = _REPO_ROOT / "Hardhat testing Node" / "artifacts" / "contracts" / "SimpleAuction.sol" / "SimpleAuction.json"

def _get_config() -> tuple[str, Path, str]:
    rpc_url = os.getenv("HARDHAT_RPC_URL", _RPC_URL)
    abi_path = Path(os.getenv("SIMPLE_AUCTION_ABI_PATH", str(_DEFAULT_ABI_PATH)))
    address = os.getenv("SIMPLE_AUCTION_ADDRESS", _DEFAULT_ADDRESS)
    return rpc_url, abi_path, address

def _init_chain():
    rpc_url, abi_path, address = _get_config()
    
    if not abi_path.exists():
        raise FileNotFoundError(f"ABI not found at: {abi_path}")

    w3 = connect_web3(rpc_url)

    contract = load_contract(
        w3,
        abi_path=str(abi_path),
        contract_address=address,
    )
    
    if not w3.eth.accounts:
        raise RuntimeError("No unlocked accounts available from this RPC")

    account = w3.eth.accounts[0]
    return w3, contract, account

def submit_bid(user_bid: float) -> dict:
    w3, contract, account = _init_chain()
    return place_bid(w3, contract, account, user_bid)


def get_state() -> dict:
    w3, contract, _account = _init_chain()
    return get_auction_state(w3, contract)
    
    