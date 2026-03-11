from postgres_config import get_connection

def test_connection():
    try:
        conn = get_connection()
        print("PostgreSQL connection successful")
        conn.close()
    except Exception as e:
        print("Connection failed:", e)

if __name__ == "__main__":
    test_connection()