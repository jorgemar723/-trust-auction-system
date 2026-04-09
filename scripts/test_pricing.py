import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.pricing_service import get_current_eth_usd_price

if __name__ == "__main__":
    price = get_current_eth_usd_price()
    
    if price is not None:
        print(f"Current ETH price (USD): {price}")
    else:
        print("Failed to fetch ETH price")