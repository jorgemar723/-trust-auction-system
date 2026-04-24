# Testing Plan — Blockchain Auction System

**File:** `backend/test_mainauction.py`  
**Technology:** Python + web3.py + Hardhat (local Ethereum node)  
**Run command:** `python -m backend.test_mainauction` (from repo root)

---

## Overview

This testing plan covers the end-to-end integration tests for the Python-to-blockchain layer of the auction system. Tests are written against the `remote_controls` package, which is the layer responsible for all on-chain read and write operations. Each test deploys a real auction contract to a local Hardhat node, executes transactions, and asserts on-chain state.

No mocking of blockchain logic is used. Every test sends real transactions and reads real contract state.

---

## Test 1 — `test_create_and_bid`

**Feature Tested:** Auction creation and bid submission.

**Code Under Test:**
- `remote_controls.factory.create_auction()`
- `remote_controls.auction_loader.load_auction_contract()`
- `remote_controls.bidding.place_bid()`
- `remote_controls.state.get_auction_state()`

**What It Does:**
Deploys a new auction contract via the AuctionFactory, verifies the auction opens in the correct state, places a bid of 1.0 ETH from the BIDDER account, and confirms the contract state reflects the new highest bid and bidder.

**Fields and Return Objects Asserted:**

| Call | Field | Expected |
|------|-------|----------|
| `create_auction()` | `result["auction_address"]` | used to load contract |
| `place_bid()` | `result["tx_hash"]` | confirms tx was mined |
| `get_auction_state()` | `state["status"]` | `== "OPEN"` |
| `get_auction_state()` | `state["highest_bid_eth"]` | `== 1.0` |
| `get_auction_state()` | `state["highest_bidder"]` | `== BIDDER address` |

**Why This Test:**
Validates the two most fundamental operations in the system — creating an auction and placing a bid. If either the factory deployment or the bid transaction is broken, all downstream escrow tests are also invalid. This test establishes the baseline that the contract is reachable and accepting bids correctly.

---

## Test 2 — `test_escrow_confirm_receipt`

**Feature Tested:** Escrow settlement via buyer confirmation (happy path).

**Code Under Test:**
- `remote_controls.escrow.confirm_receipt()`
- `remote_controls.state.get_auction_state()`
- `contract.functions.escrowAmount().call()`
- `contract.functions.buyerConfirmed().call()`
- `contract.functions.escrowSettled().call()`

**What It Does:**
Creates an auction, places a bid, advances the Hardhat clock past the auction end time, calls `endAuction()` to lock funds in escrow, then calls `confirmReceipt()` from the winning bidder's address. Verifies that the escrow is emptied and both `buyerConfirmed` and `escrowSettled` are set to `True` on-chain.

**Fields and Return Objects Asserted:**

| Call | Field | Expected |
|------|-------|----------|
| `confirm_receipt()` | `result["escrow_settled"]` | `is True` |
| `escrow_state()` | `["escrow_amount"]` | `== 0` |
| `escrow_state()` | `["buyer_confirmed"]` | `is True` |
| `escrow_state()` | `["escrow_settled"]` | `is True` |

**Why This Test:**
The buyer confirmation path is the primary intended resolution of every auction. This test verifies that calling `confirmReceipt()` from the correct address releases escrow funds to the seller and updates all relevant state flags. It also verifies that the escrow amount is fully drained after settlement.

---

## Test 3 — `test_escrow_claim_after_timeout`

**Feature Tested:** Escrow settlement via seller timeout claim (buyer never confirms).

**Code Under Test:**
- `remote_controls.escrow.claim_after_timeout()`
- `contract.functions.escrowAmount().call()`
- `contract.functions.escrowSettled().call()`
- `contract.functions.buyerConfirmed().call()`

**What It Does:**
Creates an auction, places a bid, ends the auction, then advances the clock past the confirmation window (300 seconds) without the buyer calling `confirmReceipt()`. The seller then calls `claimAfterTimeout()`. Verifies that the escrow is emptied and `escrowSettled` is `True` while `buyerConfirmed` remains `False`.

**Fields and Return Objects Asserted:**

| Call | Field | Expected |
|------|-------|----------|
| `claim_after_timeout()` | `result["escrow_settled"]` | `is True` |
| `escrow_state()` | `["escrow_settled"]` | `is True` |
| `escrow_state()` | `["buyer_confirmed"]` | `is False` |
| `escrow_state()` | `["escrow_amount"]` | `== 0` |

**Why This Test:**
Tests the fallback resolution path for the case where a buyer goes silent after winning. Verifies the seller is not permanently locked out of their funds and that the timeout mechanism works as specified. Also confirms that `buyerConfirmed` stays `False` — the seller claiming via timeout is distinct from the buyer confirming receipt.

---

## Test 4 — `test_escrow_flag_refund_and_withdraw`

**Feature Tested:** Admin-initiated refund via `flagRefund()` and subsequent withdrawal by the winning bidder via `withdraw()`.

**Code Under Test:**
- `remote_controls.escrow.flag_refund()`
- `remote_controls.withdrawal.withdraw()`
- `contract.functions.pendingReturns().call()`
- `contract.functions.escrowSettled().call()`
- `contract.functions.refundFlagged().call()`
- `contract.functions.escrowAmount().call()`

**What It Does:**
Creates an auction, places a bid, ends the auction, then has the admin call `flagRefund()`. Verifies that escrow funds move to `pendingReturns` for the winning bidder. Then calls `withdraw()` from the bidder's address and confirms the funds are received and `pendingReturns` is zeroed out.

**Fields and Return Objects Asserted:**

