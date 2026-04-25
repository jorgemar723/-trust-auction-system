# db/PostgresDB.py

import psycopg2
import os
from dotenv import load_dotenv


class PostgresDB:
    def __init__(self):
        load_dotenv()
        self.DB_URL = os.getenv("DATABASE_URL")

    def get_connection(self):
        return psycopg2.connect(self.DB_URL)