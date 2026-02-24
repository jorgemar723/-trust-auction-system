import sqlite3
import re

DB_PATH = "db/trust.db"

# Basic email pattern: something@something.domain
EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"


def is_valid_email(email: str) -> bool:
    """
    Returns True if email looks like a normal email address.
    Examples accepted: test@gmail.com, a.b+1@txstate.edu
    Examples rejected: 'test', 'test@', 'test@gmail'
    """
    if email is None:
        return False
    email = email.strip()
    return re.match(EMAIL_REGEX, email) is not None


def email_exists(email: str) -> bool:
    """
    Returns True if the email is already registered in the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE email = ? LIMIT 1", (email.strip(),))
    row = cur.fetchone()
    conn.close()
    return row is not None


def register_user(email, password):
    """
    Registers a new user if:
      1) email format is valid
      2) email is not already registered

    Returns clear success/error messages.
    """

    # 1) Validate format
    if not is_valid_email(email):
        return "ERROR: Invalid email format"

    # 2) Check duplicate BEFORE insert (clear message)
    if email_exists(email):
        return "ERROR: Email already registered"

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email.strip(), password)
        )

        conn.commit()
        conn.close()

        return "SUCCESS: User registered"

    except sqlite3.IntegrityError:
        # Backup protection in case of race condition
        return "ERROR: Email already registered"

    except Exception as e:
        return f"ERROR: {e}"