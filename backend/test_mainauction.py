"""
Standalone backend test script.

Tests full pipeline:

create auction
↓
read state
↓
place bid
↓
read updated state
"""

from backend.mainauction import (
    create_new_auction,
    submit_bid,
    get_state
)

# --- Create auction ---
print("=== Creating Auction ===")
auction = create_new_auction(3600)

auction_address = auction["auction_address"]

print("Auction address:", auction_address)


# --- Read state before mutation ---
print("\n=== State before ===")
print(get_state(auction_address))


# --- Place a bid ---
print("\n=== Placing bid ===")
result = submit_bid(auction_address, 1)
print("Bid result:", result)


# --- Read updated state ---
print("\n=== State after ===")
print(get_state(auction_address))