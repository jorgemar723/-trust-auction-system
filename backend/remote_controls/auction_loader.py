from web3 import Web3
from .bidding import connect_web3, load_contract
from .errors import BackendAPIError


def load_auction_contract(auction_address: str, abi_path: str):

    try:
        w3 = connect_web3()
    except Exception as e:
        raise BackendAPIError(
            code="RPC_UNREACHABLE",
            message="Hardhat node not reachable."
        ) from e

    try:
        contract = load_contract(
            w3,
            abi_path=abi_path,
            contract_address=auction_address
        )
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