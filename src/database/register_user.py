import os
import re
import sqlite3
import bcrypt


def get_db_path() -> str:
    """
    Read DB path at runtime so pytest can override it per-test using TRUST_DB_PATH.
    """
    return os.getenv("TRUST_DB_PATH", "db/trust.db")


def is_valid_email(email: str) -> bool:
    """
    Very basic email format check.
    """
    pattern = r"^[^@]+@[^@]+\.[^@]+$"
    return re.match(pattern, email) is not None


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    Returns a string so it can be stored in SQLite TEXT.
    """
    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed_bytes.decode("utf-8")


def register_user(email: str, password: str) -> str:
    """
    Registers a new user.

    Rules:
    - Email must be valid format
    - Email must be unique (UNIQUE constraint)
    - Password is stored ONLY as bcrypt hash
    """
    if not is_valid_email(email):
        return "ERROR: Invalid email format"

    db_path = get_db_path()
    conn = None

    try:
        conn = sqlite3.connect(db_path, timeout=10)
        cur = conn.cursor()

        password_hash = hash_password(password)

        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, password_hash),
        )

        conn.commit()
        return "SUCCESS: User registered"

    except sqlite3.IntegrityError:
        return "ERROR: Email already exists"

    except Exception as e:
        return f"ERROR: {e}"

    finally:
        if conn is not None:
            conn.close()