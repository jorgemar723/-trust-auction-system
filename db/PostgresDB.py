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
        return

    def get_auction_by_id(self, auction_id):
        return

    def get_users(self):
        return

    def get_user_by_id(self, user_id):
        return
    
    def get_bids_for_auction(self, auction_id):
        return
    
    def submit_bid(self, auction_id, user_id, bid_amount):
        return
    
    def create_auction(self, title, description, starting_bid, image_urls):
        return
    
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