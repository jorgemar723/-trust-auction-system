from db.repository_factory import get_watchlist_repository, get_auction_repository
from app.utils.datetime_utils import format_time_remaining

class WatchlistService:
    @staticmethod
    def get_user_watchlist_formatted(user_id):
        watchlist_repo = get_watchlist_repository()
        auction_repo = get_auction_repository()
        try:
            watchlist_ids = watchlist_repo.get_user_watchlist(user_id)
            watched_items = []
            for w_id in watchlist_ids:
                row = auction_repo.get_auction_by_id(w_id)
                if row:
                    images = row[4]
                    image_url = images[0] if images and len(images) > 0 else ""
                    current_bid = row[9] if row[9] is not None else row[8]
                    watched_items.append({
                        "id": row[0],
                        "title": row[2],
                        "description": row[3],
                        "image": image_url,
                        "current_bid": float(current_bid),
                        "time_remaining": format_time_remaining(row[6])
                    })
            return watched_items
        except Exception as e:
            print(f"Error fetching user watchlist: {e}")
            return []

    @staticmethod
    def toggle_watchlist(user_id, auction_id):
        watchlist_repo = get_watchlist_repository()
        try:
            watchlist = watchlist_repo.get_user_watchlist(user_id)
            if auction_id in watchlist:
                watchlist_repo.remove_from_watchlist(user_id, auction_id)
                return {"success": True, "message": "Removed from watchlist.", "error": "", "status": "removed"}
            else:
                watchlist_repo.add_to_watchlist(user_id, auction_id)
                return {"success": True, "message": "Added to watchlist.", "error": "", "status": "added"}
        except Exception as e:
            print(f"Error toggling watchlist: {e}")
            return {"success": False, "message": "", "error": "An unexpected error occurred.", "status": "error"}
