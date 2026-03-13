import psycopg2
import os
from dotenv import load_dotenv

class PostgresDB:
    def __init__(self):
        load_dotenv()
        self.DB_URL = os.getenv("DATABASE_URL")
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(self.DB_URL)
            print("Connection successful!")
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error connecting to the database: {error}")

    def close(self):
        if self.conn:
            self.conn.close()
            print("Connection closed.")

    def get_auctions(self):
        return

    def get_auction_by_id(self, auction_id):
        return

    def get_users(self):
        return

    def get_user_by_id(self, user_id):
        return
    
    def get_bids_for_auction(self, auction_id):
        return
    
    def get_highest_bid_for_auction(self, auction_id):
        return

    def submit_bid(self, auction_id, user_id, bid_amount):
        return
    
    def create_auction(self, title, description, starting_bid, image_urls):
        return
    
    def create_user(self, username, email, wallet_address):
        return
    
    def delete_auction(self, auction_id):
        return
    
    def delete_user(self, user_id):
        return
    
    def update_auction(self, auction_id, title, description, starting_bid, image_urls):
        return
    
    def update_user(self, user_id, username, email, wallet_address):
        return
    
    def get_user_watchlist(self, user_id):
        return
    
    def add_to_watchlist(self, user_id, auction_id):
        return
    
    def remove_from_watchlist(self, user_id, auction_id):
        return
    
    
