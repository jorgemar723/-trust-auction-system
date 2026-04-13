// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./SimpleAuction.sol";

contract AuctionFactory {

    address[] public auctions;

    event AuctionCreated(
        address auctionAddress,
        address seller,
        uint256 biddingTimeSeconds,
        uint256 endTime,
        uint256 startingBid
    );

    function createAuction(uint256 biddingTimeSeconds, uint256 startingBid) external returns (address) {

        SimpleAuction auction = new SimpleAuction(biddingTimeSeconds, msg.sender, startingBid);

        address auctionAddress = address(auction);

        auctions.push(auctionAddress);

        emit AuctionCreated(
            auctionAddress,
            msg.sender,
            biddingTimeSeconds,
            auction.endTime(),
            startingBid
        );

        return auctionAddress;
    }

    function getAuctions() external view returns (address[] memory) {
        return auctions;
    }

    function auctionCount() external view returns (uint256) {
        return auctions.length;
    }
}