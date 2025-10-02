"""Test API key authentication on actual API endpoints."""

import base64
import io
import os

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# Set test environment variables before importing the app
os.environ["API_USERNAME"] = "test_user"
os.environ["API_PASSWORD"] = "test_password"
os.environ["API_KEY"] = "test_api_key_123"

from app import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_image_bytes():
    """Create a sample image for testing."""
    # Create a simple RGB image
    image = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    return img_bytes.getvalue()


class TestAPIKeyAuthenticationOnEndpoints:
    """Test API key authentication on actual API endpoints."""

    def test_add_image_without_api_key_returns_401(self, client, sample_image_bytes):
        """Test that add-content/image endpoint without X-API-Key returns 401."""
        files = {"file": ("test.jpg", sample_image_bytes, "image/jpeg")}

        response = client.post("/add-content/image/test_user", files=files)
        assert response.status_code == 401

        # Should be an API key authentication error, not basic auth
        error_data = response.json()
        assert "API key" in error_data["detail"] or "ApiKey" in response.headers.get(
            "WWW-Authenticate", ""
        )

    def test_add_image_with_wrong_api_key_returns_401(self, client, sample_image_bytes):
        """Test that add-content/image endpoint with wrong X-API-Key returns 401."""
        headers = {"X-API-Key": "wrong_api_key"}
        files = {"file": ("test.jpg", sample_image_bytes, "image/jpeg")}

        response = client.post("/add-content/image/test_user", files=files, headers=headers)
        assert response.status_code == 401

        error_data = response.json()
        assert error_data["detail"] == "Invalid API key"

    def test_add_image_with_correct_api_key_processes_request(self, client, sample_image_bytes):
        """Test that add-content/image endpoint with correct X-API-Key processes the request."""
        headers = {"X-API-Key": "test_api_key_123"}
        files = {"file": ("test.jpg", sample_image_bytes, "image/jpeg")}

        # This might fail due to missing services, but it should pass authentication
        response = client.post("/add-content/image/test_user", files=files, headers=headers)

        # Should not be a 401 (authentication error)
        assert response.status_code != 401

        # Might be 500 (service error) or 422 (validation error) but not auth error
        if response.status_code == 500:
            # This is expected if embeddings_service or qdrant_service are not available
            error_data = response.json()
            assert "API key" not in error_data["detail"]  # Should not be an auth error
        elif response.status_code == 201:
            # If services are available, should succeed
            data = response.json()
            assert "image_id" in data
            assert data["status"] == "stored"

    def test_search_endpoint_without_api_key_returns_401(self, client):
        """Test that search endpoints without X-API-Key return 401."""
        # Test text search endpoint
        response = client.post("/search-by/text", json={"query": "test query"})
        assert response.status_code == 401

    def test_search_endpoint_with_api_key_processes_request(self, client):
        """Test that search endpoints with correct X-API-Key process the request."""
        headers = {"X-API-Key": "test_api_key_123"}

        # Test text search endpoint
        response = client.post("/search-by/text", json={"query": "test query"}, headers=headers)

        # Should not be a 401 (authentication error)
        assert response.status_code != 401

    def test_batch_upload_without_api_key_returns_401(self, client, sample_image_bytes):
        """Test that batch upload endpoint without X-API-Key returns 401."""
        files = [
            ("files", ("test1.jpg", sample_image_bytes, "image/jpeg")),
            ("files", ("test2.jpg", sample_image_bytes, "image/jpeg")),
        ]

        response = client.post("/add-content/image/batch/test_user", files=files)
        assert response.status_code == 401

    def test_video_endpoint_without_api_key_returns_401(self, client):
        """Test that video endpoints without X-API-Key return 401."""
        # Create a dummy video file (just bytes for this test)
        video_bytes = b"fake video content"
        files = {"file": ("test.mp4", video_bytes, "video/mp4")}

        response = client.post("/add-content/video/test_user", files=files)
        assert response.status_code == 401


class TestMixedAuthentication:
    """Test mixing different authentication types."""

    def test_api_endpoint_with_basic_auth_instead_of_api_key_fails(
        self, client, sample_image_bytes
    ):
        """Test that API endpoints fail when basic auth is used instead of API key."""
        # Create basic auth header
        credentials = base64.b64encode(b"test_user:test_password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        files = {"file": ("test.jpg", sample_image_bytes, "image/jpeg")}

        response = client.post("/add-content/image/test_user", files=files, headers=headers)
        assert response.status_code == 401

        # Should be an API key error, not basic auth success
        error_data = response.json()
        assert error_data["detail"] == "API key is required"

    def test_docs_endpoint_with_api_key_instead_of_basic_auth_fails(self, client):
        """Test that docs endpoints fail when API key is used instead of basic auth."""
        headers = {"X-API-Key": "test_api_key_123"}

        response = client.get("/api/docs", headers=headers)
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Basic"


class TestEdgeCases:
    """Test edge cases in authentication."""

    def test_empty_api_key_header_returns_401(self, client, sample_image_bytes):
        """Test that empty X-API-Key header returns 401."""
        headers = {"X-API-Key": ""}
        files = {"file": ("test.jpg", sample_image_bytes, "image/jpeg")}

        response = client.post("/add-content/image/test_user", files=files, headers=headers)
        assert response.status_code == 401

        error_data = response.json()
        # Empty string is treated as None by FastAPI, so we get "API key is required"
        assert error_data["detail"] == "API key is required"

    def test_api_key_with_extra_whitespace_fails(self, client, sample_image_bytes):
        """Test that API key with extra whitespace fails."""
        headers = {"X-API-Key": " test_api_key_123 "}  # Extra spaces
        files = {"file": ("test.jpg", sample_image_bytes, "image/jpeg")}

        response = client.post("/add-content/image/test_user", files=files, headers=headers)
        assert response.status_code == 401

        error_data = response.json()
        assert error_data["detail"] == "Invalid API key"

    def test_case_sensitive_api_key(self, client, sample_image_bytes):
        """Test that API key is case sensitive."""
        headers = {"X-API-Key": "TEST_API_KEY_123"}  # Wrong case
        files = {"file": ("test.jpg", sample_image_bytes, "image/jpeg")}

        response = client.post("/add-content/image/test_user", files=files, headers=headers)
        assert response.status_code == 401

        error_data = response.json()
        assert error_data["detail"] == "Invalid API key"

    def test_multiple_auth_headers_use_correct_one(self, client):
        """Test behavior when both auth types are provided."""
        # Provide both basic auth and API key - API endpoints should use API key
        credentials = base64.b64encode(b"test_user:test_password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}", "X-API-Key": "test_api_key_123"}

        # For API endpoints, should use API key and succeed (past auth)
        sample_image_bytes = Image.new("RGB", (100, 100), color="red")
        img_bytes = io.BytesIO()
        sample_image_bytes.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        files = {"file": ("test.jpg", img_bytes.getvalue(), "image/jpeg")}
        response = client.post("/add-content/image/test_user", files=files, headers=headers)

        # Should not be 401 (auth should pass)
        assert response.status_code != 401
