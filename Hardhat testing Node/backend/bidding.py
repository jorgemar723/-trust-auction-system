"""
bidding.py

Purpose:
    Blockchain WRITE interaction layer for the auction system.

    This module is responsible for sending state-changing transactions
    to the smart contract (e.g., placing bids).

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
    bidding.py  ← THIS FILE (write remote)
        ↓
    Hardhat / Ethereum node
"""

import json
from web3 import Web3


def connect_web3(provider_url="http://127.0.0.1:8545"):
    """
    Establish a connection to a Web3 provider.

    Parameters:
        provider_url (str): JSON-RPC endpoint (default: local Hardhat node)

    Returns:
        Web3: Active Web3 connection instance

    Raises:
        Exception if connection fails.
    """
    w3 = Web3(Web3.HTTPProvider(provider_url))

    if not w3.is_connected():
        raise Exception("Web3 connection failed.")

    return w3


def load_contract(w3, abi_path, contract_address):
    """
    Load a deployed smart contract instance.

    Parameters:
        w3 (Web3): Active Web3 connection
        abi_path (str): Path to compiled contract JSON artifact
        contract_address (str): Deployed contract address

    Returns:
        Contract: Web3 contract instance
    """
    with open(abi_path) as f:
        contract_json = json.load(f)
        abi = contract_json["abi"]

    return w3.eth.contract(
        address=contract_address,
        abi=abi
    )


def place_bid(w3, contract, account, bid_amount_eth):
    """
    Submit a bid transaction to the auction smart contract.

    This function sends a state-changing transaction to the blockchain.

    Parameters:
        w3 (Web3): Active Web3 connection
        contract: Web3 contract instance
        account (str): Address placing the bid
        bid_amount_eth (float): Bid amount in ETH

    Returns:
        dict:
            {
                "tx_hash": str,
                "highest_bid_wei": int
            }

    Notes:
        - Assumes the contract has a payable function named `bid()`.
        - Assumes the contract has a public getter `highestBid()`.
        - Relies on the local node having unlocked accounts (Hardhat default).
    """

    # Convert ETH to wei (smallest denomination)
    bid_amount_wei = w3.to_wei(bid_amount_eth, "ether")

    # Send transaction to contract
    tx_hash = contract.functions.bid().transact({
        "from": account,
        "value": bid_amount_wei
    })

    # Wait for transaction to be mined
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # Retrieve updated highest bid from contract
    highest = contract.functions.highestBid().call()

    return {
        "tx_hash": tx_hash.hex(),
        "highest_bid_wei": highest
    }