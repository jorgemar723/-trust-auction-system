"""
mainauction.py

Orchestration layer between Flask (HTTP layer) and the blockchain
interaction modules in remote_controls.

Blockchain read/write logic lives in remote_controls — not here.
Database lookup logic lives in repositories — not here.
"""

from __future__ import annotations

from db.repositories.auction_repository import AuctionRepository
from backend.remote_controls.wallet import get_eth_balance

from .remote_controls import (
    create_auction,
    get_auction_state,
    load_auction_contract,
    place_bid,
    confirm_receipt as _confirm_receipt,
    claim_after_timeout as _claim_after_timeout,
    flag_refund as _flag_refund,
    get_time_remaining_for_confirmation,
    withdraw as _withdraw,
    BackendAPIError,
)


auction_repo = AuctionRepository()
_AUCTION_REGISTRY = auction_repo.get_auction_registry()
_NEXT_AUCTION_ID = max(_AUCTION_REGISTRY.keys(), default=0) + 1


def _get_contract_address(auction_id: int) -> str:
    address = AuctionRepository().get_contract_address_by_auction_id(auction_id)

    if not address:
        raise BackendAPIError(
            code="AUCTION_NOT_FOUND",
            message="Auction not found.",
            http_status=404,
            details=f"No contract address found for auction_id={auction_id}",
        )

    return address


def _load_contract(address: str):
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
    if not wallet_address:
        raise BackendAPIError(
            code="MISSING_WALLET",
            message="User does not have a wallet address configured.",
            http_status=400,
            details="wallet_address is None or empty",
        )


def create_and_register_auction(
    duration_seconds: int,
    wallet_address: str,
    starting_bid: float,
    confirmation_window: int = 259200,
) -> dict:
    global _NEXT_AUCTION_ID

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
            "auction_id": auction_id,
            "auction_address": auction_address,
            "tx_hash": result["tx_hash"],
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
    return create_and_register_auction(duration_seconds, wallet_address, starting_bid)


def submit_bid(auction_id: int, user_bid: float, wallet_address: str) -> dict:
    _require_wallet(wallet_address)

    if user_bid <= 0:
        raise BackendAPIError(
            code="INVALID_BID",
            message="Bid amount must be positive.",
            http_status=400,
            details=f"Received bid: {user_bid}",
        )

    address = _get_contract_address(auction_id)
    w3, contract, _account = _load_contract(address)

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

    try:
        return place_bid(w3, contract, wallet_address, user_bid)
    except Exception as e:
        raise BackendAPIError(
            code="BID_FAILED",
            message="Bid transaction failed.",
            http_status=500,
            details=str(e),
        ) from e


def get_state(auction_id: int) -> dict:
    address = _get_contract_address(auction_id)
    w3, contract, _account = _load_contract(address)

    try:
        return get_auction_state(w3, contract, address)
    except Exception as e:
        raise BackendAPIError(
            code="CHAIN_CALL_FAILED",
            message="Failed to fetch on-chain state.",
            http_status=500,
            details=str(e),
        ) from e


def confirm_receipt(auction_id: int, wallet_address: str) -> dict:
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


def withdraw_funds(auction_id: int, wallet_address: str) -> dict:
    _require_wallet(wallet_address)

    address = _get_contract_address(auction_id)
    w3, contract, _account = _load_contract(address)

    try:
        result = _withdraw(w3, contract, wallet_address)
        return {"auction_id": auction_id, **result}
    except ValueError as e:
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