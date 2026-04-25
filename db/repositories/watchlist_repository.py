# db/repositories/watchlist_repository.py

from db.PostgresDB import PostgresDB


class WatchlistRepository:
    def __init__(self):
        self.db = PostgresDB()

    def get_user_watchlist(self, user_id):
        conn = self.db.get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT auction_id FROM watchlist WHERE user_id = %s",
            (user_id,)
        )

        rows = cur.fetchall()

        cur.close()
        conn.close()

        return [row[0] for row in rows]

    def add_to_watchlist(self, user_id, auction_id):
        conn = self.db.get_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO watchlist (user_id, auction_id) VALUES (%s, %s)",
                (user_id, auction_id)
            )

            conn.commit()
            return True

        except Exception as error:
            print(f"Error adding to watchlist: {error}")
            conn.rollback()
            return False

        finally:
            cur.close()
            conn.close()

    def remove_from_watchlist(self, user_id, auction_id):
        conn = self.db.get_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                "DELETE FROM watchlist WHERE user_id = %s AND auction_id = %s",
                (user_id, auction_id)
            )

            conn.commit()
            return True

        except Exception as error:
            print(f"Error removing from watchlist: {error}")
            conn.rollback()
            return False

        finally:
            cur.close()
            conn.close()