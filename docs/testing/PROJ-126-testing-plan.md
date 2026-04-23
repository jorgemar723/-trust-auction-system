# PROJ-126 Testing Plan – Backend Pricing Integration

## Overview

This testing plan focuses on validating backend auction functionality after pricing integration changes.

The goal is to ensure that:
- Backend logic remains correct and stable
- Backend is independent from pricing (USD conversion)
- Core auction behavior continues to function properly

All tests target backend orchestration methods and validate inputs, outputs, and system behavior under controlled conditions.

---

## Test 1: Auction State Retrieval (get_state)

Feature:
Auction state retrieval from blockchain

Code Under Test:
backend.mainauction.get_state(auction_id)

Inputs:
- auction_id (int)

Expected Return:
- Dictionary containing auction state data

Validation:
- Response contains "highest_bid_eth"
- Value is numeric (int or float)
- Response is not None

---

## Test 2: No USD Data in Backend

Feature:
Separation of concerns between backend and presentation layer

Code Under Test:
backend.mainauction.get_state(auction_id)

Inputs:
- auction_id (int)

Expected Return:
- Dictionary containing auction state data

Validation:
- "highest_bid_usd" is NOT present in response
- Confirms backend does not include display-layer transformations

---

## Test 3: Backend Stability Without Pricing Dependency

Feature:
Backend functionality independent of pricing services

Code Under Test:
backend.mainauction.get_state(auction_id)

Inputs:
- auction_id (int)

Expected Return:
- Dictionary containing auction state data

Validation:
- Response is not None
- Response contains "highest_bid_eth"
- Backend returns valid data even without any pricing logic

---

## Tools

- pytest (Python testing framework)
- unittest.mock (for mocking external dependencies)

---

## Alignment with PROJ-126

These tests ensure:
- Backend returns ETH-only auction data
- Backend functionality is independent of pricing APIs
- No USD-related logic exists in backend
- Core auction functionality remains stable after pricing-related changes