from db.repository_factory import get_auction_repository, get_bid_repository, get_watchlist_repository, get_user_repository
from src.services.pricing_service import get_current_eth_usd_price
from app.utils.datetime_utils import format_time_remaining
from backend.mainauction import get_state, submit_bid as mainauction_submit_bid
from backend.remote_controls.wallet import get_wallet_balance

class AuctionService:
    @staticmethod
    def get_all_auctions_formatted():
        auction_repo = get_auction_repository()
        formatted_auctions = []
        try:
            raw_auctions = auction_repo.get_auctions()
            try:
                eth_price = get_current_eth_usd_price()
            except Exception as e:
                print(f"Error fetching ETH price: {e}")
                eth_price = None

            for row in raw_auctions:
                images = row[4]
                image_url = images[0] if images and len(images) > 0 else ""
                current_bid = row[9] if row[9] is not None else row[8]
                current_bid_usd = None
                if eth_price is not None:
                    current_bid_usd = round(float(current_bid) * float(eth_price), 2)

                formatted_auctions.append({
                    "id": row[0],
                    "title": row[2],
                    "description": row[3],
                    "image": image_url,
                    "current_bid": float(current_bid),
                    "current_bid_usd": current_bid_usd,
                    "time_remaining": format_time_remaining(row[6])
                })
            return formatted_auctions
        except Exception as e:
            print(f"Error fetching auctions: {e}")
            return []

    @staticmethod
    def get_auction_state_with_usd(auction_id):
        state = get_state(auction_id)
        try:
            eth_price = get_current_eth_usd_price()
        except Exception as e:
            print(f"Error fetching ETH price: {e}")
            eth_price = None

        highest_bid_eth = state.get("highest_bid_eth")
        if eth_price is not None and highest_bid_eth is not None:
            highest_bid_usd = highest_bid_eth * eth_price

        state["highest_bid_usd"] = highest_bid_usd
        return state

    @staticmethod
    def get_auction_details(auction_id, user_id=None):
        auction_repo = get_auction_repository()
        bid_repo = get_bid_repository()
        watchlist_repo = get_watchlist_repository()
        try:
            raw_auction = auction_repo.get_auction_by_id(auction_id)
            if not raw_auction:
                return None

            seller_id = raw_auction[1]
            is_seller = user_id == seller_id if user_id else False

            images = raw_auction[4]
            current_bid = raw_auction[9] if raw_auction[9] is not None else raw_auction[8]
            
            try:
                eth_price = get_current_eth_usd_price()
            except Exception as e:
                print(f"Error fetching ETH price: {e}")
                eth_price = None

            current_bid_usd = round(float(current_bid) * float(eth_price), 2) if eth_price is not None else None

            auction = {
                "id": raw_auction[0],
                "title": raw_auction[2],
                "description": raw_auction[3],
                "images": images if images else [],
                "image": images[0] if images and len(images) > 0 else "",
                "current_bid": float(current_bid),
                "current_bid_usd": current_bid_usd
            }

            raw_bids = bid_repo.get_bids_for_auction(auction_id)
            history = []
            for bid in raw_bids:
                history.append({
                    "user": (bid[6][:10] + "...") if bid[6] else f"User {bid[2]}",
                    "amount": f"{float(bid[3])} ETH",
                    "time": bid[5].strftime("%Y-%m-%d %H:%M") if bid[5] else "Unknown",
                    "status": "Verified" if bid[4] else "Pending"
                })

            is_watched = False
            if user_id:
                watchlist = watchlist_repo.get_user_watchlist(user_id)
                is_watched = auction_id in watchlist

            return {
                "auction": auction,
                "history": history,
                "is_seller": is_seller,
                "is_watched": is_watched
            }
        except Exception as e:
            print(f"Error fetching auction details: {e}")
            return None

    @staticmethod
    def place_bid(auction_id, bidder_id, new_bid):
        auction_repo = get_auction_repository()
        user_repo = get_user_repository()
        bid_repo = get_bid_repository()
        try:
            raw_auction = auction_repo.get_auction_by_id(auction_id)
            if not raw_auction:
                return {"success": False, "message": "", "error": "Auction not found."}
            
            current_bid = raw_auction[9] if raw_auction[9] is not None else raw_auction[8]
            
            wallet_address = user_repo.get_wallet_address_by_user_id(bidder_id)
            if not wallet_address:
                return {"success": False, "message": "", "error": "You must have a test wallet assigned before placing a bid."}
            
            balance = get_wallet_balance(bidder_id)
            balance_eth = balance.get("eth") if balance else None
            
            if new_bid <= float(current_bid):
                return {"success": False, "message": "", "error": f"Bid must be higher than {float(current_bid)} ETH."}
            
            if balance_eth is not None and new_bid > float(balance_eth):
                return {"success": False, "message": "", "error": f"You only have {round(float(balance_eth), 4)} ETH available."}

            
            mainauction_submit_bid(auction_id, new_bid, wallet_address)
            success = bid_repo.submit_bid(auction_id, bidder_id, new_bid)

            if success:
                return {"success": True, "message": f"Success! Your bid of {new_bid} ETH has been placed.", "error": ""}
            else:
                return {"success": False, "message": "", "error": "Bid reached blockchain but failed to save in the database."}

        except Exception as e:
            print(f"Error placing bid: {e}")
            return {"success": False, "message": "", "error": "An unexpected error occurred while placing your bid."}
