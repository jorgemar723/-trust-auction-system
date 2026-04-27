import sys
import os
import pytest
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.PostgresDB import PostgresDB

def test_get_auctions():
    """Test that get_auctions successfully retrieves all auctions and formats them as a list."""
    db = PostgresDB()
    
    # Mock the database connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    db.conn = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # Mock the returned database rows
    mock_cursor.fetchall.return_value = [
        (1, 101, "Rolex Watch", "Vintage watch", ["img1.jpg"], "2024-01-01", "2024-01-10", "0x123", 500.0, 750.0),
        (2, 102, "MacBook Pro", "M3 Max", ["img2.jpg"], "2024-02-01", "2024-02-15", "0x456", 1000.0, 1050.0)
    ]
    
    results = db.get_auctions()
    
    # Verify results
    assert len(results) == 2
    assert results[0][2] == "Rolex Watch"
    assert results[1][9] == 1050.0
    mock_cursor.execute.assert_called_once()
    mock_cursor.close.assert_called_once()

def test_get_users():
    """Test that get_users accurately queries and returns a list of users."""
    db = PostgresDB()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    db.conn = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    mock_cursor.fetchall.return_value = [
        (1, "alice@example.com", "hash1", "0xabc"),
        (2, "bob@example.com", "hash2", "0xdef")
    ]
    
    results = db.get_users()
    
    assert len(results) == 2
    assert results[1][1] == "bob@example.com"
    mock_cursor.execute.assert_called_once_with("SELECT * FROM users")
    mock_cursor.close.assert_called_once()

def test_get_starting_bid_for_auction():
    """Test that get_starting_bid_for_auction extracts the starting bid field for a given auction ID."""
    db = PostgresDB()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    db.conn = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    mock_cursor.fetchone.return_value = (50.5,)
    
    result = db.get_starting_bid_for_auction(99)
    
    assert result == 50.5
    mock_cursor.execute.assert_called_once_with("SELECT starting_bid FROM auctions WHERE auction_id = %s", (99,))
    mock_cursor.close.assert_called_once()
