from sqlalchemy import create_engine

DB_USER = "kristianparra"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "trust_db"

DATABASE_URL = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

def get_connection():
    return engine.connect()