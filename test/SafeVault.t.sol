// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../contracts/SafeVault.sol";
import "./ReentrancyAttack.sol"; // Importa o contrato atacante que você já tem

contract SafeVaultTest is Test {
    SafeVault public vault;
    address public owner;
    address public user1;
    address public user2;

    function setUp() public {
        owner = address(this);
        user1 = makeAddr("user1");
        user2 = makeAddr("user2");
        
        vault = new SafeVault();
    }

    // --- Testes Básicos ---

    function testDeposit() public {
        vm.deal(user1, 1 ether);
        vm.prank(user1);
        vault.deposit{value: 1 ether}();
        
        assertEq(vault.balances(user1), 1 ether);
    }

    function testWithdraw() public {
        vm.deal(user1, 1 ether);
        vm.prank(user1);
        vault.deposit{value: 1 ether}();
        
        vm.prank(user1);
        vault.withdraw(1 ether);
        
        assertEq(vault.balances(user1), 0);
        assertEq(user1.balance, 1 ether); // O usuário recuperou o ETH
    }

    function testPause() public {
        vault.pause();
        assertTrue(vault.paused());
        
        vm.deal(user1, 1 ether);
        vm.expectRevert("Contract is paused");
        vm.prank(user1);
        vault.deposit{value: 1 ether}();
    }

    function testOnlyOwnerPause() public {
        vm.expectRevert("Only owner can call this");
        vm.prank(user1);
        vault.pause();
    }

    // --- Teste de Reentrância (O mais importante!) ---

    function testReentrancyProtection() public {
        // 1. Criar o atacante
        ReentrancyAttack attacker = new ReentrancyAttack(address(vault));
        
        // 2. Dar ETH para o atacante
        uint256 depositAmount = 10 ether;
        vm.deal(address(attacker), depositAmount);
        
        // 3. O atacante deposita e tenta sacar (ataque)
        vm.prank(address(attacker));
        attacker.attack{value: depositAmount}();
        
        // 4. Verificações
        // O saldo do atacante no vault deve ser 0 (pois ele sacou tudo)
        assertEq(vault.balances(address(attacker)), 0);
        
        // O saldo total do atacante (no contrato + no vault) não deve exceder o depósito inicial
        // Se o ataque tivesse sucesso, o saldo final seria maior que o inicial
        uint256 finalBalance = address(attacker).balance;
        
        // O saldo final deve ser menor que o depósito inicial (devido ao gas)
        // Se fosse maior, o ataque teria funcionado
        assertLt(finalBalance, depositAmount); 
        
        console.log("Reentrancy Test: Protected! Attack failed.");
    }
}
