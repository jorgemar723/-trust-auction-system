# PROJ-64: Local Wallet & Contract Verification

## Purpose
Ensure the local Hardhat blockchain environment is consistent and usable by verifying contract deployment, wallet assignment, and multi-user interactions after startup.

## Setup
Run the application using:

```python start_app.py```

This will:
- Start the Hardhat local node
- Deploy the AuctionFactory contract
- Reset and initialize the database
- Launch the Flask application

## Wallet Assignment
- Upon user registration, a Hardhat test wallet is automatically assigned
- Wallets are selected from available accounts provided by Hardhat
- Each user receives a unique wallet address
- No manual database updates are required

## Verification Steps
1. Start the app using `start_app.py`
2. Register User A → wallet is auto-assigned
3. Register User B → different wallet is auto-assigned
4. Log in as User A → create an auction
5. Log in as User B → place a bid

## Expected Results
- Contracts deploy successfully
- Users receive valid Hardhat wallet addresses
- Wallets are unique per user
- Auction creation succeeds
- Bidding succeeds across different users
- No manual intervention required after startup

## Outcome
The local environment is now fully reproducible and demo-ready.  
Running a single startup script initializes all components and enables multi-user blockchain interaction.

