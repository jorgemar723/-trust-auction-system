import pathlib
import sqlite3

import pytest


def apply_schema(db_path: str):
    """
    Creates all tables in a fresh SQLite DB by executing db/schema.sql
    """
    schema_file = pathlib.Path("db/schema.sql")
    assert schema_file.exists(), "db/schema.sql not found. Make sure it exists and is committed."

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript(schema_file.read_text())

    conn.commit()
    conn.close()


def get_user_row(db_path: str, email: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT email, password_hash FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return row


@pytest.fixture()
def temp_db(tmp_path, monkeypatch):
    """
    Makes a temporary DB for each test and tells register_user.py to use it.
    Prevents tests from touching your real db/trust.db and avoids locking issues.
    """
    db_path = str(tmp_path / "test_trust.db")
    apply_schema(db_path)

    # IMPORTANT: register_user.py reads TRUST_DB_PATH to know what DB to use
    monkeypatch.setenv("TRUST_DB_PATH", db_path)

    return db_path


def test_register_success(temp_db):
    from src.database.register_user import register_user

    msg = register_user("valid@email.com", "Password123!")
    assert "SUCCESS" in msg

    row = get_user_row(temp_db, "valid@email.com")
    assert row is not None
    assert row[0] == "valid@email.com"


def test_reject_invalid_email(temp_db):
    from src.database.register_user import register_user

    msg = register_user("not_an_email", "Password123!")
    assert "Invalid email format" in msg

    row = get_user_row(temp_db, "not_an_email")
    assert row is None


def test_reject_duplicate_email(temp_db):
    from src.database.register_user import register_user

    msg1 = register_user("dup@email.com", "Password123!")
    assert "SUCCESS" in msg1

    msg2 = register_user("dup@email.com", "DifferentPassword!")
    assert ("already" in msg2.lower()) or ("exists" in msg2.lower())


def test_password_is_hashed_not_plaintext(temp_db):
    from src.database.register_user import register_user

    email = "hashcheck@email.com"
    plaintext = "MyPlainPassword!"

    msg = register_user(email, plaintext)
    assert "SUCCESS" in msg

    row = get_user_row(temp_db, email)
    assert row is not None

    stored_hash = row[1]
    assert stored_hash is not None
    assert stored_hash != plaintext  # must NOT store plaintext
    assert stored_hash.startswith("$2")  # bcrypt hashes usually start with $2...