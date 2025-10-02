"""Tests for get-embeddings endpoint."""

import os
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing the app
os.environ["API_USERNAME"] = "test_user"
os.environ["API_PASSWORD"] = "test_password"
os.environ["API_KEY"] = "test_api_key_123"

from app import app
from controllers.get_embeddings.embeddings import ALLOWED_COLLECTIONS

client = TestClient(app)


class TestGetEmbeddings:
    """Test suite for get embeddings endpoint."""

    def setup_method(self):
        """Setup for each test method."""
        self.api_key = "test_api_key_123"
        self.headers = {"X-API-Key": self.api_key}
        self.valid_request = {
            "collection_name": "user_images",
            "embedding_id": "test-embedding-123",
        }

    @patch("controllers.get_embeddings.embeddings.qdrant_service._client")
    @patch("auth.apikey.verify_api_key")
    def test_get_embeddings_success(self, mock_verify_api_key, mock_client):
        """Test successful embedding retrieval."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock Qdrant client response
        mock_point = Mock()
        mock_point.vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_point.payload = {"user_id": "test-user", "image_id": "img-123"}

        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.retrieve.return_value = [mock_point]

        # Make request
        response = client.post("/get-embeddings/", json=self.valid_request, headers=self.headers)

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["embedding_id"] == "test-embedding-123"
        assert data["collection_name"] == "user_images"
        assert data["vector"] == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert data["payload"] == {"user_id": "test-user", "image_id": "img-123"}

        # Verify Qdrant was called correctly
        mock_client_instance.retrieve.assert_called_once_with(
            collection_name="user_images",
            ids=["test-embedding-123"],
            with_payload=True,
            with_vectors=True,
        )

    @patch("controllers.get_embeddings.embeddings.qdrant_service._client")
    @patch("auth.apikey.verify_api_key")
    def test_get_embeddings_not_found(self, mock_verify_api_key, mock_client):
        """Test when embedding is not found."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock Qdrant client response - empty list
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.retrieve.return_value = []

        # Make request
        response = client.post("/get-embeddings/", json=self.valid_request, headers=self.headers)

        # Verify 404 response
        assert response.status_code == 404
        data = response.json()
        assert "No embedding found with ID test-embedding-123" in data["detail"]
        assert "user_images" in data["detail"]

    @patch("controllers.get_embeddings.embeddings.qdrant_service._client")
    @patch("auth.apikey.verify_api_key")
    def test_get_embeddings_no_vector(self, mock_verify_api_key, mock_client):
        """Test when point exists but has no vector."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock Qdrant client response - point without vector
        mock_point = Mock()
        mock_point.vector = None
        mock_point.payload = {"user_id": "test-user"}

        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.retrieve.return_value = [mock_point]

        # Make request
        response = client.post("/get-embeddings/", json=self.valid_request, headers=self.headers)

        # Verify 404 response
        assert response.status_code == 404
        data = response.json()
        assert "No vector found for embedding ID test-embedding-123" in data["detail"]

    @patch("auth.apikey.verify_api_key")
    def test_get_embeddings_invalid_collection(self, mock_verify_api_key):
        """Test with invalid collection name."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        invalid_request = {
            "collection_name": "invalid_collection",
            "embedding_id": "test-embedding-123",
        }

        # Make request
        response = client.post("/get-embeddings/", json=invalid_request, headers=self.headers)

        # Verify 400 response
        assert response.status_code == 400
        data = response.json()
        assert "Invalid collection name" in data["detail"]
        assert "user_images, user_videos, watched_frames" in data["detail"]

    @patch("auth.apikey.verify_api_key")
    def test_get_embeddings_empty_embedding_id(self, mock_verify_api_key):
        """Test with empty embedding ID."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        invalid_request = {
            "collection_name": "user_images",
            "embedding_id": "   ",  # Empty/whitespace string
        }

        # Make request
        response = client.post("/get-embeddings/", json=invalid_request, headers=self.headers)

        # Verify 400 response
        assert response.status_code == 400
        data = response.json()
        assert "Embedding ID must be a non-empty string" in data["detail"]

    @patch("controllers.get_embeddings.embeddings.qdrant_service._client")
    @patch("auth.apikey.verify_api_key")
    def test_get_embeddings_qdrant_error(self, mock_verify_api_key, mock_client):
        """Test when Qdrant returns an error."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock Qdrant client to raise exception
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.retrieve.side_effect = Exception("Qdrant connection failed")

        # Make request
        response = client.post("/get-embeddings/", json=self.valid_request, headers=self.headers)

        # Verify 500 response
        assert response.status_code == 500
        data = response.json()
        assert "Failed to retrieve embeddings" in data["detail"]

    def test_get_embeddings_no_api_key(self):
        """Test that API key is required."""
        # Make request without API key
        response = client.post("/get-embeddings/", json=self.valid_request)

        # Verify 401 response
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "API key is required"

    def test_get_embeddings_invalid_api_key(self):
        """Test with invalid API key."""
        invalid_headers = {"X-API-Key": "wrong_key"}

        # Make request with invalid API key
        response = client.post("/get-embeddings/", json=self.valid_request, headers=invalid_headers)

        # Verify 401 response
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid API key"

    @patch("controllers.get_embeddings.embeddings.qdrant_service._client")
    @patch("auth.apikey.verify_api_key")
    def test_get_embeddings_all_valid_collections(self, mock_verify_api_key, mock_client):
        """Test that all allowed collections work."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock Qdrant client response
        mock_point = Mock()
        mock_point.vector = [0.1, 0.2, 0.3]
        mock_point.payload = {"test": "data"}

        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.retrieve.return_value = [mock_point]

        # Test each allowed collection
        for collection in ALLOWED_COLLECTIONS:
            request_data = {"collection_name": collection, "embedding_id": "test-id"}

            response = client.post("/get-embeddings/", json=request_data, headers=self.headers)

            assert response.status_code == 200
            data = response.json()
            assert data["collection_name"] == collection

    @patch("controllers.get_embeddings.embeddings.qdrant_service._client")
    @patch("auth.apikey.verify_api_key")
    def test_get_embeddings_empty_payload(self, mock_verify_api_key, mock_client):
        """Test when point has empty payload."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock Qdrant client response with empty payload
        mock_point = Mock()
        mock_point.vector = [0.1, 0.2, 0.3]
        mock_point.payload = None

        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.retrieve.return_value = [mock_point]

        # Make request
        response = client.post("/get-embeddings/", json=self.valid_request, headers=self.headers)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["payload"] == {}  # Should default to empty dict

    def test_get_embeddings_missing_fields(self):
        """Test with missing required fields."""
        # Test missing collection_name
        incomplete_request = {"embedding_id": "test-id"}

        response = client.post("/get-embeddings/", json=incomplete_request, headers=self.headers)

        assert response.status_code == 422  # Pydantic validation error

        # Test missing embedding_id
        incomplete_request = {"collection_name": "user_images"}

        response = client.post("/get-embeddings/", json=incomplete_request, headers=self.headers)

        assert response.status_code == 422  # Pydantic validation error
