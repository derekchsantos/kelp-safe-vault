// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../contracts/SafeVault.sol";

contract DeployScript is Script {
    function run() external {
        // Pega a chave privada do ambiente
        uint256 deployerPrivateKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        
        // Inicia a transmissão
        vm.startBroadcast(deployerPrivateKey);
        
        // Implanta o contrato
        SafeVault safeVault = new SafeVault();
        
        // Para de transmitir
        vm.stopBroadcast();
        
        // Imprime o endereço
        console.log("SafeVault deployed at:", address(safeVault));
    }
}
