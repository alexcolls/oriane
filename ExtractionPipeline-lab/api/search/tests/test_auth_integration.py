"""Integration tests for authentication flows with FastAPI app."""

import base64
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing the app
os.environ["API_USERNAME"] = "test_user"
os.environ["API_PASSWORD"] = "test_password"
os.environ["API_KEY"] = "test_api_key_123"

from app import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestDocsAuthentication:
    """Test authentication for API docs endpoints."""

    def test_docs_without_auth_returns_401(self, client):
        """Test that accessing /api/docs without auth returns 401."""
        response = client.get("/api/docs")
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Basic"

    def test_openapi_without_auth_returns_401(self, client):
        """Test that accessing /api/openapi.json without auth returns 401."""
        response = client.get("/api/openapi.json")
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Basic"

    def test_docs_with_correct_basic_auth_succeeds(self, client):
        """Test that accessing /api/docs with correct basic auth succeeds."""
        # Create basic auth header
        credentials = base64.b64encode(b"test_user:test_password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}

        response = client.get("/api/docs", headers=headers)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_with_correct_basic_auth_succeeds(self, client):
        """Test that accessing /api/openapi.json with correct basic auth succeeds."""
        # Create basic auth header
        credentials = base64.b64encode(b"test_user:test_password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}

        response = client.get("/api/openapi.json", headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        # Verify it's a valid OpenAPI schema
        openapi_schema = response.json()
        assert "openapi" in openapi_schema
        assert "info" in openapi_schema
        assert "paths" in openapi_schema

    def test_docs_with_wrong_basic_auth_returns_401(self, client):
        """Test that accessing /api/docs with wrong basic auth returns 401."""
        # Create basic auth header with wrong credentials
        credentials = base64.b64encode(b"wrong_user:wrong_password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}

        response = client.get("/api/docs", headers=headers)
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers


class TestApiKeyAuthentication:
    """Test API key authentication for API endpoints."""

    def test_root_endpoint_no_auth_required(self, client):
        """Test that root endpoint doesn't require authentication."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_api_endpoint_without_api_key_returns_401(self, client):
        """Test that API endpoints without X-API-Key return 401."""
        # Test search endpoint without API key
        response = client.post("/search-by/text/", json={"prompt": "test query"})
        assert response.status_code == 401

        # Verify it's an API key authentication error
        data = response.json()
        assert data["detail"] == "API key is required"

    def test_api_endpoint_with_correct_api_key_succeeds(self, client):
        """Test that API endpoints with correct X-API-Key pass authentication."""
        headers = {"X-API-Key": "test_api_key_123"}

        # Test text search endpoint - should pass auth even if it fails later
        response = client.post("/search-by/text/", json={"prompt": "test query"}, headers=headers)

        # Should not be a 401 (authentication error)
        assert response.status_code != 401

        # May be 500 (service error), 422 (validation error), or 200 (success) but not auth error
        if response.status_code == 500:
            # Expected if services are not available in test environment
            data = response.json()
            # Should not be an authentication error message
            assert "API key" not in data.get("detail", "")
            assert "authentication" not in data.get("detail", "").lower()
            # Common service errors we might see
            detail = data.get("detail", "")
            # These are acceptable service-level errors, not auth errors
            service_errors = [
                "batch_size",
                "MockSettings",
                "AttributeError",
                "model",
                "service",
                "connection",
                "embedding",
                "RPC",
                "UNAVAILABLE",
                "connect",
                "StatusCode",
                "grpc",
                "Connection refused",
                "remote host",
            ]
            assert any(error in detail for error in service_errors), f"Unexpected error: {detail}"
        elif response.status_code == 422:
            # Validation error - also acceptable, means auth passed
            data = response.json()
            assert "detail" in data
        elif response.status_code == 200:
            # Success - auth and service both worked
            data = response.json()
            assert isinstance(data, list)  # Should return list of search results

    def test_api_endpoint_with_wrong_api_key_returns_401(self, client):
        """Test that API endpoints with wrong X-API-Key return 401."""
        headers = {"X-API-Key": "wrong_api_key"}

        # Test text search endpoint with wrong API key
        response = client.post("/search-by/text/", json={"prompt": "test query"}, headers=headers)
        assert response.status_code == 401

        # Verify it's an API key authentication error
        data = response.json()
        assert data["detail"] == "Invalid API key"


class TestAuthenticationHeaders:
    """Test authentication response headers."""

    def test_401_response_includes_correct_www_authenticate_header_basic(self, client):
        """Test that 401 responses for basic auth include correct WWW-Authenticate header."""
        response = client.get("/api/docs")
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Basic"

    def test_basic_auth_realm_not_specified(self, client):
        """Test that basic auth doesn't specify a realm (as per current implementation)."""
        response = client.get("/api/docs")
        assert response.status_code == 401
        www_auth = response.headers.get("WWW-Authenticate", "")
        # Current implementation doesn't specify realm, just "Basic"
        assert www_auth == "Basic"


class TestAuthenticationErrorMessages:
    """Test authentication error messages."""

    def test_basic_auth_error_message(self, client):
        """Test basic auth error message format."""
        credentials = base64.b64encode(b"wrong:wrong").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}

        response = client.get("/api/docs", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Incorrect username or password"


# Mock test for testing with API endpoints when they're available
@pytest.mark.skip(reason="Need actual API endpoints to test with")
class TestWithActualEndpoints:
    """Tests that would run against actual API endpoints."""

    def test_add_content_endpoint_without_api_key(self, client):
        """Test add content endpoint without API key."""
        # This would test an actual endpoint like /add-content/image
        response = client.post("/add-content/image")
        assert response.status_code == 401

    def test_add_content_endpoint_with_api_key(self, client):
        """Test add content endpoint with API key."""
        headers = {"X-API-Key": "test_api_key_123"}
        # This would need actual request data
        response = client.post("/add-content/image", headers=headers)
        # Response would depend on the actual implementation
        # assert response.status_code in [200, 422]  # 422 for missing required data


class TestAdvancedApiKeyScenarios:
    """Test advanced API key authentication scenarios."""

    def test_api_key_case_sensitivity(self, client):
        """Test that API key authentication is case sensitive."""
        # Test with uppercase version of valid key
        headers = {"X-API-Key": "TEST_API_KEY_123"}
        response = client.post("/search-by/text/", json={"prompt": "test"}, headers=headers)
        assert response.status_code == 401

        data = response.json()
        assert data["detail"] == "Invalid API key"

    def test_api_key_with_whitespace(self, client):
        """Test that API key with extra whitespace fails."""
        headers = {"X-API-Key": " test_api_key_123 "}
        response = client.post("/search-by/text/", json={"prompt": "test"}, headers=headers)
        assert response.status_code == 401

        data = response.json()
        assert data["detail"] == "Invalid API key"

    def test_multiple_api_endpoints_protected(self, client):
        """Test that multiple API endpoints are protected by API key auth."""
        test_endpoints = [
            ("/search-by/text/", "POST", {"prompt": "test"}),
            ("/search-by/image/", "POST", {}),  # Would need file upload normally
        ]

        for endpoint, method, data in test_endpoints:
            if method == "POST":
                response = client.post(endpoint, json=data)
            else:
                response = client.get(endpoint)

            assert response.status_code == 401, f"Endpoint {endpoint} should require API key"

            response_data = response.json()
            assert response_data["detail"] == "API key is required"

    def test_api_key_in_different_header_formats(self, client):
        """Test that only X-API-Key header format works."""
        # Test various incorrect header names (note: HTTP headers are case-insensitive)
        wrong_headers_list = [
            {"API-Key": "test_api_key_123"},
            {"Authorization": "ApiKey test_api_key_123"},  # Bearer-style
            {"Api-Key": "test_api_key_123"},
        ]

        for headers in wrong_headers_list:
            response = client.post("/search-by/text/", json={"prompt": "test"}, headers=headers)
            assert response.status_code == 401, f"Headers {headers} should not work"

            data = response.json()
            assert data["detail"] == "API key is required"

        # Test that lowercase x-api-key also works (HTTP headers are case-insensitive)
        response = client.post(
            "/search-by/text/", json={"prompt": "test"}, headers={"x-api-key": "test_api_key_123"}
        )
        assert response.status_code != 401  # Should pass authentication


class TestCrossAuthenticationScenarios:
    """Test scenarios where different auth types might conflict or interact."""

    def test_api_endpoint_ignores_basic_auth_when_api_key_missing(self, client):
        """Test that API endpoints ignore basic auth when API key is missing."""
        # Valid basic auth but no API key
        credentials = base64.b64encode(b"test_user:test_password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}

        response = client.post("/search-by/text/", json={"prompt": "test"}, headers=headers)
        assert response.status_code == 401

        data = response.json()
        assert data["detail"] == "API key is required"

    def test_docs_endpoint_ignores_api_key_when_basic_auth_missing(self, client):
        """Test that docs endpoints ignore API key when basic auth is missing."""
        # Valid API key but no basic auth
        headers = {"X-API-Key": "test_api_key_123"}

        response = client.get("/api/docs", headers=headers)
        assert response.status_code == 401

        assert response.headers["WWW-Authenticate"] == "Basic"

    def test_both_auth_types_present_uses_appropriate_one(self, client):
        """Test behavior when both basic auth and API key are present."""
        credentials = base64.b64encode(b"test_user:test_password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}", "X-API-Key": "test_api_key_123"}

        # For docs endpoint, should use basic auth and succeed
        response = client.get("/api/docs", headers=headers)
        assert response.status_code == 200

        # For API endpoint, should use API key and pass auth (may fail later for other reasons)
        response = client.post("/search-by/text/", json={"prompt": "test"}, headers=headers)
        assert response.status_code != 401  # Should pass authentication


class TestAuthenticationErrorFormats:
    """Test the format and content of authentication error responses."""

    def test_api_key_error_response_format(self, client):
        """Test the format of API key authentication error responses."""
        response = client.post("/search-by/text/", json={"prompt": "test"})
        assert response.status_code == 401

        # Check response structure
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert data["detail"] == "API key is required"

        # Check content type
        assert response.headers["content-type"] == "application/json"

    def test_basic_auth_error_response_format(self, client):
        """Test the format of basic auth error responses."""
        response = client.get("/api/docs")
        assert response.status_code == 401

        # Check response structure
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

        # Check headers
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Basic"
        assert response.headers["content-type"] == "application/json"


class TestDebugAndUtilityEndpoints:
    """Test debug and utility endpoints that may have different auth requirements."""

    def test_root_endpoint_accessibility(self, client):
        """Test that root endpoint is accessible without authentication."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "message" in data

    def test_debug_settings_endpoint_accessibility(self, client):
        """Test debug settings endpoint accessibility."""
        response = client.get("/debug/settings")
        # This endpoint doesn't require auth in the current implementation
        assert response.status_code == 200

        data = response.json()
        assert "api_username" in data
        assert "api_name" in data
        # Sensitive values should be masked
        assert data["api_password"] == "***"
        assert data["api_key"] == "***"


# Test for environment variable configuration
class TestEnvironmentConfiguration:
    """Test that authentication works with environment variables."""

    def test_auth_uses_environment_variables(self, client):
        """Test that authentication uses values from environment variables."""
        # The fixture already sets environment variables
        # Test that they're being used correctly

        # Test basic auth with env vars
        credentials = base64.b64encode(b"test_user:test_password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}

        response = client.get("/api/docs", headers=headers)
        assert response.status_code == 200

        # Test with wrong credentials
        wrong_credentials = base64.b64encode(b"wrong:wrong").decode("utf-8")
        headers = {"Authorization": f"Basic {wrong_credentials}"}

        response = client.get("/api/docs", headers=headers)
        assert response.status_code == 401

    def test_api_key_from_environment(self, client):
        """Test that API key authentication uses environment variable."""
        # Test with correct API key from environment
        headers = {"X-API-Key": "test_api_key_123"}
        response = client.post("/search-by/text/", json={"prompt": "test"}, headers=headers)
        assert response.status_code != 401  # Should pass authentication

        # Test with wrong API key
        headers = {"X-API-Key": "wrong_key"}
        response = client.post("/search-by/text/", json={"prompt": "test"}, headers=headers)
        assert response.status_code == 401
