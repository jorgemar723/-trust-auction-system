"""
test_mainauction.py

Purpose:
    Standalone backend test script.

    This file verifies that the orchestration layer (backend.mainauction)
    can successfully:

        1. Retrieve current auction state (read remote)
        2. Submit a bid transaction (write remote)
        3. Retrieve updated state after mutation

    This test intentionally bypasses Flask so we can isolate and validate
    blockchain interaction logic independently of the HTTP layer.

System Flow Being Tested:

    test_mainauction
        ↓
    backend.mainauction
        ↓
    backend.state (read remote)
    backend.bidding (write remote)
        ↓
    Hardhat local blockchain
"""

from backend.mainauction import submit_bid, get_state


# --- Read current auction state before mutation ---
print("=== State before ===")
print(get_state())


# --- Send a new bid transaction ---
# This calls mainauction.submit_bid(),
# which delegates to bidding.place_bid()
print("\n=== Placing bid ===")
result = submit_bid(1)  # 1 ETH bid
print("Bid result:", result)


# --- Read updated auction state after mutation ---
print("\n=== State after ===")
print(get_state())