import hre from "hardhat";

async function main() {

  const { ethers } = await hre.network.connect();

  const factoryAddress = "0x5FbDB2315678afecb367f032d93F642f64180aa3";

  const factory = await ethers.getContractAt(
    "AuctionFactory",
    factoryAddress
  );

  const duration = 3600;

  const tx = await factory.createAuction(duration);
  const receipt = await tx.wait();

  const event = receipt.logs.find(
    (log) => log.fragment && log.fragment.name === "AuctionCreated"
  );

  console.log("New auction:", event.args.auctionAddress);
}

main().catch(console.error);
