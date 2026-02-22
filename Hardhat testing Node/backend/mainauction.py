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

from .bidding import connect_web3, load_contract, place_bid
from .state import get_auction_state


# --- Initialize blockchain connection (runs once on module import) ---

# Connect to local Hardhat node
w3 = connect_web3()

# Load deployed contract instance
contract = load_contract(
    w3,
    abi_path="Hardhat testing Node/artifacts/contracts/SimpleAuction.sol/SimpleAuction.json",
    contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3"
)

# Use first unlocked account from Hardhat node
account = w3.eth.accounts[0]


def submit_bid(user_bid: float) -> dict:
    """
    High-level bid submission function.

    Called by:
        - Flask routes
        - test_mainauction.py

    Parameters:
        user_bid (float): Bid amount in ETH

    Returns:
        dict:
            {
                "tx_hash": str,
                "highest_bid_wei": int
            }

    Delegates to:
        bidding.place_bid()
    """
    return place_bid(w3, contract, account, user_bid)


def get_state() -> dict:
    """
    Retrieve current auction state.

    Returns:
        dict containing:
            - highest bid (wei and ETH)
            - highest bidder
            - chain time
            - auction end time
            - time remaining
            - ended status

    Delegates to:
        state.get_auction_state()
    """
    return get_auction_state(w3, contract)
