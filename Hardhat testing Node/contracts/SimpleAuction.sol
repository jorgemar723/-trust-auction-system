// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./Auction/AuctionBidding.sol";
import "./Auction/AuctionSettlement.sol";

/**
 * SimpleAuction.sol
 *
 * Purpose:
 *     Top-level auction contract. Acts as the orchestrator, wiring together
 *     all auction modules via inheritance.
 *
 *     This contract does NOT:
 *         - Contain bid or settlement logic directly
 *         - Define state variables directly (via AuctionState)
 *
 *     It inherits from:
 *         AuctionBidding    → bid()
 *         AuctionSettlement → withdraw(), endAuction()
 *         AuctionState      → all state variables and events
 *                             (inherited transitively)
 *
 * System Position:
 *
 *     AuctionFactory.sol  (deployment)
 *         ↓
 *     SimpleAuction.sol  ← THIS FILE (orchestrator)
 *         ↓
 *     AuctionBidding.sol / AuctionSettlement.sol
 *         ↓
 *     AuctionState.sol  (shared storage)
 *
 * Equivalent to:
 *     mainauction.py on the Python side
 */

contract SimpleAuction is AuctionBidding, AuctionSettlement {

    constructor(uint256 _biddingTimeSeconds, address _seller, uint256 _startingBid) {
        seller = _seller;
        endTime = block.timestamp + _biddingTimeSeconds;
        startingBid = _startingBid;
    }
}