| Call | Field | Expected |
|------|-------|----------|
| `flag_refund()` | `result["refund_flagged"]` | `is True` |
| `escrow_state()` | `["refund_flagged"]` | `is True` |
| `escrow_state()` | `["escrow_settled"]` | `is True` |
| `escrow_state()` | `["escrow_amount"]` | `== 0` |
| `contract.pendingReturns(BIDDER)` | | `> 0` |
| `withdraw()` | `result["amount_withdrawn_eth"]` | `== 1.0` |
| `contract.pendingReturns(BIDDER)` after withdraw | | `== 0` |

**Why This Test:**
Tests the dispute/refund path which involves two separate transactions and two different `remote_controls` modules (`escrow.py` and `withdrawal.py`) working in sequence. Verifies that the checks-effects-interactions pattern in the contract is working correctly — funds move from escrow to `pendingReturns` on `flagRefund`, and are fully cleared on `withdraw`.

---

## Test 5 — `test_escrow_time_remaining`

**Feature Tested:** Confirmation window countdown via `timeRemainingForConfirmation()`.

**Code Under Test:**
- `remote_controls.escrow.get_time_remaining_for_confirmation()`

**What It Does:**
Creates an auction, places a bid, ends the auction, and immediately queries the time remaining. Confirms it is greater than 0. Then calls `confirmReceipt()` to settle the escrow and queries again, confirming the value drops to 0.

**Fields and Return Objects Asserted:**

| Call | Field | Expected |
|------|-------|----------|
| `get_time_remaining_for_confirmation()` (after endAuction) | `result["seconds_remaining"]` | `> 0` |
| `get_time_remaining_for_confirmation()` (after settled) | `result["seconds_remaining"]` | `== 0` |

**Why This Test:**
The confirmation window is a time-sensitive mechanism that both the buyer and seller depend on. This test verifies the read function returns a meaningful value while the window is open and correctly returns 0 once the escrow has been settled, per the expected behavior in `AuctionEscrow.sol`.

---

## Test 6 — `test_guard_confirm_after_settled`

**Feature Tested:** Contract guard: `confirmReceipt()` is blocked after escrow is already settled.

**Code Under Test:**
- `remote_controls.escrow.confirm_receipt()` (called twice intentionally)
- `SimpleAuction.sol` — `require(!escrowSettled)` guard in `confirmReceipt()`

**What It Does:**
Creates an auction, places a bid, ends the auction, and calls `confirmReceipt()` to settle the escrow. Then attempts to call `confirmReceipt()` a second time on the same contract. Asserts that the second call raises a `ContractLogicError` (Solidity revert).

**Fields and Return Objects Asserted:**

| Call | Expected |
|------|----------|
| Second `confirm_receipt()` | raises `ContractLogicError` (not `AssertionError`) |

**Why This Test:**
Verifies that the contract correctly enforces that escrow can only be settled once. Double-settlement would be a critical vulnerability allowing funds to be drained. This test confirms the on-chain guard is active and cannot be bypassed by calling the function a second time.

---

## Test 7 — `test_guard_flag_refund_after_settled`

**Feature Tested:** Contract guard: `flagRefund()` is blocked after escrow is already settled.

**Code Under Test:**
- `remote_controls.escrow.flag_refund()` (called twice intentionally)
- `SimpleAuction.sol` — `require(!escrowSettled)` guard in `flagRefund()`

**What It Does:**
Creates an auction, places a bid, ends the auction, and calls `flagRefund()` from the admin address to settle the escrow. Then attempts to call `flagRefund()` a second time. Asserts that the second call raises a `ContractLogicError`.

**Fields and Return Objects Asserted:**

| Call | Expected |
|------|----------|
| Second `flag_refund()` | raises `ContractLogicError` (not `AssertionError`) |

**Why This Test:**
Mirrors Test 6 but for the admin refund path. Confirms that once an admin has flagged a refund and the escrow is settled, the action cannot be repeated. Prevents a scenario where `pendingReturns` could be credited multiple times for the same auction.

---

## Test 8 — `test_guard_claim_before_window_expires`

**Feature Tested:** Contract guard: `claimAfterTimeout()` is blocked while the confirmation window is still open.

**Code Under Test:**
- `remote_controls.escrow.claim_after_timeout()`
- `SimpleAuction.sol` — `require(block.timestamp > escrowReleaseTimeout)` guard

**What It Does:**
Creates an auction, places a bid, ends the auction, and immediately attempts to call `claimAfterTimeout()` without advancing the clock past the confirmation window. Asserts that the call raises a `ContractLogicError`.

**Fields and Return Objects Asserted:**

| Call | Expected |
|------|----------|
| `claim_after_timeout()` before window expires | raises `ContractLogicError` |

**Why This Test:**
The confirmation window exists to give the buyer a fair opportunity to confirm receipt before the seller can claim funds unilaterally. This test verifies the contract enforces this window and that the seller cannot bypass it by calling `claimAfterTimeout()` immediately after `endAuction()`. This is the primary protection for the buyer in the escrow flow.

---

## Summary

| Test | Feature |
|------|---------|
| `test_create_and_bid` | Auction creation + bid submission |
| `test_escrow_confirm_receipt` | Escrow: buyer confirms (happy path) |
| `test_escrow_claim_after_timeout` | Escrow: seller claims after timeout |
| `test_escrow_flag_refund_and_withdraw` | Escrow: admin refund + withdrawal |
| `test_escrow_time_remaining` | Confirmation window countdown |
| `test_guard_confirm_after_settled` | Guard: no double-settlement |
| `test_guard_flag_refund_after_settled` | Guard: no double-refund |
| `test_guard_claim_before_window_expires` | Guard: timeout not premature |

**Total tests:** 8  
**Result (last run):** 8 passed, 0 failed
