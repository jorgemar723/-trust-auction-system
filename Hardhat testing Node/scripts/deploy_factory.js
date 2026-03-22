import hre from "hardhat";

async function main() {
  const { ethers } = await hre.network.connect();

  const factory = await ethers.deployContract("AuctionFactory");
  await factory.waitForDeployment();

  console.log("Factory deployed:", await factory.getAddress());
}

main().catch(console.error);
