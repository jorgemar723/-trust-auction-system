"""
withdrawal.py
 
Purpose:
    Blockchain WRITE interaction layer for pending fund withdrawals.
 
    This module handles the withdraw() function defined in AuctionSettlement.sol.
    It is used by any address that has funds queued in pendingReturns — most
    commonly outbid bidders, or the winning bidder after an admin flagRefund().
 
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
    withdrawal.py  ← THIS FILE (withdrawal remote)
        ↓
    Hardhat / Ethereum node
 
When pendingReturns are populated:
    - A bidder is outbid during the auction       → their prior bid is queued
    - Admin calls flagRefund() post-auction       → winner's escrowed bid is queued
"""
 
from web3 import Web3
 
 
def withdraw(w3, contract, account):
    """
    Withdraw all funds queued in pendingReturns for the given account.
 
    The contract zeroes out pendingReturns[account] before attempting the
    transfer (checks-effects-interactions pattern), so a failed send will
    restore the balance — the caller can safely retry.
 
    Parameters:
        w3 (Web3):     Active Web3 connection.
        contract:      Web3 contract instance.
        account (str): Address requesting the withdrawal (msg.sender).
 
    Returns:
        dict:
            {
                "tx_hash":          str,   # Mined transaction hash
                "amount_withdrawn_wei": int,  # Amount withdrawn in wei
                "amount_withdrawn_eth": float # Amount withdrawn in ETH
            }
 
    Raises:
        Exception: If the transaction reverts (e.g. no funds in pendingReturns
                   for this account).
        ValueError: If the on-chain send fails (contract returns false) —
                    funds are restored in pendingReturns and the caller can retry.
    """
    # Read pending balance before the transaction so we can report it
    pending_wei = contract.functions.pendingReturns(account).call()
 
    if pending_wei == 0:
        raise ValueError(
            f"No pending funds to withdraw for account {account}."
        )
 
    tx_hash = contract.functions.withdraw().transact({
        "from": account,
    })
 
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
 
    # Confirm the withdrawal succeeded (contract returns bool)
    # If send() failed on-chain the contract restores the balance and returns False,
    # but the tx itself won't revert — we detect this via the return value.
    # web3.py does not surface Solidity return values from transact(), so we
    # verify by checking pendingReturns is now zero.
    remaining_wei = contract.functions.pendingReturns(account).call()
    if remaining_wei != 0:
        raise ValueError(
            "Withdrawal transaction was mined but the on-chain send failed. "
            "Funds have been restored — please retry."
        )
 
    amount_eth = w3.from_wei(pending_wei, "ether")
 
    return {
        "tx_hash": tx_hash.hex(),
        "amount_withdrawn_wei": pending_wei,
        "amount_withdrawn_eth": float(amount_eth),
    }
 