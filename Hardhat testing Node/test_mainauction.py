# test_mainauction.py
from backend.mainauction import submit_bid, get_state

print("=== State before ===")
print(get_state())

print("\n=== Placing bid ===")
result = submit_bid(1)
print("Bid result:", result)

print("\n=== State after ===")
print(get_state())