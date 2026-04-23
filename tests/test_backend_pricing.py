import sys
import os
from unittest.mock import MagicMock, patch

# ------------------------------------------
# Step 1: Mock dependencies BEFORE import
# ------------------------------------------

sys.modules["boto3"] = MagicMock()
sys.modules["botocore"] = MagicMock()
sys.modules["botocore.exceptions"] = MagicMock()

# Mock PostgresDB BEFORE importing mainauction
mock_db = MagicMock()
mock_db.connect.return_value = None
mock_db.get_auction_registry.return_value = {}
mock_db.get_contract_address_by_auction_id.return_value = "0x123"
mock_db.close.return_value = None

sys.modules["db.PostgresDB"] = MagicMock(PostgresDB=MagicMock(return_value=mock_db))

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# NOW import
from backend import mainauction


# ------------------------------------------
# Test 1: Backend returns ETH-based state
# ------------------------------------------
@patch("backend.mainauction.get_auction_state")
@patch("backend.mainauction._load_contract")
@patch("backend.mainauction._get_contract_address")
def test_backend_returns_eth_state(mock_get_address, mock_load_contract, mock_get_auction_state):
    mock_get_address.return_value = "0x123"
    mock_load_contract.return_value = (None, None, None)

    mock_get_auction_state.return_value = {
        "highest_bid_eth": 1.2,
        "status": "OPEN"
    }

    result = mainauction.get_state(1)

    assert result["highest_bid_eth"] == 1.2
    assert result["status"] == "OPEN"


# ------------------------------------------
# Test 2: Backend does NOT include USD field
# ------------------------------------------
@patch("backend.mainauction.get_auction_state")
@patch("backend.mainauction._load_contract")
@patch("backend.mainauction._get_contract_address")
def test_backend_no_usd_field(mock_get_address, mock_load_contract, mock_get_auction_state):
    mock_get_address.return_value = "0x123"
    mock_load_contract.return_value = (None, None, None)

    mock_get_auction_state.return_value = {
        "highest_bid_eth": 2.0,
        "status": "OPEN"
    }

    result = mainauction.get_state(1)

    assert "highest_bid_usd" not in result


# ------------------------------------------
# Test 3: Backend stable without pricing
# ------------------------------------------
@patch("backend.mainauction.get_auction_state")
@patch("backend.mainauction._load_contract")
@patch("backend.mainauction._get_contract_address")
def test_backend_stable_without_pricing(mock_get_address, mock_load_contract, mock_get_auction_state):
    mock_get_address.return_value = "0x123"
    mock_load_contract.return_value = (None, None, None)

    mock_get_auction_state.return_value = {
        "highest_bid_eth": 3.0,
        "status": "OPEN"
    }

    result = mainauction.get_state(1)

    assert result is not None
    assert result["highest_bid_eth"] == 3.0