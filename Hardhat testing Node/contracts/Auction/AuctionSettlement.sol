// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./AuctionState.sol";

/**
 * AuctionSettlement.sol
 *
 * Purpose:
 *     Handles auction finalization and fund withdrawals.
 *
 *     This contract does NOT:
 *         - Define state variables (inherited from AuctionState)
 *         - Handle bid placement logic
 *
 *     It is inherited by:
 *         SimpleAuction.sol
 *
 * System Position:
 *
 *     SimpleAuction.sol  (orchestrator)
 *         ↓
 *     AuctionSettlement.sol  ← THIS FILE (settlement logic)
 *         ↓
 *     AuctionState.sol  (shared storage)
 */

abstract contract AuctionSettlement is AuctionState {

    function withdraw() external returns (bool) {
        uint256 amount = pendingReturns[msg.sender];
        require(amount > 0, "No funds to withdraw");

        pendingReturns[msg.sender] = 0;

        if (!payable(msg.sender).send(amount)) {
            pendingReturns[msg.sender] = amount;
            return false;
        }
        return true;
    }

    function endAuction() external {
        require(block.timestamp >= endTime, "Auction not yet ended");
        require(!ended, "Auction already closed");

        ended = true;

        emit AuctionEnded(highestBidder, highestBid);

        payable(seller).transfer(highestBid);
    }
}