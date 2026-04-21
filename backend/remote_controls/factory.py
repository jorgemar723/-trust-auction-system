"""
factory.py
 
Purpose:
    Blockchain WRITE interaction layer for auction creation.
 
    This module is responsible for deploying new auction contracts
    on-chain via the AuctionFactory smart contract.
 
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
    factory.py  ← THIS FILE (auction creation remote)
        ↓
    Hardhat / Ethereum node
"""
 
import json
from pathlib import Path
from web3 import Web3
 
from .auction_loader import connect_web3
from .errors import BackendAPIError
 
_REPO_ROOT = Path(__file__).resolve().parents[2]
 
_FACTORY_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
 
_FACTORY_ABI_PATH = (
    _REPO_ROOT
    / "Hardhat testing Node"
    / "artifacts"
    / "contracts"
    / "AuctionFactory.sol"
    / "AuctionFactory.json"
)
 
 
def load_factory(w3):
    """
    Load the AuctionFactory contract instance.
 
    Parameters:
        w3 (Web3): Active Web3 connection.
 
    Returns:
        Contract: Web3 contract instance for AuctionFactory.
    """
    with open(_FACTORY_ABI_PATH) as f:
        contract_json = json.load(f)
 
    abi = contract_json["abi"]
 
    return w3.eth.contract(
        address=_FACTORY_ADDRESS,
        abi=abi,
    )
 
 
def create_auction(
    duration_seconds: int,
    sender_address: str,
    starting_bid_eth: float,
    confirmation_window: int = 259200,  # default: 3 days in seconds
):
    """
    Deploy a new auction contract via AuctionFactory.
 
    Parameters:
        duration_seconds  (int):   How long the auction runs (seconds).
        sender_address    (str):   Seller's wallet address.
        starting_bid_eth  (float): Minimum opening bid in ETH.
        confirmation_window (int): Seconds the buyer has to confirm receipt
                                   before the seller can claim timeout.
                                   Default: 3 days (259200 seconds).
 
    Returns:
        dict:
            {
                "auction_address": str,  # Address of the deployed auction
                "tx_hash":         str,  # Transaction hash
            }
 
    Raises:
        BackendAPIError: MISSING_WALLET if sender_address is invalid.
        BackendAPIError: EVENT_NOT_FOUND if AuctionCreated event is missing
                         from the transaction receipt.
        BackendAPIError: AUCTION_CREATION_FAILED if the transaction fails.
    """
    w3 = connect_web3()
    factory = load_factory(w3)
    starting_bid_wei = w3.to_wei(starting_bid_eth, "ether")
 
    if sender_address:
        sender_address = Web3.to_checksum_address(sender_address)
 
    if not sender_address or not Web3.is_address(sender_address):
        raise BackendAPIError(
            code="MISSING_WALLET",
            message="User does not have a wallet address configured.",
            details="sender_address is None or empty",
        )
 
    try:
        tx_hash = factory.functions.createAuction(
            duration_seconds,
            starting_bid_wei,
            confirmation_window,
        ).transact({
            "from": sender_address,
        })
 
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        events  = factory.events.AuctionCreated().process_receipt(receipt)
 
        print("EVENTS:", events)
 
        if not events:
            raise BackendAPIError(
                code="EVENT_NOT_FOUND",
                message="AuctionCreated event not found in receipt.",
                details=str(receipt),
            )
 
        auction_address = events[0]["args"]["auctionAddress"]
 
        return {
            "auction_address": auction_address,
            "tx_hash":         tx_hash.hex(),
        }
 
    except Exception as e:
        raise BackendAPIError(
            code="AUCTION_CREATION_FAILED",
            message="Failed to create auction.",
            details=str(e),
        ) from e
 