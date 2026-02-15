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


## Features
- [User interface] Python application provides a command-line or simple web interface for users to interact with the system. 
	- User Story: As a **Bidder**, I want a **clear and responsive interface** so that I can easily view the current highest bid and submit my own without writing raw code.
- [Etherium VM] Blockchain-based auction system running on a local Hardhat network
	- As a **Developer**, I want to run the auction on a **local Hardhat network** so that I can test transactions instantly and for free before deploying to a mainnet.
- [Smart Contract] A Solidity smart contract that enforces the auction rules, such as requiring higher bids and respecting time limits
	- As an **Auction Participant**, I want the **Solidity contract to automatically enforce rules** so that the process is fair and I don't have to trust a third party.
- [AI Fraud Detection] An AI analytics engine that flags suspicious bidding patterns
	- As a **Seller**, I want the AI analytics engine to **flag suspicious bidding patterns** so that I can avoid "shill bidding" or bot manipulation on my items.
- [Real Time UI Updates] Real time bidding updates shown to user in python UI
	- As a **Bidder**, I want the Python-based UI to **provide real-time updates** from the SQL database so that I never miss a bid due to lag or synchronization issues.
- [Auction State Transparency] Smart contract getter function and Python display logic for retrieving auction information by ID
	- As a **Bidder**, I want to **retrieve the full state of an auction** so that I can make informed bidding decisions.
- [Multi-Auction Support] Unique auction ID system enabling simultaneous independent auctions without data conflicts
	- As a **Seller**, I want to **create and manage multiple auctions simultaneously** so that I can list and sell more than one item at a time without conflicts between auctions.


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
Project is: _in progress_ / _complete_ / _no longer being worked on_. If you are no longer working on it, provide reasons why.


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