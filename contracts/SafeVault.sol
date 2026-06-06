// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title SafeVault
 * @notice Smart contract with reentrancy protection and pause mechanism
 * @dev Inspired by lessons from the KelpDAO incident (April 2026)
 */

contract SafeVault {
    mapping(address => uint256) public balances;
    bool public paused;
    address public owner;
    
    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);
    event Paused(address indexed by);
    event Unpaused(address indexed by);
    event EmergencyFreeze(address indexed target, uint256 amountFrozen);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this");
        _;
    }
    
    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    // Função interna para atualizar o saldo (evita problemas de chamada)
    function _deposit(address user, uint256 amount) internal {
        balances[user] += amount;
        emit Deposit(user, amount);
    }
    
    function deposit(uint256 amount) external payable whenNotPaused {
        require(amount > 0, "Amount must be greater than zero");
        _deposit(msg.sender, amount);
    }
    
    function withdraw(uint256 amount) external whenNotPaused {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        // Checks-Effects-Interactions pattern (Prevents Reentrancy)
        balances[msg.sender] -= amount;
        
        (bool success,) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        emit Withdrawal(msg.sender, amount);
    }
    
    function pause() external onlyOwner {
        paused = true;
        emit Paused(msg.sender);
    }
    
    function unpause() external onlyOwner {
        paused = false;
        emit Unpaused(msg.sender);
    }
    
    // Emergency freeze function (similar to Arbitrum freeze)
    function emergencyFreeze(address target) external onlyOwner {
        uint256 amount = balances[target];
        balances[target] = 0;
        emit EmergencyFreeze(target, amount);
    }
    
    receive() external payable {
        // Chama a função interna diretamente
        _deposit(msg.sender, msg.value);
    }
}
