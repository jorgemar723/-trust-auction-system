import json
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
print("Connected:", w3.is_connected())

# Load ABI
with open("/home/biggie/TRUST/trust/Hardhat testing Node/artifacts/SimpleAuction.json") as f:
    contract_json = json.load(f)
    abi = contract_json["abi"]

contract_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

contract = w3.eth.contract(
    address=contract_address,
    abi=abi
)

account = w3.eth.accounts[0]

tx_hash = contract.functions.bid().transact({
    "from": account,
    "value": w3.to_wei(1, "ether")
})

w3.eth.wait_for_transaction_receipt(tx_hash)

print("Bid placed!")

highest = contract.functions.highestBid().call()
print("Highest bid:", w3.from_wei(highest, "ether"), "ETH")
