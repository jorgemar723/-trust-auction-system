# backend/state.py
from web3 import Web3

def get_chain_time(w3: Web3) -> int:
    """Return latest block timestamp (seconds since epoch)."""
    latest_block = w3.eth.get_block("latest")
    return int(latest_block["timestamp"])

def get_auction_state(w3: Web3, contract) -> dict:
    """
    Reads auction state from the contract and returns a nice dict.

    Assumes your contract has:
      - highestBid() -> uint
      - highestBidder() -> address   (or highestBidder / highestBidderAddress)
      - auctionEndTime() -> uint     (or endTime / auctionEnd / biddingEnd)
    """

    highest_bid_wei = contract.functions.highestBid().call()

    # Highest bidder function name varies a lot across tutorials.
    # Try a few common names.
    bidder_fn_candidates = ["highestBidder", "highestBidderAddress", "highest_bidder"]
    highest_bidder = None
    for fn_name in bidder_fn_candidates:
        if hasattr(contract.functions, fn_name):
            highest_bidder = getattr(contract.functions, fn_name)().call()
            break

    # End time function name also varies.
    end_fn_candidates = ["auctionEndTime", "endTime", "auctionEnd", "biddingEnd"]
    auction_end_time = None
    for fn_name in end_fn_candidates:
        if hasattr(contract.functions, fn_name):
            auction_end_time = int(getattr(contract.functions, fn_name)().call())
            break

    now = get_chain_time(w3)

    time_remaining = None
    ended = None
    if auction_end_time is not None:
        time_remaining = max(0, auction_end_time - now)
        ended = (time_remaining == 0)

    return {
        "chain_time": now,
        "highest_bid_wei": int(highest_bid_wei),
        "highest_bid_eth": float(w3.from_wei(highest_bid_wei, "ether")),
        "highest_bidder": highest_bidder,
        "auction_end_time": auction_end_time,
        "time_remaining_seconds": time_remaining,
        "ended": ended,
    }