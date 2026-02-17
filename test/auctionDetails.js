import { expect } from "chai";
import fs from "fs";
import { JsonRpcProvider, Wallet, ContractFactory } from "ethers";

describe("SimpleAuction Contract Tests", function () {
  const RPC_URL = "http://127.0.0.1:8545";

  // Hardhat node default keys (from your node output)
  const PK0 =
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"; // Account #0
  const PK1 =
    "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"; // Account #1

  const ARTIFACT_PATH = "./artifacts/contracts/Auction.sol/SimpleAuction.json";

  function loadArtifact() {
    return JSON.parse(fs.readFileSync(ARTIFACT_PATH, "utf8"));
  }

  async function deployWithKey(privateKey) {
    const artifact = loadArtifact();
    const provider = new JsonRpcProvider(RPC_URL);
    const wallet = new Wallet(privateKey, provider);
    const factory = new ContractFactory(artifact.abi, artifact.bytecode, wallet);
    const contract = await factory.deploy(1000);
    await contract.waitForDeployment();
    return { contract, provider, wallet };
  }

  it("deploys and sets endTime properly", async function () {
    const { contract } = await deployWithKey(PK0);
    const endTime = await contract.endTime();
    expect(Number(endTime)).to.be.greaterThan(0);
  });

  it("updates highestBid after a bid", async function () {
    const { contract } = await deployWithKey(PK1);

    const bidTx = await contract.bid({
      value: BigInt("1000000000000000000"), // 1 ETH
    });
    await bidTx.wait();

    const highestBid = await contract.highestBid();
    expect(highestBid).to.equal(BigInt("1000000000000000000"));
  });
});
