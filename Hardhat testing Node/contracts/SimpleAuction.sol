// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SimpleAuction {
    address public seller;
    uint256 public endTime;

    address public highestBidder;
    uint256 public highestBid;
    uint256 public startingBid;

    bool public ended;

    mapping(address => uint256) public pendingReturns;

    event HighestBidIncreased(address bidder, uint256 amount);
    event AuctionEnded(address winner, uint256 amount);

    constructor(uint256 _biddingTimeSeconds, address _seller, uint256 _startingBid) {
        seller = _seller;
        endTime = block.timestamp + _biddingTimeSeconds;
        startingBid = _startingBid;
    }

    function bid() external payable {
        require(block.timestamp < endTime, "Auction already ended");
        require(msg.value >= startingBid, "Bid is below starting bid");
        require(msg.value > highestBid, "Bid not high enough");

        if (highestBid != 0) {
            pendingReturns[highestBidder] += highestBid;
        }

        highestBidder = msg.sender;
        highestBid = msg.value;

        emit HighestBidIncreased(msg.sender, msg.value);
    }

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
