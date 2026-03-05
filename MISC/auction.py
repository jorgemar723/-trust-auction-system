#!/usr/bin/env python3
"""
auction.py

PROJ-54..58: View Auction Details by Auction ID (compatible with current Auction.sol).

Why this file changed:
- Your previous version had placeholders for ABI path and contract address, and it always placed a bid.
- This version adds a safe "view details" flow that:
    1) looks up an auction by ID from auctions.json (title/description + contract address)
    2) fetches highestBid and endTime live from the deployed SimpleAuction contract
    3) prints all required fields
- (Optional) still supports placing a bid with a subcommand.

Usage:
  View details:
    python auction.py view <auction_id> <abi_json_path> [rpc_url] [registry_path]

  Place a bid (optional helper):
    python auction.py bid <auction_id> <abi_json_path> <eth_amount> [rpc_url] [registry_path]

Example (Hardhat local):
  python auction.py view 1 artifacts/contracts/Auction.sol/SimpleAuction.json http://127.0.0.1:8545 auctions.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from web3 import Web3

from auction_details import (
    AuctionNotFoundError,
    fetch_onchain_details,
    format_auction_details,
    get_auction_record,
    load_registry,
)


def _die(msg: str, code: int = 1) -> None:
    print(msg)
    raise SystemExit(code)


def _load_abi(abi_json_path: str | Path):
    p = Path(abi_json_path)
    if not p.exists():
        _die(f"ERROR: ABI file not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if "abi" not in data:
        _die(f"ERROR: ABI JSON missing 'abi' field: {p}")
    return data["abi"]


def _connect(rpc_url: str) -> Web3:
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        _die(f"ERROR: Could not connect to RPC at {rpc_url}")
    return w3


def _contract(w3: Web3, address: str, abi):
    try:
        return w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)
    except Exception as e:
        _die(f"ERROR: Could not build contract for address {address}: {e}")


def _pretty_end_time(unix_ts: int) -> str:
    try:
        dt = datetime.fromtimestamp(int(unix_ts), tz=timezone.utc)
        return dt.isoformat()
    except Exception:
        return str(unix_ts)


def cmd_view(auction_id: int, abi_path: str, rpc_url: str, registry_path: str) -> None:
    registry = load_registry(registry_path)
    try:
        rec = get_auction_record(registry, auction_id)
    except AuctionNotFoundError as e:
        _die(f"ERROR: {e}")

    abi = _load_abi(abi_path)
    w3 = _connect(rpc_url)
    c = _contract(w3, rec.contractAddress, abi)

    try:
        onchain = fetch_onchain_details(c)
    except Exception as e:
        _die(f"ERROR: Failed reading on-chain details: {e}")

    # Convert wei -> ETH for readability
    def wei_to_eth(x):
        return f"{w3.from_wei(int(x), 'ether')} ETH"

    output = format_auction_details(rec, onchain, wei_to_eth=wei_to_eth)
    # Add a nicer end-time line while keeping the required unix display
    output += f"Auction End Date (UTC ISO): {_pretty_end_time(onchain.get('endTime'))}\n"
    print(output, end="")


def cmd_bid(auction_id: int, abi_path: str, eth_amount: str, rpc_url: str, registry_path: str) -> None:
    registry = load_registry(registry_path)
    try:
        rec = get_auction_record(registry, auction_id)
    except AuctionNotFoundError as e:
        _die(f"ERROR: {e}")

    abi = _load_abi(abi_path)
    w3 = _connect(rpc_url)
    c = _contract(w3, rec.contractAddress, abi)

    # Use first local account (Hardhat node exposes unlocked accounts)
    try:
        account = w3.eth.accounts[0]
    except Exception:
        _die("ERROR: No unlocked accounts available from this RPC")

    value_wei = w3.to_wei(float(eth_amount), "ether")
    try:
        tx_hash = c.functions.bid().transact({"from": account, "value": value_wei})
        w3.eth.wait_for_transaction_receipt(tx_hash)
    except Exception as e:
        _die(f"ERROR: bid() transaction failed: {e}")

    print(f"Bid placed from {account} for {eth_amount} ETH on auction {auction_id}.")
    # Show updated details
    cmd_view(auction_id, abi_path, rpc_url, registry_path)


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] in {"-h", "--help"}:
        print(__doc__.strip())
        return

    sub = argv[1].lower()

    if sub == "view":
        if len(argv) < 4:
            _die("Usage: python auction.py view <auction_id> <abi_json_path> [rpc_url] [registry_path]")
        auction_id = int(argv[2])
        abi_path = argv[3]
        rpc_url = argv[4] if len(argv) >= 5 else "http://127.0.0.1:8545"
        registry_path = argv[5] if len(argv) >= 6 else "auctions.json"
        cmd_view(auction_id, abi_path, rpc_url, registry_path)
        return

    if sub == "bid":
        if len(argv) < 5:
            _die("Usage: python auction.py bid <auction_id> <abi_json_path> <eth_amount> [rpc_url] [registry_path]")
        auction_id = int(argv[2])
        abi_path = argv[3]
        eth_amount = argv[4]
        rpc_url = argv[5] if len(argv) >= 6 else "http://127.0.0.1:8545"
        registry_path = argv[6] if len(argv) >= 7 else "auctions.json"
        cmd_bid(auction_id, abi_path, eth_amount, rpc_url, registry_path)
        return

    _die(f"Unknown command '{sub}'. Use --help.", 2)


if __name__ == "__main__":
    main(sys.argv)
