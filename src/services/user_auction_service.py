from db.repository_factory import get_auction_repository
from app.utils.datetime_utils import format_time_remaining

class UserAuctionService:
    @staticmethod
    def get_user_auctions_formatted(user_id):
        auction_repo = get_auction_repository()
        try:
            raw_auctions = auction_repo.get_auctions_by_seller_id(user_id)
            formatted_auctions = []
            for row in raw_auctions:
                images = row[4]
                image_url = images[0] if images and len(images) > 0 else ""
                current_bid = row[9] if row[9] is not None else row[8]

                formatted_auctions.append({
                    "id": row[0],
                    "title": row[2],
                    "description": row[3],
                    "image": image_url,
                    "current_bid": float(current_bid),
                    "time_remaining": format_time_remaining(row[6])
                })
            return formatted_auctions
        except Exception as e:
            print(f"Error fetching user auctions: {e}")
            return []