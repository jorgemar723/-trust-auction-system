# PROJ-89: Auction State Integration & Cleanup

## Purpose

This task ensures the Flask application retrieves and displays live blockchain-backed auction state using dynamic contract addresses stored in the database, instead of relying on hardcoded values or temporary in-memory mappings.

The main goal is to support the project’s multi-auction architecture, where each auction has its own deployed smart contract and the app fetches state based on the selected `auction_id`.

---

## What This Task Changed

PROJ-89 connects the auction detail page to the blockchain through the following flow:

1. A user opens an auction detail page in Flask.
2. The detail page requests `/api/state/<auction_id>`.
3. Flask calls `backend.mainauction.get_state(auction_id)`.
4. `mainauction.py` queries the database for the `contract_address` associated with that `auction_id`.
5. The backend loads the correct `SimpleAuction` contract using that address.
6. `state.py` reads live blockchain values from the contract.
7. Flask returns the state as JSON.
8. The UI updates the auction status, countdown, and timestamps using the returned blockchain data.

This replaces older approaches based on temporary registry logic and ensures auction state is resolved dynamically from the database.

---

## State Retrieval Flow

### Frontend
The auction detail page (`templates/detail.html`) fetches live auction state from:

/api/state/<auction_id>

This request happens automatically when the page loads and refreshes periodically so the countdown and auction status stay current.

### Flask Route

In flask_app.py, the route:

@app.route("/api/state/<int:auction_id>")
def api_state(auction_id):

receives the auction ID and calls the backend state controller.

### Backend Controller

In backend/mainauction.py, get_state(auction_id):
	•	opens a database connection
	•	looks up the contract_address for the given auction_id
	•	loads the deployed contract for that address
	•	calls the blockchain state reader

### Blockchain Read Layer

In backend/state.py, the contract is queried for live values such as:
	•	highest bid
	•	highest bidder
	•	current chain time
	•	auction end time
	•	open/closed status

These values are formatted and returned to Flask as a structured response.

### UI Update

In detail.html, JavaScript reads the API response and updates:
	•	auction status
	•	countdown timer
	•	readable chain time
	•	readable auction end time

---


### Files Involved

**flask_app.py**

Contains the /api/state/<auction_id> route and connects Flask to the backend state logic.

**backend/mainauction.py**

Acts as the controller layer between Flask and the blockchain helper modules.

**backend/auction_loader.py**

Loads the correct auction contract dynamically using the contract address from the database.

**backend/state.py**

Reads live state from the blockchain.

**db/PostgresDB.py**

Stores auction records and provides the database lookup:
	•	auction_id -> contract_address

**templates/detail.html**

Fetches live state from Flask and displays it on the page.

---


### How to Run the System

The system is tested locally using Flask, PostgreSQL, and a Hardhat blockchain node.

#### Terminal 1 — Flask App

From the project root:

```
source .venv/bin/activate
python flask_app.py
```
Flask runs at:

```http://127.0.0.1:8000```

#### Terminal 2 — Hardhat Node

From the Hardhat folder:

```
cd "Hardhat testing Node"
npx hardhat node
```
This starts the local blockchain at:

```http://127.0.0.1:8545```

#### Terminal 3 — Compile and Deploy Factory Contract

Still inside the Hardhat folder:

```
cd "Hardhat testing Node"
rm -rf artifacts cache
npx hardhat compile
npx hardhat run scripts/deploy_factory.js --network localhost
```

After deployment, copy the printed factory address and update _FACTORY_ADDRESS in:

```backend/factory.py```

This is currently a manual step in the local development workflow.

---
#### Terminal 4 — Optional Database Checks

From the project root:

```
source .venv/bin/activate
python
```
This can be used to inspect auction rows, users, and contract addresses during testing.

---
## How to Test PROJ-89

1. Start all services

	•	Flask app
	•	Hardhat node
	•	deployed factory contract

2. Register and log in

Create a valid user account in the Flask app.

3. Create at least two auctions

Use different durations so they produce different countdowns and end times.

4. Confirm auctions were stored

Check that each auction in the database has its own contract_address.

5. Test the API directly

Open:

```http://127.0.0.1:8000/api/state/<auction_id>```

This should return blockchain-backed state for the requested auction.

6. Test the detail pages

Open:

```http://127.0.0.1:8000/auction/<auction_id>```

The page should show:
	•	live auction status
	•	countdown timer
	•	chain time
	•	auction end time

7. Verify multi-auction behavior

Different auctions should show different:
	•	contract addresses
	•	timers
	•	statuses
	•	end times

This confirms the state is being resolved dynamically per auction instead of through a single shared contract.

---

## Expected Result

When PROJ-89 is working correctly:
	•	/api/state/<auction_id> returns live blockchain state
	•	the backend resolves state through auction_id -> contract_address
	•	auction detail pages display the correct per-auction blockchain data
	•	different auctions return different state values
	•	the state flow works through Flask, backend logic, database lookup, and blockchain reads

----

## Known Notes

	•	The local development setup currently requires manually updating the deployed factory address in backend/factory.py after redeployment.
	•	This is a local environment/deployment configuration issue and is separate from the state retrieval logic implemented in PROJ-89.
	•	Wallet/MetaMask integration is out of scope for this task.
	•	Auction creation form improvements are also out of scope for this task.

---

## Summary

PROJ-89 completes the integration needed for live, database-driven auction state retrieval in the TRUST system.

Instead of relying on a hardcoded contract or temporary in-memory auction mapping, the application now:

	•	stores each auction’s deployed contract address in the database
	•	resolves the correct contract dynamically using auction_id
	•	fetches real on-chain state from that contract
	•	displays that state in the Flask UI