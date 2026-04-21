"""
test_mainauction.py

End-to-end integration tests for the full auction stack:

    remote_controls/ -> Hardhat node -> SimpleAuction.sol

Prerequisites:
    - Hardhat node running at http://127.0.0.1:8545
    - AuctionFactory deployed at the address in factory.py
    - Run from repo root: python -m backend.test_mainauction

Hardhat default accounts:
    Account[0] -- ADMIN  (factory deployer)
    Account[1] -- SELLER
    Account[2] -- BIDDER

State field notes:
    get_auction_state() returns:
        contract_address, chain_time, chain_time_readable,
        highest_bid_wei, highest_bid_eth, highest_bidder,
        auction_end_time, auction_end_time_readable,
        time_remaining_seconds, time_remaining_display, status

    Escrow fields (buyer_confirmed, escrow_settled, refund_flagged,
    escrow_amount, pendingReturns) are NOT in get_auction_state --
    they are read directly from the contract via .call().
"""

import sys
from web3 import Web3

from backend.remote_controls import (
    create_auction,
    load_auction_contract,
    place_bid,
    get_auction_state,
    confirm_receipt,
    claim_after_timeout,
    flag_refund,
    get_time_remaining_for_confirmation,
    withdraw,
)

# ===========================================================================
# Hardhat accounts — must be exactly EIP-55 checksummed
# ===========================================================================

ADMIN  = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"   # account[0]
SELLER = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"   # account[1]
BIDDER = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"   # account[2]

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))


# ===========================================================================
# Helpers
# ===========================================================================

def advance_time(seconds: int) -> None:
    """Fast-forward the Hardhat node clock and mine a block."""
    w3.provider.make_request("evm_increaseTime", [seconds])
    w3.provider.make_request("evm_mine", [])


def new_auction(duration=60, starting_bid=0.5, confirmation_window=300):
    """
    Deploy a fresh auction via the factory.
    Returns (auction_address, w3_c, contract).
    """
    result  = create_auction(duration, SELLER, starting_bid, confirmation_window)
    address = result["auction_address"]
    w3_c, contract, _ = load_auction_contract(address)
    return address, w3_c, contract


def end_auction(w3_c, contract):
    tx = contract.functions.endAuction().transact({"from": SELLER})
    w3_c.eth.wait_for_transaction_receipt(tx)


def escrow_state(contract) -> dict:
    """
    Read escrow fields directly from the contract.
    These are not included in get_auction_state() / state.py.
    """
    return {
        "ended":           contract.functions.ended().call(),
        "escrow_amount":   contract.functions.escrowAmount().call(),
        "buyer_confirmed": contract.functions.buyerConfirmed().call(),
        "escrow_settled":  contract.functions.escrowSettled().call(),
        "refund_flagged":  contract.functions.refundFlagged().call(),
    }


def print_escrow(label: str, contract) -> None:
    s = escrow_state(contract)
    print(f"\n  --- {label} ---")
    for k, v in s.items():
        print(f"  {k}: {v}")


# ===========================================================================
# Test runner
# ===========================================================================

PASSED = 0
FAILED = 0


def run_test(name, fn):
    global PASSED, FAILED
    print(f"\n{'=' * 60}")
    print(f"  {name}")
    print(f"{'=' * 60}")
    try:
        fn()
        print(f"\n  PASSED")
        PASSED += 1
    except Exception as e:
        import traceback
        print(f"\n  FAILED: {e}", file=sys.stderr)
        traceback.print_exc()
        FAILED += 1


# ===========================================================================
# Tests
# ===========================================================================

def test_create_and_bid():
    """Auction deploys and accepts a valid bid."""
    address, w3_c, contract = new_auction(duration=3600)

    state = get_auction_state(w3_c, contract, address)
    assert state["status"] == "OPEN", "Auction should be open"
    assert state["highest_bid_eth"] == 0.0

    result = place_bid(w3_c, contract, BIDDER, 1.0)
    assert "tx_hash" in result

    state = get_auction_state(w3_c, contract, address)
    assert state["highest_bid_eth"] == 1.0
    assert state["highest_bidder"].lower() == BIDDER.lower()
    assert state["status"] == "OPEN"


def test_escrow_confirm_receipt():
    """Buyer confirms receipt -- escrow released to seller immediately."""
    address, w3_c, contract = new_auction()

    place_bid(w3_c, contract, BIDDER, 1.0)
    advance_time(61)
    end_auction(w3_c, contract)
    print_escrow("after endAuction", contract)

    assert escrow_state(contract)["escrow_amount"] > 0, "Funds should be in escrow"

    result = confirm_receipt(w3_c, contract, BIDDER)
    assert result["escrow_settled"] is True
    print_escrow("after confirmReceipt", contract)

    s = escrow_state(contract)
    assert s["buyer_confirmed"] is True
    assert s["escrow_settled"]  is True
    assert s["escrow_amount"]   == 0


