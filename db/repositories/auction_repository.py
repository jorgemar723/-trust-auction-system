# db/repositories/auction_repository.py

from db.PostgresDB import PostgresDB
from app.utils.s3_utils import delete_file_from_s3
import os


class AuctionRepository:
    def __init__(self):
        self.db = PostgresDB()

    def get_auctions(self):
        conn = self.db.get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT auction_id, seller_id, title, description, images,
                   created_at, expires_at, contract_address,
                   starting_bid, highest_bid
            FROM auctions
        """)

        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def get_auctions_by_seller_id(self, seller_id):
        conn = self.db.get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT auction_id, seller_id, title, description, images,
                   created_at, expires_at, contract_address,
                   starting_bid, highest_bid
            FROM auctions
            WHERE seller_id = %s
        """, (seller_id,))

        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def get_auction_by_id(self, auction_id):
        conn = self.db.get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT auction_id, seller_id, title, description, images,
                   created_at, expires_at, contract_address,
                   starting_bid, highest_bid
            FROM auctions
            WHERE auction_id = %s
        """, (auction_id,))

        row = cur.fetchone()
        cur.close()
        conn.close()
        return row

    def get_auction_registry(self):
        conn = self.db.get_connection()
        cur = conn.cursor()

        cur.execute("SELECT auction_id, contract_address FROM auctions")
        rows = cur.fetchall()

        cur.close()
        conn.close()

        return {row[0]: row[1] for row in rows}

    def get_contract_address_by_auction_id(self, auction_id):
        conn = self.db.get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT contract_address FROM auctions WHERE auction_id = %s",
            (auction_id,)
        )

        row = cur.fetchone()
        cur.close()
        conn.close()

        return row[0] if row else None

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
        tx_hash,
    ):
        conn = self.db.get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO auctions (
                    title,
                    description,
                    starting_bid,
                    images,
                    created_at,
                    expires_at,
                    seller_id,
                    contract_address
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                title,
                description,
                starting_bid,
                image_urls,
                created_at,
                expires_at,
                seller_id,
                contract_address,
            ))

            cur.execute(
                "SELECT auction_id FROM auctions WHERE contract_address = %s",
                (contract_address,)
            )

            auction_id = cur.fetchone()[0]

            cur.execute(
                "INSERT INTO registry (auction_id, registry_id) VALUES (%s, %s)",
                (auction_id, tx_hash)
            )

            conn.commit()
            return True

        except Exception as error:
            print(f"Error creating auction: {error}")
            conn.rollback()
            return False

        finally:
            cur.close()
            conn.close()

    def update_auction(self, auction_id, title, description, image_urls):
        conn = self.db.get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE auctions
                SET title = %s,
                    description = %s,
                    images = %s
                WHERE auction_id = %s
            """, (title, description, image_urls, auction_id))

            conn.commit()
            return True

        except Exception as error:
            print(f"Error updating auction: {error}")
            conn.rollback()
            return False

        finally:
            cur.close()
            conn.close()

    def update_contract_address(self, auction_id, contract_address):
        conn = self.db.get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE auctions
                SET contract_address = %s
                WHERE auction_id = %s
            """, (contract_address, auction_id))

            conn.commit()
            return True

        except Exception as error:
            print(f"Error updating contract address: {error}")
            conn.rollback()
            return False

        finally:
            cur.close()
            conn.close()

    def delete_auction(self, auction_id):
        conn = self.db.get_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                "SELECT images FROM auctions WHERE auction_id = %s",
                (auction_id,)
            )

            row = cur.fetchone()
            image_urls = row[0] if row and row[0] else []

            cur.execute(
                "DELETE FROM auctions WHERE auction_id = %s",
                (auction_id,)
            )

            conn.commit()

            bucket_name = os.environ.get("AWS_S3_BUCKET_NAME")

            if bucket_name and image_urls:
                for url in image_urls:
                    delete_file_from_s3(url, bucket_name)

            return True

        except Exception as error:
            print(f"Error deleting auction: {error}")
            conn.rollback()
            return False

        finally:
            cur.close()
            conn.close()