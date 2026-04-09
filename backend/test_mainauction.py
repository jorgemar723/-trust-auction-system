
from backend.mainauction import (
    create_and_register_auction,
    submit_bid,
    get_state,
)
 
print("=== Creating Auction ===")
auction = create_and_register_auction(
    duration_seconds=3600,
    wallet_address="0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266",
    starting_bid=0.5,  # ETH
)
 
auction_id = auction["auction_id"]
auction_address = auction["auction_address"]
 
print("Auction ID:", auction_id)
print("Auction address:", auction_address)
 
print("\n=== State before ===")
print(get_state(auction_id))
 
print("\n=== Placing bid ===")
result = submit_bid(auction_id, 1, "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266")
print("Bid result:", result)
 
print("\n=== State after ===")
print(get_state(auction_id))