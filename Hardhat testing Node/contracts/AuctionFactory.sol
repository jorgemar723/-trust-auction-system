// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./SimpleAuction.sol";

contract AuctionFactory {

    address[] public auctions;

    event AuctionCreated(
        address auctionAddress,
        address seller,
        uint256 biddingTimeSeconds,
        uint256 endTime
    );

    function createAuction(uint256 biddingTimeSeconds) external returns (address) {

        // Deploy a new SimpleAuction contract
        SimpleAuction auction = new SimpleAuction(biddingTimeSeconds,msg.sender);

        address auctionAddress = address(auction);

        // Track deployed auction
        auctions.push(auctionAddress);

        emit AuctionCreated(
            auctionAddress,
            msg.sender,
            biddingTimeSeconds,
            auction.endTime()
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