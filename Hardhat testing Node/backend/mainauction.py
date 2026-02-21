from .bidding import connect_web3, load_contract, place_bid

w3 = connect_web3()
contract = load_contract(
    w3,
    abi_path="artifacts/contracts/SimplAuction.sol/SimpleAuction.json",
    contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3"
)

account = w3.eth.accounts[0]

def submit_bid(user_bid):
    return place_bid(w3, contract, account, user_bid)
