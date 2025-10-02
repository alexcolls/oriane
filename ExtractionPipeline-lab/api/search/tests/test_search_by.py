"""Tests for search-by endpoints (text and image)."""

import io
import os
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# Set test environment variables before importing the app
os.environ["API_USERNAME"] = "test_user"
os.environ["API_PASSWORD"] = "test_password"
os.environ["API_KEY"] = "test_api_key_123"

from app import app

client = TestClient(app)


class TestSearchByText:
    """Test suite for search by text endpoint."""

    def setup_method(self):
        """Setup for each test method."""
        self.api_key = "test_api_key_123"
        self.headers = {"X-API-Key": self.api_key}
        self.valid_request = {"prompt": "a beautiful sunset over the ocean", "limit": 5}

    @patch("controllers.search_by.text.qdrant_service.search")
    @patch("controllers.search_by.text.embeddings_service.get_text_embedding")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_text_success(self, mock_verify_api_key, mock_get_embedding, mock_search):
        """Test successful text search."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock embedding generation
        mock_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_get_embedding.return_value = mock_embedding

        # Mock search results
        mock_hit1 = Mock()
        mock_hit1.id = "result-1"
        mock_hit1.score = 0.95
        mock_hit1.payload = {"video_id": "video-123", "frame_number": 10}

        mock_hit2 = Mock()
        mock_hit2.id = "result-2"
        mock_hit2.score = 0.88
        mock_hit2.payload = {"video_id": "video-456", "frame_number": 25}

        mock_search.return_value = [mock_hit1, mock_hit2]

        # Make request
        response = client.post("/search-by/text/", json=self.valid_request, headers=self.headers)

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        assert data[0]["id"] == "result-1"
        assert data[0]["score"] == 0.95
        assert data[0]["payload"]["video_id"] == "video-123"
        assert data[1]["id"] == "result-2"
        assert data[1]["score"] == 0.88

        # Verify service calls
        mock_get_embedding.assert_called_once_with("a beautiful sunset over the ocean")
        mock_search.assert_called_once_with(vector=mock_embedding, limit=5)

    @patch("auth.apikey.verify_api_key")
    def test_search_by_text_empty_prompt(self, mock_verify_api_key):
        """Test search with empty prompt."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        invalid_request = {"prompt": "   ", "limit": 5}  # Empty/whitespace

        # Make request
        response = client.post("/search-by/text/", json=invalid_request, headers=self.headers)

        # Verify 400 response
        assert response.status_code == 400
        data = response.json()
        assert "Prompt must not be empty" in data["detail"]

    @patch("controllers.search_by.text.qdrant_service.search")
    @patch("controllers.search_by.text.embeddings_service.get_text_embedding")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_text_default_limit(
        self, mock_verify_api_key, mock_get_embedding, mock_search
    ):
        """Test search with default limit."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock embedding and search
        mock_get_embedding.return_value = [0.1, 0.2, 0.3]
        mock_search.return_value = []

        # Request without explicit limit
        request_no_limit = {"prompt": "test query"}

        # Make request
        response = client.post("/search-by/text/", json=request_no_limit, headers=self.headers)

        # Verify response
        assert response.status_code == 200

        # Verify default limit was used
        mock_search.assert_called_once_with(vector=[0.1, 0.2, 0.3], limit=5)

    @patch("controllers.search_by.text.embeddings_service.get_text_embedding")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_text_embedding_error(self, mock_verify_api_key, mock_get_embedding):
        """Test when embedding generation fails."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock embedding service to raise exception
        mock_get_embedding.side_effect = Exception("Embedding model failed")

        # Make request - this will raise exception since controller doesn't handle it
        with pytest.raises(Exception) as exc_info:
            response = client.post(
                "/search-by/text/", json=self.valid_request, headers=self.headers
            )

        # Verify the exception message
        assert "Embedding model failed" in str(exc_info.value)

    @patch("controllers.search_by.text.qdrant_service.search")
    @patch("controllers.search_by.text.embeddings_service.get_text_embedding")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_text_search_error(
        self, mock_verify_api_key, mock_get_embedding, mock_search
    ):
        """Test when Qdrant search fails."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock embedding generation
        mock_get_embedding.return_value = [0.1, 0.2, 0.3]

        # Mock search to raise exception
        mock_search.side_effect = Exception("Qdrant search failed")

        # Make request
        response = client.post("/search-by/text/", json=self.valid_request, headers=self.headers)

        # Verify 500 response
        assert response.status_code == 500
        data = response.json()
        assert "Qdrant search failed" in data["detail"]

    @patch("controllers.search_by.text.qdrant_service.search")
    @patch("controllers.search_by.text.embeddings_service.get_text_embedding")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_text_empty_results(
        self, mock_verify_api_key, mock_get_embedding, mock_search
    ):
        """Test search with no results."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock embedding generation
        mock_get_embedding.return_value = [0.1, 0.2, 0.3]

        # Mock empty search results
        mock_search.return_value = []

        # Make request
        response = client.post("/search-by/text/", json=self.valid_request, headers=self.headers)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_search_by_text_no_api_key(self):
        """Test that API key is required."""
        # Make request without API key
        response = client.post("/search-by/text/", json=self.valid_request)

        # Verify 401 response
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "API key is required"


