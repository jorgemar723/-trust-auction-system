import sqlite3

DB_PATH = "db/trust.db"

def register_user(email, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, password)
        )

        conn.commit()
        conn.close()

        return "SUCCESS: User registered"

    except sqlite3.IntegrityError:
        return "ERROR: Email already exists"

    except Exception as e:
        return f"ERROR: {e}"