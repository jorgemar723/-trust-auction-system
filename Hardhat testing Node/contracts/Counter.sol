// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract Counter {
    uint256 public count;

    event CountChanged(uint256 newCount);

    function increment() public {
        count += 1;
        emit CountChanged(count);
    }

    function decrement() public {
        require(count > 0, "Cannot go below zero");
        count -= 1;
        emit CountChanged(count);
    }

    function reset() public {
        count = 0;
        emit CountChanged(count);
    }
}
