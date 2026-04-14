import requests
import time

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

_cached_price = None
_last_fetch_time = 0

CACHE_DURATION = 60  # seconds (increase to avoid rate limit)


def get_current_eth_usd_price():
    """
    Fetch current ETH → USD price from CoinGecko API with caching.

    Returns:
        float | None
    """
    global _cached_price, _last_fetch_time

    current_time = time.time()

    # Return cached value if still fresh
    if _cached_price is not None and (current_time - _last_fetch_time < CACHE_DURATION):
        return _cached_price

    params = {
        "ids": "ethereum",
        "vs_currencies": "usd"
    }

    try:
        response = requests.get(
            COINGECKO_URL,
            params=params,
            headers={"User-Agent": "Mozilla/5.0"},  # helps avoid blocking
            timeout=5
        )

        # Handle rate limit explicitly
        if response.status_code == 429:
            print("Rate limited by CoinGecko. Using cached value.")
            return _cached_price

        response.raise_for_status()

        data = response.json()

        if "ethereum" in data and "usd" in data["ethereum"]:
            _cached_price = float(data["ethereum"]["usd"])
            _last_fetch_time = current_time
            return _cached_price

        return _cached_price

    except Exception as e:
        print("Pricing API ERROR:", e)
        return _cached_price