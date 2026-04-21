"""
escrow.py
 
Purpose:
    Blockchain interaction layer for post-auction escrow operations.
 
    This module handles all state-changing transactions and read calls
    related to the escrow lifecycle defined in AuctionEscrow.sol.
 
    It does NOT:
        - Handle HTTP requests
        - Handle user input
        - Manage application flow
 
    It is called by:
        backend.mainauction (controller/orchestration layer)
 
System Position:
 
    Flask (HTTP layer)
        ↓
    backend.mainauction
        ↓
    escrow.py  ← THIS FILE (escrow remote)
        ↓
    Hardhat / Ethereum node
 
Escrow Lifecycle:
    After endAuction() is called, one of three paths resolves the escrow:
 
        1. Buyer calls confirmReceipt()     → funds sent to seller immediately
        2. Seller calls claimAfterTimeout() → funds sent to seller after window expires
        3. Admin calls flagRefund()         → funds queued in pendingReturns for winner
                                              (winner must call withdraw() to collect)
"""
 
from web3 import Web3
 
 
def confirm_receipt(w3, contract, account):
    """
    Called by the winning bidder to confirm they received the item.
    Immediately releases escrowed funds to the seller.
 
    Parameters:
        w3 (Web3):   Active Web3 connection.
        contract:    Web3 contract instance.
        account (str): Address of the winning bidder (msg.sender).
 
    Returns:
        dict:
            {
                "tx_hash":        str,   # Mined transaction hash
                "escrow_settled": bool   # True — escrow is now resolved
            }
 
    Raises:
        Exception: If the transaction reverts (e.g. caller is not the winner,
                   auction has not ended, escrow already settled).
    """
    tx_hash = contract.functions.confirmReceipt().transact({
        "from": account,
    })
 
    w3.eth.wait_for_transaction_receipt(tx_hash)
 
    return {
        "tx_hash": tx_hash.hex(),
        "escrow_settled": True,
    }
 
 
def claim_after_timeout(w3, contract, account):
    """
    Called by the seller when the buyer never confirmed receipt and
    the confirmation window has expired.
    Releases escrowed funds to the seller.
 
    Parameters:
        w3 (Web3):     Active Web3 connection.
        contract:      Web3 contract instance.
        account (str): Address of the seller (msg.sender).
 
    Returns:
        dict:
            {
                "tx_hash":        str,   # Mined transaction hash
                "escrow_settled": bool   # True — escrow is now resolved
            }
 
    Raises:
        Exception: If the transaction reverts (e.g. caller is not the seller,
                   confirmation window has not expired, escrow already settled).
    """
    tx_hash = contract.functions.claimAfterTimeout().transact({
        "from": account,
    })
 
    w3.eth.wait_for_transaction_receipt(tx_hash)
 
    return {
        "tx_hash": tx_hash.hex(),
        "escrow_settled": True,
    }
 
 
def flag_refund(w3, contract, account):
    """
    Called only by the admin to cancel the escrow and return funds to
    the winning bidder via pendingReturns.
 
    NOTE: This does NOT send funds directly — it queues them in
    pendingReturns. The winner must call withdraw() (via withdrawal.py)
    to collect their refund.
 
    Parameters:
        w3 (Web3):     Active Web3 connection.
        contract:      Web3 contract instance.
        account (str): Address of the admin (msg.sender).
 
    Returns:
        dict:
            {
                "tx_hash":       str,   # Mined transaction hash
                "refund_flagged": bool  # True — refund has been queued
            }
 
    Raises:
        Exception: If the transaction reverts (e.g. caller is not admin,
                   auction has not ended, escrow already settled,
                   no funds in escrow).
    """
    tx_hash = contract.functions.flagRefund().transact({
        "from": account,
    })
 
    w3.eth.wait_for_transaction_receipt(tx_hash)
 
    return {
        "tx_hash": tx_hash.hex(),
        "refund_flagged": True,
    }
 
 
def get_time_remaining_for_confirmation(w3, contract):
    """
    Read-only call to check how many seconds remain in the buyer
    confirmation window.
 
    Returns 0 if:
        - The window has already expired
        - Escrow has been settled
        - Auction has not ended yet
 
    Parameters:
        w3 (Web3):  Active Web3 connection.
        contract:   Web3 contract instance.
 
    Returns:
        dict:
            {
                "seconds_remaining": int   # 0 if expired/settled/not ended
            }
    """
    seconds_remaining = contract.functions.timeRemainingForConfirmation().call()
 
    return {
        "seconds_remaining": seconds_remaining,
    }
 