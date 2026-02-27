import fs from "fs";
import { JsonRpcProvider, Wallet, ContractFactory } from "ethers";

const RPC_URL = "http://127.0.0.1:8545";

// Hardhat local node Account #0 private key (the one it prints)
const PRIVATE_KEY =
  "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80";

const ARTIFACT_PATH = "./artifacts/contracts/Auction.sol/SimpleAuction.json";

async function main() {
  const artifact = JSON.parse(fs.readFileSync(ARTIFACT_PATH, "utf8"));

  // Hardhat artifact format: abi + bytecode
  const abi = artifact.abi;
  const bytecode = artifact.bytecode;

  const provider = new JsonRpcProvider(RPC_URL);
  const wallet = new Wallet(PRIVATE_KEY, provider);

  const factory = new ContractFactory(abi, bytecode, wallet);

  // constructor(uint _biddingTime)
  const contract = await factory.deploy(1000);

  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("DEPLOYED_ADDRESS:", address);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
