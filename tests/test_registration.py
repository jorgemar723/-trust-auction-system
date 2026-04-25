import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()
TEST_DB_URL = os.getenv("DATABASE_URL")


def init_test_db():
    with open(PROJECT_ROOT / "db" / "schema.sql", "r") as f:
        schema = f.read()

    conn = psycopg2.connect(TEST_DB_URL)
    cur = conn.cursor()
    cur.execute(schema)
    conn.commit()
    cur.close()
    conn.close()


@pytest.fixture(autouse=True)
def setup_db():
    init_test_db()
    yield


@patch("db.repositories.user_repository.get_next_available_wallet_address")
def test_create_user_success(mock_wallet):
    from db.repositories.user_repository import UserRepository

    mock_wallet.return_value = "0x0000000000000000000000000000000000000001"

    user_repo = UserRepository()
    result = user_repo.create_user("test@example.com", "password123")

    assert result["success"] is True
    assert "user_id" in result
    assert result["wallet_address"] == "0x0000000000000000000000000000000000000001"


@patch("db.repositories.user_repository.get_next_available_wallet_address")
def test_create_user_duplicate_email_fails(mock_wallet):
    from db.repositories.user_repository import UserRepository

    mock_wallet.return_value = "0x0000000000000000000000000000000000000001"

    user_repo = UserRepository()

    first_result = user_repo.create_user("duplicate@example.com", "password123")
    second_result = user_repo.create_user("duplicate@example.com", "password456")

    assert first_result["success"] is True
    assert second_result["success"] is False
    assert "already exists" in second_result["error"]


@patch("db.repositories.user_repository.get_next_available_wallet_address")
def test_get_user_by_email_returns_created_user(mock_wallet):
    from db.repositories.user_repository import UserRepository

    mock_wallet.return_value = "0x0000000000000000000000000000000000000001"

    user_repo = UserRepository()

    create_result = user_repo.create_user("lookup@example.com", "password123")
    user = user_repo.get_user_by_email("lookup@example.com")

    assert create_result["success"] is True
    assert user is not None
    assert user[1] == "lookup@example.com"