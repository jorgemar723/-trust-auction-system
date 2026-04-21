"""
mainauction.py
 
Orchestration layer between Flask (HTTP layer) and the blockchain
interaction modules in remote_controls.
 
Each public function in this file follows the same three-step pattern:
    1. Validate inputs
    2. Look up the contract address and load the contract
    3. Call the appropriate remote and return the result
 
Blockchain read/write logic lives in remote_controls — not here.
 
System Position:
 
    Flask (HTTP layer)
        ↓
    mainauction.py  ← THIS FILE (orchestration)
        ↓
    remote_controls/ (bidding.py, escrow.py, withdrawal.py, …)
        ↓
    Hardhat / Ethereum node
"""
 
from __future__ import annotations
 
from db.PostgresDB import PostgresDB
from backend.remote_controls.wallet import get_eth_balance
 
from .remote_controls import (
    # Auction lifecycle
    create_auction,
    get_auction_state,
    load_auction_contract,
    # Bidding
    place_bid,
    # Escrow
    confirm_receipt      as _confirm_receipt,
    claim_after_timeout  as _claim_after_timeout,
    flag_refund          as _flag_refund,
    get_time_remaining_for_confirmation,
    # Withdrawal
    withdraw             as _withdraw,
    # Errors
    BackendAPIError,
)
 
 
# ─── Module-level auction registry ───────────────────────────────────────────
#
# Loaded once at import time so we can assign sequential IDs without hitting
# the DB on every request. Format: {auction_id (int): contract_address (str)}
 
db = PostgresDB()
db.connect()
_AUCTION_REGISTRY = db.get_auction_registry()
db.close()
 
_NEXT_AUCTION_ID = max(_AUCTION_REGISTRY.keys(), default=0) + 1
 
 
# ─── Private helpers ──────────────────────────────────────────────────────────
 
 
def _get_contract_address(auction_id: int) -> str:
    """
    Look up the on-chain contract address for an auction ID.
    Raises BackendAPIError(404) if not found.
    """
    db = PostgresDB()
    db.connect()
    address = db.get_contract_address_by_auction_id(auction_id)
    db.close()
 
    if not address:
        raise BackendAPIError(
            code="AUCTION_NOT_FOUND",
            message="Auction not found.",
            http_status=404,
            details=f"No contract address found for auction_id={auction_id}",
        )
 
    return address
 
 
def _load_contract(address: str):
    """
    Load a Web3 contract instance from a contract address.
    Raises BackendAPIError(500) if the load fails.
 
    Returns:
        tuple: (w3, contract, account)
    """
    try:
        return load_auction_contract(address)
    except Exception as e:
        raise BackendAPIError(
            code="CONTRACT_LOAD_FAILED",
            message="Failed to load auction contract.",
            http_status=500,
            details=str(e),
        ) from e
 
 
def _require_wallet(wallet_address: str) -> None:
    """Raise BackendAPIError(400) if wallet_address is missing."""
    if not wallet_address:
        raise BackendAPIError(
            code="MISSING_WALLET",
            message="User does not have a wallet address configured.",
            http_status=400,
            details="wallet_address is None or empty",
        )
 
 
# ─── Auction creation ─────────────────────────────────────────────────────────
 
 
def create_and_register_auction(
    duration_seconds: int,
    wallet_address: str,
    starting_bid: float,
    confirmation_window: int = 259200,  # 3 days in seconds
) -> dict:
    """
    Create a new auction on-chain and register it locally.
 
    Args:
        duration_seconds:    How long the auction runs (seconds).
        wallet_address:      Seller's wallet address.
        starting_bid:        Minimum opening bid in ETH.
        confirmation_window: Seconds the buyer has to confirm receipt before
                             the seller can claim a timeout. Default: 3 days.
 
    Returns:
        dict: { auction_id, auction_address, tx_hash, confirmation_window }
    """
    global _NEXT_AUCTION_ID
 
    # ── Input validation ──────────────────────────────────────────────────
    _require_wallet(wallet_address)
 
    if duration_seconds <= 0:
        raise BackendAPIError(
            code="INVALID_DURATION",
            message="Auction duration must be positive.",
            http_status=400,
            details=f"Received duration: {duration_seconds}",
        )
 
    if starting_bid <= 0:
        raise BackendAPIError(
            code="INVALID_STARTING_BID",
            message="Starting bid must be positive.",
            http_status=400,
            details=f"Received starting_bid: {starting_bid}",
        )
 
    if confirmation_window <= 0:
        raise BackendAPIError(
            code="INVALID_CONFIRMATION_WINDOW",
            message="Confirmation window must be positive.",
            http_status=400,
            details=f"Received confirmation_window: {confirmation_window}",
        )
 
    # ── On-chain creation + local registration ────────────────────────────
    try:
        result = create_auction(
            duration_seconds,
            wallet_address,
            starting_bid,
            confirmation_window,
        )
        auction_address = result["auction_address"]
 
        auction_id = _NEXT_AUCTION_ID
        _AUCTION_REGISTRY[auction_id] = auction_address
        _NEXT_AUCTION_ID += 1
 
        return {
            "auction_id":          auction_id,
            "auction_address":     auction_address,
            "tx_hash":             result["tx_hash"],
            "confirmation_window": confirmation_window,
        }
 
    except Exception as e:
        raise BackendAPIError(
            code="AUCTION_CREATION_FAILED",
            message="Failed to create auction.",
            http_status=500,
            details=str(e),
        ) from e
 
 