def test_escrow_claim_after_timeout():
    """Seller claims after buyer never confirms and window expires."""
    address, w3_c, contract = new_auction()

    place_bid(w3_c, contract, BIDDER, 1.0)
    advance_time(61)
    end_auction(w3_c, contract)

    assert escrow_state(contract)["escrow_amount"] > 0, "Funds should be in escrow"

    advance_time(301)
    print_escrow("after window expires", contract)

    result = claim_after_timeout(w3_c, contract, SELLER)
    assert result["escrow_settled"] is True
    print_escrow("after claimAfterTimeout", contract)

    s = escrow_state(contract)
    assert s["escrow_settled"]  is True
    assert s["buyer_confirmed"] is False
    assert s["escrow_amount"]   == 0


def test_escrow_flag_refund_and_withdraw():
    """Admin flags refund -- bidder withdraws via pendingReturns."""
    address, w3_c, contract = new_auction()

    place_bid(w3_c, contract, BIDDER, 1.0)
    advance_time(61)
    end_auction(w3_c, contract)

    assert escrow_state(contract)["escrow_amount"] > 0, "Funds should be in escrow"

    result = flag_refund(w3_c, contract, ADMIN)
    assert result["refund_flagged"] is True
    print_escrow("after flagRefund", contract)

    s = escrow_state(contract)
    assert s["refund_flagged"] is True
    assert s["escrow_settled"] is True
    assert s["escrow_amount"]  == 0

    pending = contract.functions.pendingReturns(BIDDER).call()
    assert pending > 0, "pendingReturns should be funded after flagRefund"
    print(f"\n  pendingReturns[BIDDER]: {w3.from_wei(pending, 'ether')} ETH")

    bal_before = w3.eth.get_balance(BIDDER)
    result = withdraw(w3_c, contract, BIDDER)
    bal_after  = w3.eth.get_balance(BIDDER)

    print(f"  Withdrawn: {result['amount_withdrawn_eth']} ETH")
    print(f"  Bidder net (approx, minus gas): +{w3.from_wei(bal_after - bal_before, 'ether')} ETH")
    assert contract.functions.pendingReturns(BIDDER).call() == 0


def test_escrow_time_remaining():
    """timeRemainingForConfirmation returns > 0 after endAuction, 0 after settled."""
    address, w3_c, contract = new_auction()

    place_bid(w3_c, contract, BIDDER, 1.0)
    advance_time(61)
    end_auction(w3_c, contract)

    result = get_time_remaining_for_confirmation(w3_c, contract)
    assert result["seconds_remaining"] > 0, "Window should still be open"
    print(f"\n  seconds_remaining (open): {result['seconds_remaining']}s")

    confirm_receipt(w3_c, contract, BIDDER)

    result = get_time_remaining_for_confirmation(w3_c, contract)
    assert result["seconds_remaining"] == 0, "Window should report 0 after settlement"
    print(f"  seconds_remaining (settled): {result['seconds_remaining']}s")


def test_guard_confirm_after_settled():
    """confirmReceipt reverts on an already-settled escrow."""
    address, w3_c, contract = new_auction()

    place_bid(w3_c, contract, BIDDER, 1.0)
    advance_time(61)
    end_auction(w3_c, contract)
    confirm_receipt(w3_c, contract, BIDDER)

    try:
        confirm_receipt(w3_c, contract, BIDDER)
        raise AssertionError("should have reverted")
    except Exception as e:
        if isinstance(e, AssertionError):
            raise
        print(f"  Correctly blocked: {type(e).__name__}")


def test_guard_flag_refund_after_settled():
    """flagRefund reverts on an already-settled escrow."""
    address, w3_c, contract = new_auction()

    place_bid(w3_c, contract, BIDDER, 1.0)
    advance_time(61)
    end_auction(w3_c, contract)
    flag_refund(w3_c, contract, ADMIN)

    try:
        flag_refund(w3_c, contract, ADMIN)
        raise AssertionError("should have reverted")
    except Exception as e:
        if isinstance(e, AssertionError):
            raise
        print(f"  Correctly blocked: {type(e).__name__}")


def test_guard_claim_before_window_expires():
    """claimAfterTimeout reverts while the confirmation window is still open."""
    address, w3_c, contract = new_auction()

    place_bid(w3_c, contract, BIDDER, 1.0)
    advance_time(61)
    end_auction(w3_c, contract)

    try:
        claim_after_timeout(w3_c, contract, SELLER)
        raise AssertionError("should have reverted")
    except Exception as e:
        if isinstance(e, AssertionError):
            raise
        print(f"  Correctly blocked: {type(e).__name__}")


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":

    run_test("Create auction + place bid",                     test_create_and_bid)
    run_test("Escrow: buyer confirms receipt",                 test_escrow_confirm_receipt)
    run_test("Escrow: seller claims after timeout",            test_escrow_claim_after_timeout)
    run_test("Escrow: admin flags refund + bidder withdraws",  test_escrow_flag_refund_and_withdraw)
    run_test("Escrow: time remaining for confirmation",        test_escrow_time_remaining)
    run_test("Guard: confirmReceipt blocked after settled",    test_guard_confirm_after_settled)
    run_test("Guard: flagRefund blocked after settled",        test_guard_flag_refund_after_settled)
    run_test("Guard: claimAfterTimeout blocked before window", test_guard_claim_before_window_expires)

    print(f"\n{'=' * 60}")
    print(f"  Results: {PASSED} passed, {FAILED} failed")
    print(f"{'=' * 60}")
    sys.exit(0 if FAILED == 0 else 1)