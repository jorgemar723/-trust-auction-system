"""
state.py

Purpose:
    Blockchain READ-ONLY interaction layer for the auction system.

    This module retrieves auction state from the smart contract.
    It does NOT send transactions or modify blockchain state.

    It is intended to be called by:
        - backend.mainauction (controller layer)
        - test_mainauction.py (backend testing)

Responsibilities:
    - Retrieve highest bid
    - Retrieve highest bidder
    - Retrieve auction end time
    - Calculate time remaining using on-chain timestamp

System Position:

    Flask (HTTP layer)
        ↓
    backend.mainauction
        ↓
    state.py  ← THIS FILE (read remote)
        ↓
    Hardhat / Ethereum node
"""

from web3 import Web3


def wei_to_eth(w3: Web3, wei_value: int) -> float:
    """Converts Wei value to Ether."""
    return float(w3.from_wei(wei_value, "ether"))

def get_chain_time(w3: Web3) -> int:
    """
    Retrieve the latest block timestamp from the blockchain.

    Parameters:
        w3 (Web3): Active Web3 connection

    Returns:
        int: Current blockchain time (seconds since epoch)
    """
    latest_block = w3.eth.get_block("latest")
    return int(latest_block["timestamp"])

def get_auction_state(w3: Web3, contract, contract_address: str) -> dict:   
    """
    Read current auction state from a specific auction smart contract.

    This function performs only .call() operations
    (no transactions are sent).

    Assumptions:
        The contract exposes:
            - highestBid() -> uint
            - highestBidder() -> address
            - auctionEndTime() -> uint

        Because contract naming varies across implementations,
        this function attempts multiple common method names.

    Parameters:
        w3 (Web3): Active Web3 connection
        contract: Web3 contract instance representing a specific auction
        contract_address (str): Address of the auction smart contract.
            This uniquely identifies the auction instance and is used by
            the backend and UI to reference specific auctions.

    Returns:
        dict:
            {
                "contract_address": str | None,
                "chain_time": int,
                "highest_bid_wei": int,
                "highest_bid_eth": float,
                "highest_bidder": str | None,
                "auction_end_time": int | None,
                "time_remaining_seconds": int | None,
                "ended": bool | None,
                "status": str | None
            }
    """

    # --- Highest bid ---
    highest_bid_wei = contract.functions.highestBid().call()

    # --- Highest bidder ---
    bidder_fn_candidates = [
        "highestBidder",
        "highestBidderAddress",
        "highest_bidder"
    ]

    highest_bidder = None
    for fn_name in bidder_fn_candidates:
        if hasattr(contract.functions, fn_name):
            highest_bidder = getattr(contract.functions, fn_name)().call()
            break

    # --- Auction end time ---
    end_fn_candidates = [
        "auctionEndTime",
        "endTime",
        "auctionEnd",
        "biddingEnd"
    ]

    auction_end_time = None
    for fn_name in end_fn_candidates:
        if hasattr(contract.functions, fn_name):
            auction_end_time = int(getattr(contract.functions, fn_name)().call())
            break

    # --- Chain time ---
    now = get_chain_time(w3)

    # --- Time remaining calculation ---
    time_remaining = None
    ended = None
    status = None
    
    if auction_end_time is not None:
        time_remaining = max(0, auction_end_time - now)
        ended = (time_remaining == 0)
        status = "CLOSED" if ended else "OPEN"

    return {
        "contract_address": contract_address,
        "chain_time": now,
        "highest_bid_wei": int(highest_bid_wei),
        "highest_bid_eth": wei_to_eth(w3, highest_bid_wei),
        "highest_bidder": highest_bidder,
        "auction_end_time": auction_end_time,
        "time_remaining_seconds": time_remaining,
        "ended": ended,
        "status": status,

    }
    
    