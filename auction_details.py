import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class AuctionRecord:
    """Off-chain registry record for an on-chain auction contract.

    We store human-facing metadata (title/description) off-chain, while
    fetching dynamic on-chain state (highestBid/endTime) live from the chain.
    """

    auctionId: int
    title: str
    description: str
    contractAddress: str


class AuctionNotFoundError(KeyError):
    pass


def load_registry(path: str | Path) -> Dict[int, AuctionRecord]:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    auctions: Dict[int, AuctionRecord] = {}
    for item in data.get("auctions", []):
        rec = AuctionRecord(
            auctionId=int(item["auctionId"]),
            title=str(item["title"]),
            description=str(item["description"]),
            contractAddress=str(item["contractAddress"]),
        )
        auctions[rec.auctionId] = rec
    return auctions


def get_auction_record(registry: Dict[int, AuctionRecord], auction_id: int) -> AuctionRecord:
    """
    PROJ-56: Retrieve an AuctionRecord by auction_id from the loaded registry.
    Raises AuctionNotFoundError when the ID is not present.
    """

    try:
        return registry[int(auction_id)]
    except Exception as e:
        raise AuctionNotFoundError(f"Auction ID {auction_id} not found") from e


def fetch_onchain_details(contract: Any) -> Dict[str, Any]:
    """Fetch the on-chain fields required by PROJ-54.

    Contract is expected to be a Web3.py contract instance for Auction.sol's
    SimpleAuction.
    """
    highest_bid_wei = contract.functions.highestBid().call()
    end_time_unix = contract.functions.endTime().call()
    return {
        "highestBid": highest_bid_wei,
        "endTime": end_time_unix,
    }

def fetch_trustauction_state(contract: Any, auction_id: int) -> Dict[str, Any]:
    """
    PROJ-38: Fetch on-chain auction state via TRUSTAuction.getAuctionState(auctionId).

    Expects contract to be a Web3.py contract instance for TRUSTAuction.sol.
    Returns a Python-friendly dict.
    """
    # Solidity returns: (seller, itemDescription, highestBid, highestBidder, endTime, isOpen)
    (seller, item_desc, highest_bid, highest_bidder, end_time, is_open) = (
        contract.functions.getAuctionState(int(auction_id)).call()
    )

    return {
        "seller": seller,
        "itemDescription": item_desc,
        "highestBid": int(highest_bid),
        "highestBidder": highest_bidder,
        "endTime": int(end_time),
        "isOpen": bool(is_open),
        "status": "OPEN" if is_open else "CLOSED",
    }
    
def format_auction_details(
    auction: AuctionRecord,
    onchain: Dict[str, Any],
    *,
    wei_to_eth: Optional[callable] = None,
) -> str:
    """Create a readable, CLI-friendly output."""
    highest = onchain.get("highestBid")
    end_time = onchain.get("endTime")

    if wei_to_eth is None:
        highest_display = str(highest)
    else:
        highest_display = str(wei_to_eth(highest))

    return (
        f"Auction ID: {auction.auctionId}\n"
        f"Title: {auction.title}\n"
        f"Description: {auction.description}\n"
        f"Current Highest Bid: {highest_display}\n"
        f"Auction End Date (unix): {end_time}\n"
    )
