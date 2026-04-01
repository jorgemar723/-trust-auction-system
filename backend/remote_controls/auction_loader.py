import json
from pathlib import Path
from web3 import Web3
from .errors import BackendAPIError

_REPO_ROOT = Path(__file__).resolve().parents[2]
 
_ABI_PATH = (
    _REPO_ROOT
    / "Hardhat testing Node"
    / "artifacts"
    / "contracts"
    / "SimpleAuction.sol"
    / "SimpleAuction.json"
)
print("ABI PATH:", _ABI_PATH)


def connect_web3(provider_url: str = "http://127.0.0.1:8545"):
    """
    Establish a connection to a Web3 provider.

    Parameters:
        provider_url (str): JSON-RPC endpoint (default: local Hardhat node)

    Returns:
        Web3: Active Web3 connection instance

    Raises:
        Exception if connection fails.
    """
    w3 = Web3(Web3.HTTPProvider(provider_url))

    if not w3.is_connected():
        raise Exception("Web3 connection failed.")

    return w3


def load_contract(w3,contract_address: str):
    """
    Load a deployed smart contract instance.

    Parameters:
        w3 (Web3): Active Web3 connection
        abi_path (str): Path to compiled contract JSON artifact
        contract_address (str): Deployed contract address

    Returns:
        Contract: Web3 contract instance
    """
    with open(_ABI_PATH) as f:
        contract_json = json.load(f)
        abi = contract_json["abi"]

    return w3.eth.contract(
        address=contract_address,
        abi=abi
    )


def load_auction_contract(auction_address: str):
    try:
        w3 = connect_web3()
    except Exception as e:
        raise BackendAPIError(
            code="RPC_UNREACHABLE",
            message="Hardhat node not reachable."
        ) from e

    try:
        contract = load_contract(w3, contract_address=auction_address)
    except Exception as e:
        raise BackendAPIError(
            code="CONTRACT_LOAD_FAILED",
            message="Failed to load auction contract.",
            details=str(e)
        ) from e

    if not w3.eth.accounts:
        raise BackendAPIError(
            code="NO_UNLOCKED_ACCOUNTS",
            message="No unlocked accounts available from RPC."
        )

    account = w3.eth.accounts[0]

    return w3, contract, account