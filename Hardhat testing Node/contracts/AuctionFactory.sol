// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./SimpleAuction.sol";

/**
 * AuctionFactory.sol
 *
 * Purpose:
 *     Deploys new SimpleAuction instances and keeps a registry of them.
 *
 *     The factory deployer is automatically set as the admin for every
 *     auction it creates. The admin address is the only address that can
 *     trip the emergency refund flag on any auction deployed by this factory.
 *
 *     If you need per-auction admins, replace `address(this)` / the stored
 *     admin below with a per-call parameter.
 */
contract AuctionFactory {

    // The address that deployed this factory — set as admin on every auction
    address public immutable factoryAdmin;

    address[] public auctions;

    event AuctionCreated(
        address auctionAddress,
        address seller,
        uint256 biddingTimeSeconds,
        uint256 endTime,
        uint256 startingBid,
        address admin,
        uint256 confirmationWindow
    );

    constructor() {
        factoryAdmin = msg.sender;
    }

    /**
     * @param biddingTimeSeconds  How long the auction runs (in seconds)
     * @param startingBid         Minimum bid in wei
     * @param confirmationWindow  Seconds the buyer has to confirm receipt after auction ends
     *                            e.g. 259200 = 3 days
     */
    function createAuction(
        uint256 biddingTimeSeconds,
        uint256 startingBid,
        uint256 confirmationWindow
    ) external returns (address) {
            require(biddingTimeSeconds > 0, "Bidding time must be greater than 0");
            require(startingBid > 0, "Starting bid must be greater than 0");
            require(confirmationWindow > 0, "Confirmation window must be greater than 0");

        SimpleAuction auction = new SimpleAuction(
            biddingTimeSeconds,
            msg.sender,       // seller
            startingBid,
            factoryAdmin,     // admin — factory deployer can trip refund flag
            confirmationWindow
        );

        address auctionAddress = address(auction);

        auctions.push(auctionAddress);

        emit AuctionCreated(
            auctionAddress,
            msg.sender,
            biddingTimeSeconds,
            auction.endTime(),
            startingBid,
            factoryAdmin,
            confirmationWindow
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