import psycopg2
import os
import bcrypt
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
        auctions = []
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM auctions")
            rows = cur.fetchall()
            for row in rows:
                auctions.append(row)
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error fetching auctions: {error}")
        return auctions
    

    def get_auction_by_id(self, auction_id):
        auction = None
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM auctions WHERE auction_id = %s", (auction_id,))
            auction = cur.fetchone()
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error fetching auction by ID: {error}")
        return auction

    def get_users(self):
        users = []
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM users")
            rows = cur.fetchall()
            for row in rows:
                users.append(row)
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error fetching users: {error}")
        return users

    def get_user_by_id(self, user_id):
        user = None
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user = cur.fetchone()
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error fetching user by ID: {error}")
        return user

    def get_bids_for_auction(self, auction_id):
        bids = []
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM bidding_history WHERE auction_id = %s", (auction_id,))
            rows = cur.fetchall()
            for row in rows:
                bids.append(row)
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error fetching bids for auction: {error}")
        return bids

    def get_highest_bid_for_auction(self, auction_id):
        highest_bid = None
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT highest_bid FROM auctions WHERE auction_id = %s", (auction_id,))
            highest_bid = cur.fetchone()[0]
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error fetching highest bid for auction: {error}")
        return highest_bid
    
    def get_starting_bid_for_auction(self, auction_id):
        starting_bid = None
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT starting_bid FROM auctions WHERE auction_id = %s", (auction_id,))
            starting_bid = cur.fetchone()[0]
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error fetching starting bid for auction: {error}")
        return starting_bid

    def submit_bid(self, auction_id, user_id, bid_amount):
        # check if bid is higher than current highest bid and higher than starting bid
        current_highest_bid = self.get_highest_bid_for_auction(auction_id)
        starting_bid = self.get_starting_bid_for_auction(auction_id)
        if current_highest_bid is None or bid_amount <= current_highest_bid:
            print(f"Bid of {bid_amount} is not higher than current highest bid of {current_highest_bid}.")
            return False
        if bid_amount <= starting_bid:
            print(f"Bid of {bid_amount} is not higher than the starting bid of {starting_bid}.")
            return False

        try:
            cur = self.conn.cursor()
            # get users wallet address
            cur.execute("SELECT wallet_address FROM users WHERE user_id = %s", (user_id,))
            wallet_address = cur.fetchone()[0]
            # insert bid into history
            cur.execute("INSERT INTO bidding_history (auction_id, user_id, bid_amount, wallet_address) VALUES (%s, %s, %s, %s)", (auction_id, user_id, bid_amount, wallet_address))
            # update highest bid
            cur.execute("UPDATE auctions SET highest_bid = %s WHERE auction_id = %s", (bid_amount, auction_id))
            self.conn.commit()
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error submitting bid: {error}")
            self.conn.rollback()
            return False
        return True
    
    def create_auction(
            self, 
            title, 
            description, 
            starting_bid, 
            image_urls, 
            created_at, 
            expires_at, 
            seller_id,
            contract_address,
            ):
        try:
            cur = self.conn.cursor()
            cur.execute("INSERT INTO auctions (title, description, starting_bid, images, created_at, expires_at, seller_id, contract_address) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (title, description, starting_bid, image_urls, created_at, expires_at, seller_id, contract_address))
            self.conn.commit()
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error creating auction: {error}")
            self.conn.rollback()
            return False
        return True
    
    def get_contract_address_by_auction_id(self, auction_id):
        contract_address = None
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT contract_address FROM auctions WHERE auction_id = %s", (auction_id,))
            row = cur.fetchone()
            if row:
                contract_address = row[0]
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error fetching contract address for auction: {error}")
        return contract_address
    
    
    def delete_auction(self, auction_id):
        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM auctions WHERE auction_id = %s", (auction_id,))
            self.conn.commit()
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error deleting auction: {error}")
            self.conn.rollback()
            return False
        return True
    
    def delete_user(self, user_id):
        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            self.conn.commit()
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error deleting user: {error}")
            self.conn.rollback()
            return False
        return True
    
    def update_auction(self, auction_id, title, description, starting_bid, image_urls):
        try:
            cur = self.conn.cursor()
            cur.execute("UPDATE auctions SET title = %s, description = %s, starting_bid = %s, images = %s WHERE auction_id = %s", (title, description, starting_bid, image_urls, auction_id))
            self.conn.commit()
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error updating auction: {error}")
            self.conn.rollback()
            return False
        return True
    
    def update_user(self, user_id, email, wallet_address):
        try:
            cur = self.conn.cursor()
            cur.execute("UPDATE users SET email = %s, wallet_address = %s WHERE user_id = %s", (email, wallet_address, user_id))
            self.conn.commit()
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error updating user: {error}")
            self.conn.rollback()
            return False
        return True
    
    def get_user_watchlist(self, user_id):
        watchlist = []
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT auction_id FROM watchlist WHERE user_id = %s", (user_id,))
            rows = cur.fetchall()
            for row in rows:
                watchlist.append(row[0])
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error fetching user watchlist: {error}")
        return watchlist
    
    def add_to_watchlist(self, user_id, auction_id):
        try:
            cur = self.conn.cursor()
            cur.execute("INSERT INTO watchlist (user_id, auction_id) VALUES (%s, %s)", (user_id, auction_id))
            self.conn.commit()
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error adding to watchlist: {error}")
            self.conn.rollback()
            return False
        return True
    def create_user(self, email, password):
        try:
            if not self.conn:
                self.connect()

            if not self.conn:
                return {"success": False, "error": "Database connection failed."}

            cur = self.conn.cursor()

            password_hash = bcrypt.hashpw(
                password.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

            query = """
                INSERT INTO users (email, password_hash)
                VALUES (%s, %s)
                RETURNING user_id;
            """

            cur.execute(query, (email, password_hash))
            user_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()

            return {"success": True, "user_id": user_id}

        except psycopg2.errors.UniqueViolation:
            if self.conn:
                self.conn.rollback()
            return {"success": False, "error": "An account with that email already exists."}

        except Exception as error:
            if self.conn:
                self.conn.rollback()
            return {"success": False, "error": str(error)}

    def get_user_by_email(self, email):
        try:
            if not self.conn:
                self.connect()

            if not self.conn:
                return None

            cur = self.conn.cursor()
            query = """
                SELECT user_id, email, password_hash
                FROM users
                WHERE email = %s;
            """
            cur.execute(query, (email,))
            user = cur.fetchone()
            cur.close()

            return user

        except Exception:
            return None
    def remove_from_watchlist(self, user_id, auction_id):
        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM watchlist WHERE user_id = %s AND auction_id = %s", (user_id, auction_id))
            self.conn.commit()
            cur.close()
        except (psycopg2.DatabaseError, Exception) as error:
            print(f"Error removing from watchlist: {error}")
            self.conn.rollback()
            return False
        return True
    
    
