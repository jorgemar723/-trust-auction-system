import json
from web3 import Web3

#test
def connect_web3(provider_url="http://127.0.0.1:8545"):
    w3 = Web3(Web3.HTTPProvider(provider_url))
    if not w3.is_connected():
        raise Exception("Web3 connection failed.")
    return w3


def load_contract(w3, abi_path, contract_address):
    with open(abi_path) as f:
        contract_json = json.load(f)
        abi = contract_json["abi"]

    return w3.eth.contract(
        address=contract_address,
        abi=abi
    )


def place_bid(w3, contract, account, bid_amount_eth):
    bid_amount_wei = w3.to_wei(bid_amount_eth, "ether")

    tx_hash = contract.functions.bid().transact({
        "from": account,
        "value": bid_amount_wei
    })

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    highest = contract.functions.highestBid().call()

    return {
        "tx_hash": tx_hash.hex(),
        "highest_bid_wei": highest
    }
