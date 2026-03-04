# TRUST — Transparent Register for Unbiased Sales & Trades
> Online auction house that uses blockchain to regulate rules and payment, AI analytics, built using Python, C++, SQL, and Solidity. We are developing this for security-minded individuals, as an alternative to auction houses that don't offer comprehensive fraud protection and security. This project will impact users by offering a safe place to shop and auction their personal items. Built by Nathan Carlson, Jorge Martinez-Lopez, Joseph Krabe, Kristian Parra, and Robert Krause.
> Live demo [_here_](https://www.example.com). <!-- If you have the project hosted somewhere, include the link here. -->

## Table of Contents
* [General Info](#general-information)
* [Technologies Used](#technologies-used)
* [Features](#features)
* [Screenshots](#screenshots)
* [Setup](#setup)
* [Usage](#usage)
* [Project Status](#project-status)
* [Room for Improvement](#room-for-improvement)
* [Acknowledgements](#acknowledgements)
* [Contact](#contact)
<!-- * [License](#license) -->


## General Information

- What problem does this application solve?
	- Reduced fraud and increased security when compared to alternatives (like ebay)
- Why did you undertake it?
	- We wanted to explore blockchain-based system design and demonstrate how smart contracts can increase trust in digital marketplaces
<!-- You don't have to answer all the questions - just the ones relevant to your project. -->


## Technologies Used
- Python → main app logic, API/server, UI/CLI
- Solidity → smart contract for auction rules (remix IDE)
- C++ → analytics, bid processing, hashing
- SQL → Database
- JSON/JSON RPC → data format for communication


# Features

## Sprint 1

### Contributions

Jorge: “designed initial auction contract structure and implemented blockchain integration layer with structured backend error handling”

- Jira Task: Auction State Design (initial multi-auction architecture groundwork, architectural groundwork for next sprint)
	- PROJ-36 [Bitbucket](https://bitbucket.org/cs3398-bith-s26/trust/src/a44a2c7c1cfb36409e09086acf594c58e20fddc5/?at=Tasks%2FPROJ-36-auction-state-design)

- Jira Task: Auction Controller Integration Planning (architectural groundwork for next sprint)
	- PROJ-37, [Bitbucket](https://bitbucket.org/cs3398-bith-s26/trust/src/91e8af3c4d478af2b2f1bf94d7be3752af8a5c0d/?at=Tasks%2FPROJ-37-implement-solidity-getter-for-au)

- Jira Task: Flask to Smart Contract Integration
	- PROJ-38, [Bitbucket](https://bitbucket.org/cs3398-bith-s26/trust/src/d8ed5e963daf9e4c95d9a929763ca81311262a19/?at=feature%2FPROJ-38-update-python-client-json-rpc)

- Jira Task: Structured Backend Error Handling
	- PROJ-39, [Bitbucket](https://bitbucket.org/cs3398-bith-s26/trust/src/03e84149e38c17482358bb7d64f31036a41f5300/?at=feature%2FPROJ-39-backend-error-handling)

Kristian Parra: "Implemented user registration functionality including database schema, password hashing, email validation, and unit testing."

Jira Task: PROJ-49 – Design user database structure
- Bitbucket: (https://bitbucket.org/cs3398-bith-s26/trust/commits/branch/PROJ-49-user-database-structure

Jira Task: PROJ-50 – Implement user registration function
- Bitbucket: (https://bitbucket.org/cs3398-bith-s26/trust/commits/branch/PROJ-50-user-registration)

Jira Task: PROJ-51 – Validate email input
- Bitbucket: (https://bitbucket.org/cs3398-bith-s26/trust/commits/branch/PROJ-51-validate-email-input)

Jira Task: PROJ-52 – Implement password hashing
- Bitbucket: (https://bitbucket.org/cs3398-bith-s26/trust/commits/branch/feature%2FPROJ-52-password-hashing)

Jira Task: PROJ-53 – Write unit tests for registration
- Bitbucket: (https://bitbucket.org/cs3398-bith-s26/trust/commits/branch/feature%2FPROJ-53-write-unit-tests-for-registration)
Robert Krause : "Created Hard local blockhain node, Created in chain auction logic, created remotes to interact with contract live on the blockchain from python layer"
Jira task: PROJ-5 Set up local Hardhat node
Bitbucket: https://bitbucket.org/cs3398-bith-s26/trust/commits/843606e2b5b2703a6e505369f4c67feb97162de6 
Jira task: PROJ-6 Create base Solidity contract
Bitbucket: https://bitbucket.org/cs3398-bith-s26/trust/commits/9a3b941f96afc07ffc9fa440e0674346301fb8cc
Jira task: PROJ-7 Design Auction data structure
Bitbucket- https://bitbucket.org/cs3398-bith-s26/trust/commits/9a3b941f96afc07ffc9fa440e0674346301fb8cc
Jira task: PROJ-63 Export ABI for Pythonh
Bitbucket: https://bitbucket.org/cs3398-bith-s26/trust/commits/5c78482f52bd5d161ec3e4988968ec94924f70a0
Jira task: PROJ-61 Create bidding.py
Bitbucket-https://bitbucket.org/cs3398-bith-s26/trust/commits/5c78482f52bd5d161ec3e4988968ec94924f70a0
Jira task: PROJ-69 Create state.py
Bitbucket- https://bitbucket.org/cs3398-bith-s26/trust/commits/3460b36afa493b661a9caf395a47da5ec76ea0e6
Report

Nathan: “Created local flask-powered web app that allows users to interact with active auctions”

- Jira Task: Foundational Architecture & Layout
	- [PROJ-71](https://cs3398-bith-s26new.atlassian.net/browse/PROJ-71)
	- [Bitbucket](https://bitbucket.org/cs3398-bith-s26/trust/branch/feature/PROJ-71-foundational-architecture-layout)

- Jira Task: Advanced Auction Gallery & Card Components
	- [PROJ-72](https://cs3398-bith-s26new.atlassian.net/browse/PROJ-72)
	- [Bitbucket](https://bitbucket.org/cs3398-bith-s26/trust/branch/feature/PROJ-72-advanced-auction-gallery-card-components)

- Jira Task: Auction Detail Page & Bidding Interface
	- [PROJ-73](https://cs3398-bith-s26new.atlassian.net/browse/PROJ-73)
	- [Bitbucket](https://bitbucket.org/cs3398-bith-s26/trust/branch/feature/PROJ-73-auction-detail-page-bidding-inte)



- [User interface] Python application provides a command-line or simple web interface for users to interact with the system. 
	- User Story: As a **Bidder**, I want a **clear and responsive interface** so that I can easily view the current highest bid and submit my own without writing raw code.
- [Etherium VM] Blockchain-based auction system running on a local Hardhat network
	- As a **Developer**, I want to run the auction on a **local Hardhat network** so that I can test transactions instantly and for free before deploying to a testnet
-• [Testnet Integration] Deploy and run auctions on a public Ethereum testnet (e.g., Sepolia) using real wallets and testnet ETH
◦ 	User Story: As a Bidder, I want to interact with auctions on a public Ethereum testnet using a realcrypto wallet so that I can 			experience a realistic decentralized auction without risking real money.
- [Smart Contract] A Solidity smart contract that enforces the auction rules, such as requiring higher bids and respecting time limits
	- As an **Auction Participant**, I want the **Solidity contract to automatically enforce rules** so that the process is fair and I don't have to trust a third party.
- [AI Fraud Detection] An AI analytics engine that flags suspicious bidding patterns
	- As a **Seller**, I want the AI analytics engine to **flag suspicious bidding patterns** so that I can avoid "shill bidding" or bot manipulation on my items.
- [Flask web app] Web app that allows users to browse auctions
	- **As a buyer**, I want to **browse a clean, professional web gallery** of active auctions.
- [User Registration] System allows new users to create an account to participate in auctions.  
	- User Story: As a **new user**, I would like to **create an account** so that I can securely participate in auctions on the TRUST platform.
- [View Auction Details] System displays detailed information about a selected auction.  
	- User Story: As a **user**, I would like to **view the details of an auction** so that I can understand what item is being sold before placing a bid.


# Next Steps

#### Jorge

- Refactor smart contract to support multiple simultaneous auctions
- Implement bid submission endpoint connecting Flask to on-chain placeBid
- Add integration tests validating full blockchain transaction flow

#### Kristian Parra
- Connect backend registration system to Jorge’s frontend interface
- Test full user registration flow from UI to database
- Fix any integration bugs between frontend and backend

#### Nathan Carlson
- Finish UI pages and polish
- Implement auction db
- Connect auction db to flask app
- Test database connections

## Screenshots
![Example screenshot](./img/Trust logo with shield and checkmark.png)
<!-- If you have screenshots you'd like to share, include them here. -->


## Setup
What are the project requirements/dependencies? Where are they listed? A requirements.txt or a Pipfile.lock file perhaps? Where is it located?

Proceed to describe how to install / setup one's local environment / get started with the project.


## Usage
How does one go about using it?
Provide various use cases and code examples here.

`write-your-code-here`


## Project Status
Project is: In Progress

## Room for Improvement
Include areas you believe need improvement / could be improved. Also add TODOs for future development.

Room for improvement:
- Improvement to be done 1
- Improvement to be done 2

To do:
- Feature to be added 1
- Feature to be added 2


## Acknowledgements
Give credit here.
- This project was inspired by...
- This project was based on [this tutorial](https://www.example.com).
- Many thanks to...


## Contact
Created by [@flynerdpl](https://www.flynerd.pl/) - feel free to contact me!


<!-- Optional -->
<!-- ## License -->
<!-- This project is open source and available under the [... License](). -->

<!-- You don't have to include all sections - just the one's relevant to your project -->