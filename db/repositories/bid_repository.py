# db/repositories/bid_repository.py

from db.PostgresDB import PostgresDB


class BidRepository:
    def __init__(self):
        self.db = PostgresDB()

    def get_bids_for_auction(self, auction_id):
        conn = self.db.get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM bidding_history WHERE auction_id = %s", (auction_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    def submit_bid(self, auction_id, user_id, bid_amount):
        conn = self.db.get_connection()
        cur = conn.cursor()

        try:
            cur.execute("SELECT wallet_address FROM users WHERE user_id = %s", (user_id,))
            wallet = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO bidding_history (auction_id, user_id, bid_amount, wallet_address)
                VALUES (%s, %s, %s, %s)
            """, (auction_id, user_id, bid_amount, wallet))

            cur.execute("""
                UPDATE auctions SET highest_bid = %s WHERE auction_id = %s
            """, (bid_amount, auction_id))

            conn.commit()
            return True

        except Exception as e:
            print("Bid error:", e)
            conn.rollback()
            return False

        finally:
            cur.close()
            conn.close()