def create_new_auction(
    duration_seconds: int,
    wallet_address: str,
    starting_bid: float,
) -> dict:
    """
    Backward-compatible wrapper around create_and_register_auction().
    Prefer create_and_register_auction() for new code.
    """
    return create_and_register_auction(duration_seconds, wallet_address, starting_bid)
 
 
# ─── Bidding ──────────────────────────────────────────────────────────────────
 
 
def submit_bid(auction_id: int, user_bid: float, wallet_address: str) -> dict:
    """
    Validate and submit a bid to an active auction.
 
    Checks that the bid is positive and that the wallet has sufficient
    funds before sending the transaction on-chain.
 
    Args:
        auction_id:     ID of the auction to bid on.
        user_bid:       Bid amount in ETH.
        wallet_address: Address placing the bid.
 
    Returns:
        dict: { tx_hash, highest_bid_wei }
    """
    # ── Input validation ──────────────────────────────────────────────────
    _require_wallet(wallet_address)
 
    if user_bid <= 0:
        raise BackendAPIError(
            code="INVALID_BID",
            message="Bid amount must be positive.",
            http_status=400,
            details=f"Received bid: {user_bid}",
        )
 
    # ── Contract lookup ───────────────────────────────────────────────────
    address = _get_contract_address(auction_id)
    w3, contract, _account = _load_contract(address)
 
    # ── Balance check ─────────────────────────────────────────────────────
    try:
        balance_eth = float(get_eth_balance(w3, wallet_address))
    except Exception as e:
        raise BackendAPIError(
            code="BALANCE_CHECK_FAILED",
            message="Failed to retrieve wallet balance.",
            http_status=500,
            details=str(e),
        ) from e
 
    if user_bid > balance_eth:
        raise BackendAPIError(
            code="INSUFFICIENT_FUNDS",
            message="Insufficient wallet balance.",
            http_status=400,
            details=(
                f"Balance: {round(balance_eth, 2)} ETH, "
                f"Attempted bid: {round(user_bid, 2)} ETH"
            ),
        )
 
    # ── Place bid ─────────────────────────────────────────────────────────
    try:
        return place_bid(w3, contract, wallet_address, user_bid)
    except Exception as e:
        raise BackendAPIError(
            code="BID_FAILED",
            message="Bid transaction failed.",
            http_status=500,
            details=str(e),
        ) from e
 
 
# ─── Auction state ────────────────────────────────────────────────────────────
 
 
def get_state(auction_id: int) -> dict:
    """
    Fetch the current on-chain state of an auction.
 
    Args:
        auction_id: ID of the auction to query.
 
    Returns:
        dict: On-chain state fields plus { highest_bid_usd: float | None }
    """
    address  = _get_contract_address(auction_id)
    w3, contract, _account = _load_contract(address)
 
    try:
        state = get_auction_state(w3, contract, address)
        return state
 
    except Exception as e:
        raise BackendAPIError(
            code="CHAIN_CALL_FAILED",
            message="Failed to fetch on-chain state.",
            http_status=500,
            details=str(e),
        ) from e
 
 
