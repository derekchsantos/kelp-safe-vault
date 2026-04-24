const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("SafeVault", function () {
  let safeVault;
  let owner;
  let user1;
  let user2;

  beforeEach(async function () {
    [owner, user1, user2] = await ethers.getSigners();
    const SafeVault = await ethers.getContractFactory("SafeVault");
    safeVault = await SafeVault.deploy();
    await safeVault.waitForDeployment();
  });

  describe("Depósito", function () {
    it("Deve permitir depósito de ETH", async function () {
      await safeVault.connect(user1).deposit({ value: ethers.parseEther("1") });
      expect(await safeVault.balances(user1.address)).to.equal(ethers.parseEther("1"));
    });
  });

  describe("Saque", function () {
    it("Deve permitir saque com saldo suficiente", async function () {
      await safeVault.connect(user1).deposit({ value: ethers.parseEther("1") });
      await safeVault.connect(user1).withdraw(ethers.parseEther("1"));
      expect(await safeVault.balances(user1.address)).to.equal(0);
    });
  });

  describe("Pausa", function () {
    it("Apenas owner pode pausar", async function () {
      await safeVault.pause();
      expect(await safeVault.paused()).to.be.true;
    });
  });

  describe("Teste de Reentrância", function () {
    it("Deve prevenir ataque de reentrância", async function () {
      const Attacker = await ethers.getContractFactory("ReentrancyAttack");
      const attacker = await Attacker.deploy(await safeVault.getAddress());
      await attacker.waitForDeployment();

      const depositAmount = ethers.parseEther("10");
      await attacker.attack({ value: depositAmount });

      const attackerBalanceInVault = await safeVault.balances(attacker.getAddress());
      expect(attackerBalanceInVault).to.equal(0);
      
      console.log("✅ Teste de Reentrância: Protegido!");
    });
  });
});
