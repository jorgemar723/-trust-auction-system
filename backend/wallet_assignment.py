from web3 import Web3


def get_next_available_wallet_address(assigned_wallets):
    try:
        w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

        if not w3.is_connected():
            print("Error: Could not connect to Hardhat node.")
            return None

        hardhat_accounts = w3.eth.accounts

        for account in hardhat_accounts:
            if account not in assigned_wallets:
                return account

        print("No available Hardhat wallets.")
        return None

    except Exception as error:
        print(f"Error getting next available wallet: {error}")
        return None