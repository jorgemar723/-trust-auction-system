// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * AuctionState.sol
 *
 * Purpose:
 *     Base contract that defines all shared state variables and events
 *     for the auction system.
 *
 *     This contract does NOT:
 *         - Contain any business logic
 *         - Handle bids or settlements
 *
 *     It is inherited by:
 *         AuctionBidding.sol
 *         AuctionSettlement.sol
 *         SimpleAuction.sol
 *
 * System Position:
 *
 *     SimpleAuction.sol  (orchestrator)
 *         ↓
 *     AuctionBidding.sol / AuctionSettlement.sol
 *         ↓
 *     AuctionState.sol  ← THIS FILE (shared storage)
 */

abstract contract AuctionState {

    // ─── Auction Parameters ───────────────────────────────────────────────
    address public seller;
    uint256 public endTime;
    uint256 public startingBid;

    // ─── Bid Tracking ─────────────────────────────────────────────────────
    address public highestBidder;
    uint256 public highestBid;

    // ─── Settlement ───────────────────────────────────────────────────────
    bool public ended;

    // ─── Pending Withdrawals ──────────────────────────────────────────────
    mapping(address => uint256) public pendingReturns;

    // ─── Events ───────────────────────────────────────────────────────────
    event HighestBidIncreased(address indexed bidder, uint256 amount);
    event AuctionEnded(address indexed winner, uint256 amount);
}