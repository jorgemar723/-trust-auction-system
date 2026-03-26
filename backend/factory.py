import json
from web3 import Web3
from pathlib import Path

from .bidding import connect_web3
from .errors import BackendAPIError

_REPO_ROOT = Path(__file__).resolve().parents[1]

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

    with open(_FACTORY_ABI_PATH) as f:
        contract_json = json.load(f)

    abi = contract_json["abi"]

    return w3.eth.contract(
        address=_FACTORY_ADDRESS,
        abi=abi
    )


def create_auction(duration_seconds: int, sender_address: str):

    w3 = connect_web3()
    factory = load_factory(w3)
    
    # Makes sure wallet exists
    if not sender_address or not Web3.is_address(sender_address):
        raise BackendAPIError(
            code="MISSING_WALLET",
            message="User does not have a wallet address configured",
            details="sender_address is None or empty"
        )

    try:
        tx_hash = factory.functions.createAuction(
            duration_seconds
        ).transact({
            "from": sender_address
        })

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        events = factory.events.AuctionCreated().process_receipt(receipt)

        print("EVENTS:", events)

        if not events:
            raise BackendAPIError(
                code="EVENT_NOT_FOUND",
                message="AuctionCreated event not found in receipt",
                details=str(receipt)
            )

        event = events[0]

        auction_address = event["args"]["auctionAddress"]

        return {
            "auction_address": auction_address,
            "tx_hash": tx_hash.hex()
        }

    except Exception as e:
        raise BackendAPIError(
            code="AUCTION_CREATION_FAILED",
            message="Failed to create auction",
            details=str(e)
        ) from e