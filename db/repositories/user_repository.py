# db/repositories/user_repository.py

import bcrypt
import psycopg2

from db.PostgresDB import PostgresDB
from backend.wallet_assignment import get_next_available_wallet_address


class UserRepository:
    def __init__(self):
        self.db = PostgresDB()

    def get_users(self):
        conn = self.db.get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users")
        users = cur.fetchall()

        cur.close()
        conn.close()
        return users

    def get_user_by_id(self, user_id):
        conn = self.db.get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()

        cur.close()
        conn.close()
        return user

    def get_user_by_email(self, email):
        conn = self.db.get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT user_id, email, password_hash
                FROM users
                WHERE email = %s
            """, (email,))

            return cur.fetchone()

        except Exception as error:
            print(f"Error fetching user by email: {error}")
            return None

        finally:
            cur.close()
            conn.close()

    def get_wallet_address_by_user_id(self, user_id):
        conn = self.db.get_connection()
        cur = conn.cursor()

        cur.execute("SELECT wallet_address FROM users WHERE user_id = %s", (user_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row[0] if row else None

    def get_assigned_wallet_addresses(self):
        conn = self.db.get_connection()
        cur = conn.cursor()

        cur.execute("SELECT wallet_address FROM users WHERE wallet_address IS NOT NULL")
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return [row[0] for row in rows]

    def create_user(self, email, password):
        conn = self.db.get_connection()
        cur = conn.cursor()

        try:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

            cur.execute("""
                INSERT INTO users (email, password_hash)
                VALUES (%s, %s)
                RETURNING user_id
            """, (email, password_hash))

            user_id = cur.fetchone()[0]

            cur.execute("SELECT wallet_address FROM users WHERE wallet_address IS NOT NULL")
            assigned_wallets = [row[0] for row in cur.fetchall()]

            wallet_address = get_next_available_wallet_address(assigned_wallets)

            if not wallet_address:
                conn.rollback()
                return {
                    "success": False,
                    "error": "No test wallets are currently available."
                }

            cur.execute(
                "UPDATE users SET wallet_address = %s WHERE user_id = %s",
                (wallet_address, user_id)
            )

            conn.commit()

            return {
                "success": True,
                "user_id": user_id,
                "wallet_address": wallet_address
            }

        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return {
                "success": False,
                "error": "An account with that email already exists."
            }

        except Exception as error:
            conn.rollback()
            return {
                "success": False,
                "error": str(error)
            }

        finally:
            cur.close()
            conn.close()

    def update_user(self, user_id, email, wallet_address):
        conn = self.db.get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE users
                SET email = %s, wallet_address = %s
                WHERE user_id = %s
            """, (email, wallet_address, user_id))

            conn.commit()
            return True

        except Exception as error:
            print(f"Error updating user: {error}")
            conn.rollback()
            return False

        finally:
            cur.close()
            conn.close()

    def delete_user(self, user_id):
        conn = self.db.get_connection()
        cur = conn.cursor()

        try:
            cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            conn.commit()
            return True

        except Exception as error:
            print(f"Error deleting user: {error}")
            conn.rollback()
            return False

        finally:
            cur.close()
            conn.close()