# ─── Escrow ───────────────────────────────────────────────────────────────────
 
 
def confirm_receipt(auction_id: int, wallet_address: str) -> dict:
    """
    Called by the winning bidder to confirm they received the item.
    Immediately releases escrowed funds to the seller on-chain.
 
    Args:
        auction_id:     ID of the auction to confirm.
        wallet_address: Must match highestBidder on the contract.
 
    Returns:
        dict: { auction_id, tx_hash, escrow_settled }
    """
    _require_wallet(wallet_address)
    address = _get_contract_address(auction_id)
    w3, contract, _account = _load_contract(address)
 
    try:
        result = _confirm_receipt(w3, contract, wallet_address)
        return {"auction_id": auction_id, **result}
    except Exception as e:
        raise BackendAPIError(
            code="CONFIRM_RECEIPT_FAILED",
            message="Failed to confirm receipt.",
            http_status=500,
            details=str(e),
        ) from e
 
 
def claim_after_timeout(auction_id: int, wallet_address: str) -> dict:
    """
    Called by the seller when the buyer never confirmed receipt and
    the confirmation window has expired. Releases escrowed funds to
    the seller on-chain.
 
    Args:
        auction_id:     ID of the auction to claim.
        wallet_address: Must match seller on the contract.
 
    Returns:
        dict: { auction_id, tx_hash, escrow_settled }
    """
    _require_wallet(wallet_address)
    address = _get_contract_address(auction_id)
    w3, contract, _account = _load_contract(address)
 
    try:
        result = _claim_after_timeout(w3, contract, wallet_address)
        return {"auction_id": auction_id, **result}
    except Exception as e:
        raise BackendAPIError(
            code="CLAIM_TIMEOUT_FAILED",
            message="Failed to claim after timeout.",
            http_status=500,
            details=str(e),
        ) from e
 
 
def flag_refund(auction_id: int, wallet_address: str) -> dict:
    """
    Admin-only. Cancels the escrow and queues the winning bid back into
    pendingReturns for the winner to collect.
 
    NOTE: This does NOT send funds directly — the winner must call
    withdraw_funds() afterward to collect their refund.
 
    Args:
        auction_id:     ID of the auction to refund.
        wallet_address: Must match admin on the contract.
 
    Returns:
        dict: { auction_id, tx_hash, refund_flagged }
    """
    _require_wallet(wallet_address)
    address = _get_contract_address(auction_id)
    w3, contract, _account = _load_contract(address)
 
    try:
        result = _flag_refund(w3, contract, wallet_address)
        return {"auction_id": auction_id, **result}
    except Exception as e:
        raise BackendAPIError(
            code="FLAG_REFUND_FAILED",
            message="Failed to flag refund.",
            http_status=500,
            details=str(e),
        ) from e
 
 
def get_escrow_time_remaining(auction_id: int) -> dict:
    """
    Read-only. Returns how many seconds remain in the buyer confirmation
    window. Returns 0 if the window has expired, escrow is already
    settled, or the auction has not ended yet.
 
    Args:
        auction_id: ID of the auction to query.
 
    Returns:
        dict: { auction_id, seconds_remaining }
    """
    address = _get_contract_address(auction_id)
    w3, contract, _account = _load_contract(address)
 
    try:
        result = get_time_remaining_for_confirmation(w3, contract)
        return {"auction_id": auction_id, **result}
    except Exception as e:
        raise BackendAPIError(
            code="CHAIN_CALL_FAILED",
            message="Failed to fetch escrow time remaining.",
            http_status=500,
            details=str(e),
        ) from e
 
 
# ─── Withdrawal ───────────────────────────────────────────────────────────────
 
 
def withdraw_funds(auction_id: int, wallet_address: str) -> dict:
    """
    Withdraw all funds queued in pendingReturns for the given wallet.
 
    Used by:
        - Outbid bidders reclaiming their bids during or after the auction.
        - The winning bidder collecting their refund after flag_refund().
 
    Args:
        auction_id:     ID of the auction contract to withdraw from.
        wallet_address: Funds are withdrawn from pendingReturns[wallet_address].
 
    Returns:
        dict: { auction_id, tx_hash, amount_withdrawn_wei, amount_withdrawn_eth }
    """
    _require_wallet(wallet_address)
    address = _get_contract_address(auction_id)
    w3, contract, _account = _load_contract(address)
 
    try:
        result = _withdraw(w3, contract, wallet_address)
        return {"auction_id": auction_id, **result}
    except ValueError as e:
        # withdrawal.py raises ValueError for zero-balance or a failed on-chain send
        raise BackendAPIError(
            code="WITHDRAWAL_FAILED",
            message=str(e),
            http_status=400,
            details=f"auction_id={auction_id}, wallet={wallet_address}",
        ) from e
    except Exception as e:
        raise BackendAPIError(
            code="WITHDRAWAL_FAILED",
            message="Withdrawal transaction failed.",
            http_status=500,
            details=str(e),
        ) from e
 
