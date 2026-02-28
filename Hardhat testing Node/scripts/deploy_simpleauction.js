import hre from "hardhat";

async function main() {
  const { ethers } = await hre.network.connect();
  const biddingTimeSeconds = 3600;

  const auction = await ethers.deployContract("SimpleAuction", [biddingTimeSeconds]);
  await auction.waitForDeployment();

  console.log("SimpleAuction deployed to:", await auction.getAddress());
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
