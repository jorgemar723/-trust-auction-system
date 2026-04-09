# PROJ-122: ETH → USD API Integration

## Selected API

CoinGecko public API

Endpoint:
https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd

## Reason for Selection

- No API key required
- Lightweight and fast
- Simple JSON response
- Suitable for retrieving current ETH price only

## Expected Response

{
  "ethereum": {
    "usd": 3482.17
  }
}

## Integration Plan

A new pricing service module will be created:

src/services/pricing_service.py

This module will:
- Send a GET request to the API
- Parse the ETH → USD value
- Return the price for backend use

## Architecture Alignment

- Pricing logic is separate from blockchain logic
- No changes to smart contracts
- Will be reused in later tasks (PROJ-124, PROJ-125)

## Scope Constraints

- No historical pricing
- No multi-currency support
- No frontend changes