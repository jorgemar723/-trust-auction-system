import requests

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"


def get_current_eth_usd_price():
    """
    Fetch current ETH → USD price from CoinGecko API.
    Returns:
        float | None: ETH price in USD, or None if request fails
    """
    params = {
            "ids": "ethereum",
            "vs_currencies": "usd"
    }
    
    try:

        response = requests.get(COINGECKO_URL, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()
        
        # Validate response structure
        if "ethereum" in data and "usd" in data["ethereum"]:
            return float(data["ethereum"]["usd"])
        return None

    except (requests.RequestException, KeyError, ValueError):
        # Return None to allow fallback in later tasks
        return None