class TestSearchByImage:
    """Test suite for search by image endpoint."""

    def setup_method(self):
        """Setup for each test method."""
        self.api_key = "test_api_key_123"
        self.headers = {"X-API-Key": self.api_key}

        # Create test image in memory
        self.test_image = Image.new("RGB", (100, 100), color="red")
        self.test_image_bytes = io.BytesIO()
        self.test_image.save(self.test_image_bytes, format="PNG")
        self.test_image_bytes.seek(0)

    @patch("controllers.search_by.image.qdrant_service.search")
    @patch("controllers.search_by.image.embeddings_service.get_image_embedding")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_image_success(self, mock_verify_api_key, mock_get_embedding, mock_search):
        """Test successful image search."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock embedding generation
        mock_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_get_embedding.return_value = mock_embedding

        # Mock search results
        mock_hit = Mock()
        mock_hit.id = "result-1"
        mock_hit.score = 0.92
        mock_hit.payload = {"video_id": "video-789", "frame_number": 15}

        mock_search.return_value = [mock_hit]

        # Prepare file
        image_bytes = io.BytesIO()
        self.test_image.save(image_bytes, format="PNG")
        image_bytes.seek(0)

        # Make request
        response = client.post(
            "/search-by/image/",
            files={"file": ("test.png", image_bytes, "image/png")},
            params={"limit": 5},
            headers=self.headers,
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["id"] == "result-1"
        assert data[0]["score"] == 0.92
        assert data[0]["payload"]["video_id"] == "video-789"

        # Verify service calls
        mock_get_embedding.assert_called_once()
        mock_search.assert_called_once_with(vector=mock_embedding, limit=5)

    @patch("auth.apikey.verify_api_key")
    def test_search_by_image_invalid_file_type(self, mock_verify_api_key):
        """Test with non-image file."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Create text file
        text_file = io.BytesIO(b"This is not an image")

        # Make request
        response = client.post(
            "/search-by/image/",
            files={"file": ("test.txt", text_file, "text/plain")},
            headers=self.headers,
        )

        # Verify 400 response
        assert response.status_code == 400
        data = response.json()
        assert "File must be an image" in data["detail"]

    @patch("auth.apikey.verify_api_key")
    def test_search_by_image_empty_file(self, mock_verify_api_key):
        """Test with empty file."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Create empty file
        empty_file = io.BytesIO(b"")

        # Make request
        response = client.post(
            "/search-by/image/",
            files={"file": ("empty.png", empty_file, "image/png")},
            headers=self.headers,
        )

        # Verify 400 response
        assert response.status_code == 400
        data = response.json()
        assert "Empty image file" in data["detail"]

    @patch("auth.apikey.verify_api_key")
    def test_search_by_image_corrupted_file(self, mock_verify_api_key):
        """Test with corrupted image file."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Create corrupted image bytes
        corrupted_file = io.BytesIO(b"corrupted image data")

        # Make request
        response = client.post(
            "/search-by/image/",
            files={"file": ("corrupted.png", corrupted_file, "image/png")},
            headers=self.headers,
        )

        # Verify 400 response
        assert response.status_code == 400
        data = response.json()
        assert "Invalid image file" in data["detail"]

    @patch("controllers.search_by.image.qdrant_service.search")
    @patch("controllers.search_by.image.embeddings_service.get_image_embedding")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_image_default_limit(
        self, mock_verify_api_key, mock_get_embedding, mock_search
    ):
        """Test search with default limit."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock embedding and search
        mock_get_embedding.return_value = [0.1, 0.2, 0.3]
        mock_search.return_value = []

        # Prepare file
        image_bytes = io.BytesIO()
        self.test_image.save(image_bytes, format="PNG")
        image_bytes.seek(0)

        # Make request without limit parameter
        response = client.post(
            "/search-by/image/",
            files={"file": ("test.png", image_bytes, "image/png")},
            headers=self.headers,
        )

        # Verify response
        assert response.status_code == 200

        # Verify default limit was used
        mock_search.assert_called_once_with(vector=[0.1, 0.2, 0.3], limit=5)

    @patch("controllers.search_by.image.qdrant_service.search")
    @patch("controllers.search_by.image.embeddings_service.get_image_embedding")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_image_rgb_conversion(
        self, mock_verify_api_key, mock_get_embedding, mock_search
    ):
        """Test that images are converted to RGB."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock embedding and search
        mock_get_embedding.return_value = [0.1, 0.2, 0.3]
        mock_search.return_value = []

        # Create RGBA image
        rgba_image = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        image_bytes = io.BytesIO()
        rgba_image.save(image_bytes, format="PNG")
        image_bytes.seek(0)

        # Make request
        response = client.post(
            "/search-by/image/",
            files={"file": ("test.png", image_bytes, "image/png")},
            headers=self.headers,
        )

        # Verify response
        assert response.status_code == 200

        # Verify embedding service was called (meaning RGB conversion worked)
        mock_get_embedding.assert_called_once()
        # The call argument should be an RGB image
        called_image = mock_get_embedding.call_args[0][0]
        assert called_image.mode == "RGB"

    @patch("controllers.search_by.image.embeddings_service.get_image_embedding")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_image_embedding_error(self, mock_verify_api_key, mock_get_embedding):
        """Test when embedding generation fails."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock embedding service to raise exception
        mock_get_embedding.side_effect = Exception("Embedding model failed")

        # Prepare file
        image_bytes = io.BytesIO()
        self.test_image.save(image_bytes, format="PNG")
        image_bytes.seek(0)

        # Make request
        response = client.post(
            "/search-by/image/",
            files={"file": ("test.png", image_bytes, "image/png")},
            headers=self.headers,
        )

        # Verify 500 response
        assert response.status_code == 500
        data = response.json()
        assert "Failed to generate image embedding" in data["detail"]

    @patch("controllers.search_by.image.qdrant_service.search")
    @patch("controllers.search_by.image.embeddings_service.get_image_embedding")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_image_search_error(
        self, mock_verify_api_key, mock_get_embedding, mock_search
    ):
        """Test when Qdrant search fails."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock embedding generation
        mock_get_embedding.return_value = [0.1, 0.2, 0.3]

        # Mock search to raise exception
        mock_search.side_effect = Exception("Qdrant search failed")

        # Prepare file
        image_bytes = io.BytesIO()
        self.test_image.save(image_bytes, format="PNG")
        image_bytes.seek(0)

        # Make request
        response = client.post(
            "/search-by/image/",
            files={"file": ("test.png", image_bytes, "image/png")},
            headers=self.headers,
        )

        # Verify 500 response
        assert response.status_code == 500
        data = response.json()
        assert "Search failed" in data["detail"]

    def test_search_by_image_no_api_key(self):
        """Test that API key is required."""
        # Prepare file
        image_bytes = io.BytesIO()
        self.test_image.save(image_bytes, format="PNG")
        image_bytes.seek(0)

        # Make request without API key
        response = client.post(
            "/search-by/image/", files={"file": ("test.png", image_bytes, "image/png")}
        )

        # Verify 401 response
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "API key is required"

    @patch("controllers.search_by.image.qdrant_service.search")
    @patch("controllers.search_by.image.embeddings_service.get_image_embedding")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_image_custom_limit(
        self, mock_verify_api_key, mock_get_embedding, mock_search
    ):
        """Test search with custom limit."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock embedding and search
        mock_get_embedding.return_value = [0.1, 0.2, 0.3]
        mock_search.return_value = []

        # Prepare file
        image_bytes = io.BytesIO()
        self.test_image.save(image_bytes, format="PNG")
        image_bytes.seek(0)

        # Make request with custom limit
        response = client.post(
            "/search-by/image/",
            files={"file": ("test.png", image_bytes, "image/png")},
            params={"limit": 10},
            headers=self.headers,
        )

        # Verify response
        assert response.status_code == 200

        # Verify custom limit was used
        mock_search.assert_called_once_with(vector=[0.1, 0.2, 0.3], limit=10)
