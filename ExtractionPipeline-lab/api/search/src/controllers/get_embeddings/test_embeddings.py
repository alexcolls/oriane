from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from .embeddings import ALLOWED_COLLECTIONS, router

# Create a test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


@patch("controllers.get_embeddings.embeddings.qdrant_service._client")
def test_happy_path(mock_client):
    """Test successful retrieval of embeddings."""
    mock_client_instance = mock_client.return_value
    mock_point = MagicMock()
    mock_point.vector = [0.1, 0.2]
    mock_point.payload = {"key": "value"}
    mock_client_instance.retrieve.return_value = [mock_point]

    response = client.post("/", json={"collection_name": "user_images", "embedding_id": "test_id"})

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["embedding_id"] == "test_id"
    assert response_data["collection_name"] == "user_images"
    assert response_data["vector"] == [0.1, 0.2]
    assert response_data["payload"] == {"key": "value"}


@patch("controllers.get_embeddings.embeddings.qdrant_service._client")
def test_embedding_not_found(mock_client):
    """Test 404 response when embedding is not found."""
    mock_client_instance = mock_client.return_value
    mock_client_instance.retrieve.return_value = []

    response = client.post(
        "/", json={"collection_name": "user_images", "embedding_id": "non_existent_id"}
    )

    assert response.status_code == 404
    assert (
        "No embedding found with ID non_existent_id in collection user_images"
        in response.json()["detail"]
    )


def test_invalid_collection():
    """Test 400 response for invalid collection name."""
    response = client.post(
        "/", json={"collection_name": "invalid_collection", "embedding_id": "test_id"}
    )

    assert response.status_code == 400
    assert "Invalid collection name" in response.json()["detail"]


def test_empty_embedding_id():
    """Test 400 response for empty embedding_id."""
    response = client.post("/", json={"collection_name": "user_images", "embedding_id": ""})

    assert response.status_code == 400
    assert "Embedding ID must be a non-empty string" in response.json()["detail"]


def test_whitespace_only_embedding_id():
    """Test 400 response for whitespace-only embedding_id."""
    response = client.post("/", json={"collection_name": "user_images", "embedding_id": "   "})

    assert response.status_code == 400
    assert "Embedding ID must be a non-empty string" in response.json()["detail"]


@patch("controllers.get_embeddings.embeddings.qdrant_service._client")
def test_qdrant_exception(mock_client):
    """Test 500 response when Qdrant throws an exception."""
    mock_client_instance = mock_client.return_value
    mock_client_instance.retrieve.side_effect = Exception("Qdrant connection failed")

    response = client.post("/", json={"collection_name": "user_images", "embedding_id": "test_id"})

    assert response.status_code == 500
    assert "Failed to retrieve embeddings" in response.json()["detail"]
