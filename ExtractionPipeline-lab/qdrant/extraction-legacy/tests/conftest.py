"""
Pytest configuration file for the extraction pipeline tests.
"""

import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Add the parent directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock environment variables that the application might need
os.environ.setdefault("ORIANE_ADMIN_DB_URL", "sqlite:///:memory:")


@pytest.fixture(scope="session")
def test_db_url():
    """Provide a test database URL."""
    return "sqlite:///:memory:"


@pytest.fixture
def temp_checkpoint_dir():
    """Create a temporary directory for checkpoint files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing."""
    with patch("qdrant_client.QdrantClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance
