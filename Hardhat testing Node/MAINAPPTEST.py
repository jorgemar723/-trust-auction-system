from bidding import connect_web3, load_contract, place_bid

w3 = connect_web3()

contract = load_contract(
    w3,
    abi_path="path/to/SimpleAuction.json",
    contract_address="0xYourContractAddress"
)

account = w3.eth.accounts[0]

user_bid = float(input("Enter bid in ETH: "))

result = place_bid(w3, contract, account, user_bid)

print("Bid placed!")
print("Transaction hash:", result["tx_hash"])
print("New highest bid (wei):", result["highest_bid_wei"])