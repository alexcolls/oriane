"""Unit tests for authentication functions."""

# Mock settings for testing
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials


class MockSettings:
    api_username = "test_user"
    api_password = "test_password"
    api_key = "test_api_key_123"
    batch_size = 8
    dim = 512  # Vector dimension for embeddings
    reports_dir = Path(".output/reports")

    def __init__(self):
        # Ensure the reports_dir exists for the profiler
        self.reports_dir.mkdir(parents=True, exist_ok=True)


# Replace the real settings with our mock for testing
import sys

sys.modules["config.env_config"] = type(sys)("config.env_config")
sys.modules["config.env_config"].settings = MockSettings()

from auth.apikey import verify_api_key

# Now import the auth functions
from auth.basic import verify_credentials


class TestVerifyCredentials:
    """Test cases for verify_credentials function."""

    def test_verify_credentials_success(self):
        """Test successful credential verification."""
        credentials = HTTPBasicCredentials(username="test_user", password="test_password")

        result = verify_credentials(credentials)
        assert result == "test_user"

    def test_verify_credentials_wrong_username(self):
        """Test credential verification with wrong username."""
        credentials = HTTPBasicCredentials(username="wrong_user", password="test_password")

        with pytest.raises(HTTPException) as exc_info:
            verify_credentials(credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Incorrect username or password"
        assert exc_info.value.headers == {"WWW-Authenticate": "Basic"}

    def test_verify_credentials_wrong_password(self):
        """Test credential verification with wrong password."""
        credentials = HTTPBasicCredentials(username="test_user", password="wrong_password")

        with pytest.raises(HTTPException) as exc_info:
            verify_credentials(credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Incorrect username or password"
        assert exc_info.value.headers == {"WWW-Authenticate": "Basic"}

    def test_verify_credentials_wrong_both(self):
        """Test credential verification with wrong username and password."""
        credentials = HTTPBasicCredentials(username="wrong_user", password="wrong_password")

        with pytest.raises(HTTPException) as exc_info:
            verify_credentials(credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Incorrect username or password"
        assert exc_info.value.headers == {"WWW-Authenticate": "Basic"}


class TestVerifyApiKey:
    """Test cases for verify_api_key function."""

    def test_verify_api_key_success(self):
        """Test successful API key verification."""
        result = verify_api_key("test_api_key_123")
        assert result == "test_api_key_123"

    def test_verify_api_key_wrong_key(self):
        """Test API key verification with wrong key."""
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key("wrong_api_key")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid API key"
        assert exc_info.value.headers == {"WWW-Authenticate": "ApiKey"}

    def test_verify_api_key_missing_key(self):
        """Test API key verification with missing key."""
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(None)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "API key is required"
        assert exc_info.value.headers == {"WWW-Authenticate": "ApiKey"}

    def test_verify_api_key_empty_key(self):
        """Test API key verification with empty key."""
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key("")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid API key"
        assert exc_info.value.headers == {"WWW-Authenticate": "ApiKey"}
