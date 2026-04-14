
from web3 import Web3
from backend.mainauction import (
    create_and_register_auction,
    submit_bid,
    get_state,
)
 
# ─── Hardhat default accounts ─────────────────────────────────────────────────
# Account[0] — used as the factory deployer AND admin (same address in Hardhat)
# Account[1] — seller
# Account[2] — bidder / buyer
ADMIN   = "0xf39Fd6e51aad88F6f4ce6aB8827279cffFb92266"   # account[0]  (factory deployer = admin)
SELLER  = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"   # account[1]
BIDDER  = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"   # account[2]
 
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
 
 
def advance_time(seconds: int):
    """
    Fast-forward the Hardhat node clock by `seconds`.
    Mines a new block so block.timestamp reflects the change immediately.
    """
    w3.provider.make_request("evm_increaseTime", [seconds])
    w3.provider.make_request("evm_mine", [])
 
 
def print_escrow_state(label: str, auction_id: int):
    state = get_state(auction_id)
    print(f"\n--- {label} ---")
    print(f"  status:                       {state['status']}")
    print(f"  ended:                        {state['ended']}")
    print(f"  highest_bid_eth:              {state['highest_bid_eth']} ETH")
    print(f"  highest_bidder:               {state['highest_bidder']}")
    print(f"  escrow_amount_eth:            {state['escrow_amount_eth']} ETH")
    print(f"  buyer_confirmed:              {state['buyer_confirmed']}")
    print(f"  escrow_settled:               {state['escrow_settled']}")
    print(f"  refund_flagged:               {state['refund_flagged']}")
    print(f"  confirmation_window_seconds:  {state['confirmation_window_seconds']}")
    print(f"  escrow_release_timeout:       {state['escrow_release_timeout_readable']}")
    print(f"  time_remaining_confirmation:  {state['time_remaining_for_confirmation']}s")
 
 
# ══════════════════════════════════════════════════════════════════════════════
# EXISTING TESTS — unchanged
# ══════════════════════════════════════════════════════════════════════════════
 
print("=== Creating Auction ===")
auction = create_and_register_auction(
    duration_seconds=3600,
    wallet_address=SELLER,
    starting_bid=0.5,   # ETH
)
 
auction_id      = auction["auction_id"]
auction_address = auction["auction_address"]
 
print("Auction ID:",      auction_id)
print("Auction address:", auction_address)
 
print("\n=== State before bid ===")
print(get_state(auction_id))
 
print("\n=== Placing bid ===")
result = submit_bid(auction_id, 1.0, BIDDER)
print("Bid result:", result)
 
print("\n=== State after bid ===")
print(get_state(auction_id))
 
 
# ══════════════════════════════════════════════════════════════════════════════
# ESCROW TEST 1 — Buyer confirms receipt → seller gets paid
# ══════════════════════════════════════════════════════════════════════════════
 
print("\n\n════════════════════════════════════════")
print("ESCROW TEST 1: Buyer confirms receipt")
print("════════════════════════════════════════")
 
auction_1 = create_and_register_auction(
    duration_seconds=60,
    wallet_address=SELLER,
    starting_bid=0.5,
    confirmation_window=300,    # buyer has 5 minutes to confirm
)
id_1 = auction_1["auction_id"]
print("Auction ID:", id_1)
 
submit_bid(id_1, 1.0, BIDDER)
print_escrow_state("After bid (auction still open)", id_1)
 
# End the auction
advance_time(61)
 
# Load the contract directly to call endAuction()
from backend.remote_controls import load_auction_contract
w3_c, contract_1, _ = load_auction_contract(auction_1["auction_address"])
 
tx = contract_1.functions.endAuction().transact({"from": SELLER})
w3_c.eth.wait_for_transaction_receipt(tx)
print_escrow_state("After endAuction() — funds locked in escrow", id_1)
 
# Buyer confirms receipt
tx = contract_1.functions.confirmReceipt().transact({"from": BIDDER})
w3_c.eth.wait_for_transaction_receipt(tx)
print_escrow_state("After confirmReceipt() — seller paid, escrow settled", id_1)
 
assert get_state(id_1)["buyer_confirmed"]  is True,  "FAIL: buyer_confirmed should be True"
assert get_state(id_1)["escrow_settled"]   is True,  "FAIL: escrow_settled should be True"
assert get_state(id_1)["escrow_amount_wei"] == 0,    "FAIL: escrow should be empty after confirm"
print("✓ TEST 1 PASSED")
 
 
# ══════════════════════════════════════════════════════════════════════════════
# ESCROW TEST 2 — Buyer never confirms → seller claims after timeout
# ══════════════════════════════════════════════════════════════════════════════
 
print("\n\n════════════════════════════════════════")
print("ESCROW TEST 2: Seller claims after timeout")
print("════════════════════════════════════════")
 
auction_2 = create_and_register_auction(
    duration_seconds=60,
    wallet_address=SELLER,
    starting_bid=0.5,
    confirmation_window=300,    # 5 minute window
)
id_2 = auction_2["auction_id"]
print("Auction ID:", id_2)
 
submit_bid(id_2, 1.0, BIDDER)
 
advance_time(61)    # end the auction
 
w3_c, contract_2, _ = load_auction_contract(auction_2["auction_address"])
tx = contract_2.functions.endAuction().transact({"from": SELLER})
w3_c.eth.wait_for_transaction_receipt(tx)
print_escrow_state("After endAuction() — confirmation window is open", id_2)
 
# Buyer does NOT confirm — fast forward past the confirmation window
advance_time(301)
print_escrow_state("After window expires (buyer never confirmed)", id_2)
 
# Seller claims
tx = contract_2.functions.claimAfterTimeout().transact({"from": SELLER})
w3_c.eth.wait_for_transaction_receipt(tx)
print_escrow_state("After claimAfterTimeout() — seller paid", id_2)
 
assert get_state(id_2)["escrow_settled"]    is True, "FAIL: escrow_settled should be True"
assert get_state(id_2)["buyer_confirmed"]   is False,"FAIL: buyer_confirmed should still be False"
assert get_state(id_2)["escrow_amount_wei"] == 0,    "FAIL: escrow should be empty after claim"
print("✓ TEST 2 PASSED")
 
 
# ══════════════════════════════════════════════════════════════════════════════
# ESCROW TEST 3 — Admin trips refund flag → bidder withdraws via pendingReturns
# ══════════════════════════════════════════════════════════════════════════════
 
print("\n\n════════════════════════════════════════")
print("ESCROW TEST 3: Admin flags refund")
print("════════════════════════════════════════")
 
auction_3 = create_and_register_auction(
    duration_seconds=60,
    wallet_address=SELLER,
    starting_bid=0.5,
    confirmation_window=300,
)
id_3 = auction_3["auction_id"]
print("Auction ID:", id_3)
 
submit_bid(id_3, 1.0, BIDDER)
 
advance_time(61)
 
w3_c, contract_3, _ = load_auction_contract(auction_3["auction_address"])
tx = contract_3.functions.endAuction().transact({"from": SELLER})
w3_c.eth.wait_for_transaction_receipt(tx)
print_escrow_state("After endAuction() — funds in escrow", id_3)
 
# Admin trips the refund flag
tx = contract_3.functions.flagRefund().transact({"from": ADMIN})
w3_c.eth.wait_for_transaction_receipt(tx)
print_escrow_state("After flagRefund() — escrow moved to pendingReturns", id_3)
 
assert get_state(id_3)["refund_flagged"]    is True, "FAIL: refund_flagged should be True"
assert get_state(id_3)["escrow_settled"]    is True, "FAIL: escrow_settled should be True"
assert get_state(id_3)["escrow_amount_wei"] == 0,    "FAIL: escrow should be empty after flag"
 
# Verify bidder's pendingReturns was credited on-chain
pending = contract_3.functions.pendingReturns(BIDDER).call()
print(f"\n  pendingReturns[BIDDER] on-chain: {w3.from_wei(pending, 'ether')} ETH")
assert pending > 0, "FAIL: pendingReturns should be > 0 after flagRefund"
 
# Bidder withdraws their refund
bidder_balance_before = w3.eth.get_balance(BIDDER)
tx = contract_3.functions.withdraw().transact({"from": BIDDER})
w3_c.eth.wait_for_transaction_receipt(tx)
bidder_balance_after = w3.eth.get_balance(BIDDER)
 
print(f"  Bidder balance change: +{w3.from_wei(bidder_balance_after - bidder_balance_before, 'ether')} ETH (approx, minus gas)")
print("✓ TEST 3 PASSED")
 
 
# ══════════════════════════════════════════════════════════════════════════════
# GUARD TESTS — confirm actions are blocked after escrow is settled
# ══════════════════════════════════════════════════════════════════════════════
 
print("\n\n════════════════════════════════════════")
print("GUARD TESTS: Actions blocked after settlement")
print("════════════════════════════════════════")
 
# Try to confirmReceipt on an already-settled escrow (auction_1 — already confirmed)
try:
    contract_1.functions.confirmReceipt().transact({"from": BIDDER})
    print("FAIL: confirmReceipt should have reverted on settled escrow")
except Exception as e:
    print(f"✓ confirmReceipt correctly blocked after settlement: {type(e).__name__}")
 
# Try to flagRefund on an already-settled escrow (auction_3 — already flagged)
try:
    contract_3.functions.flagRefund().transact({"from": ADMIN})
    print("FAIL: flagRefund should have reverted on settled escrow")
except Exception as e:
    print(f"✓ flagRefund correctly blocked after settlement: {type(e).__name__}")
 
# Try to claimAfterTimeout before the window expires (use auction_2's contract,
# but it's already settled — create a fresh one to test the timing guard)
auction_guard = create_and_register_auction(
    duration_seconds=60,
    wallet_address=SELLER,
    starting_bid=0.5,
    confirmation_window=300,
)
submit_bid(auction_guard["auction_id"], 1.0, BIDDER)
advance_time(61)
w3_c, contract_guard, _ = load_auction_contract(auction_guard["auction_address"])
contract_guard.functions.endAuction().transact({"from": SELLER})
 
try:
    # Window hasn't expired yet — should revert
    contract_guard.functions.claimAfterTimeout().transact({"from": SELLER})
    print("FAIL: claimAfterTimeout should have reverted before window expires")
except Exception as e:
    print(f"✓ claimAfterTimeout correctly blocked before window expires: {type(e).__name__}")
 
print("\n\n════════════════════════════════════════")
print("ALL TESTS COMPLETE")
print("════════════════════════════════════════")
