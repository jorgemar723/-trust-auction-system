import psycopg2
import os
from dotenv import load_dotenv

# ===========================================================
# This script initializes the database schema. 
# Whenever we make changes to the schema.sql file, 
# run this script to apply those changes to the database.
# ===========================================================

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def run_sql_schema(file_path):
    try:
        # Read the schema file
        with open(file_path, 'r') as f:
            schema_sql = f.read()

        # Connect to Neon
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Execute it
        cur.execute(schema_sql)
        
        conn.commit()
        print("Schema initialized successfully")

    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    run_sql_schema("db/schema.sql")