
"""
__init__.py
 
Public API for the remote_controls package.
 
Exposes the functions used by backend.mainauction to interact with
the Ethereum node. All blockchain read/write logic lives in the
individual modules below — import from here, not from those files directly.
 
Modules:
    auction_loader  — Web3 connection + contract loading
    factory         — Auction deployment (AuctionFactory contract)
    bidding         — Bid submission (SimpleAuction.bid)
    escrow          — Escrow lifecycle (confirmReceipt, claimAfterTimeout, flagRefund)
    withdrawal      — Pending fund withdrawal (SimpleAuction.withdraw)
    state           — On-chain state reads
    wallet          — Wallet balance queries
    errors          — Shared BackendAPIError exception
"""
 
from .factory        import create_auction
from .auction_loader import load_auction_contract
from .bidding        import place_bid
from .escrow         import (
    confirm_receipt,
    claim_after_timeout,
    flag_refund,
    get_time_remaining_for_confirmation,
)
from .withdrawal     import withdraw
from .state          import get_auction_state
from .errors         import BackendAPIError
 
__all__ = [
    # Auction lifecycle
    "create_auction",
    "load_auction_contract",
    # Bidding
    "place_bid",
    # Escrow
    "confirm_receipt",
    "claim_after_timeout",
    "flag_refund",
    "get_time_remaining_for_confirmation",
    # Withdrawal
    "withdraw",
    # State
    "get_auction_state",
    # Errors
    "BackendAPIError",
]