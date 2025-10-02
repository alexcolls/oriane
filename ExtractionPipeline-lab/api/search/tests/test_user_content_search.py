import os
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing the app
os.environ["API_USERNAME"] = "test_user"
os.environ["API_PASSWORD"] = "test_password"
os.environ["API_KEY"] = "test_api_key_123"

from app import app
from controllers.search_by_user_content.image import UserImageSearchRequest
from controllers.search_by_user_content.video import UserVideoSearchRequest

# Test client
client = TestClient(app)


class TestUserContentSearch:
    """Test user content search endpoints."""

    def setup_method(self):
        """Setup for each test method."""
        self.api_key = "test_api_key_123"  # Match the environment variable
        self.headers = {"X-API-Key": self.api_key}
        self.user_id = "test-user-123"
        self.image_id = "test-image-456"
        self.video_id = "test-video-789"

    @patch("controllers.search_by_user_content.image.qdrant_service.fetch_embedding")
    @patch("controllers.search_by_user_content.image.qdrant_service.search")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_user_image_success(
        self, mock_verify_api_key, mock_search, mock_fetch_embedding
    ):
        """Test successful image search."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock embedding fetch
        mock_embedding = [0.1, 0.2, 0.3]
        mock_payload = {"user_id": self.user_id, "image_id": self.image_id}
        mock_fetch_embedding.return_value = (mock_embedding, mock_payload)

        # Mock search results
        mock_hit = Mock()
        mock_hit.id = "result-123"
        mock_hit.score = 0.95
        mock_hit.payload = {"video_id": "matched-video", "frame_number": 5}
        mock_search.return_value = [mock_hit]

        # Make request
        response = client.post(
            "/search-by-user-content/user-image",
            json={"user_id": self.user_id, "image_id": self.image_id, "limit": 5},
            headers=self.headers,
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "result-123"
        assert data[0]["score"] == 0.95
        assert data[0]["payload"]["video_id"] == "matched-video"

        # Verify service calls
        mock_fetch_embedding.assert_called_once_with(
            collection="user_images", user_id=self.user_id, entry_id=self.image_id
        )
        mock_search.assert_called_once_with(
            vector=mock_embedding, limit=5, collection="watched_frames"
        )

    @patch("controllers.search_by_user_content.video.qdrant_service.fetch_all_video_embeddings")
    @patch("controllers.search_by_user_content.video.qdrant_service.search")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_user_video_success(
        self, mock_verify_api_key, mock_search, mock_fetch_all_embeddings
    ):
        """Test successful video search."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock video embeddings fetch
        frame1_embedding = [0.1, 0.2, 0.3]
        frame2_embedding = [0.4, 0.5, 0.6]
        frame1_metadata = {"frame_number": 1, "frame_second": 1.5}
        frame2_metadata = {"frame_number": 2, "frame_second": 3.0}
        mock_fetch_all_embeddings.return_value = [
            (frame1_embedding, frame1_metadata),
            (frame2_embedding, frame2_metadata),
        ]

        # Mock search results for each frame
        mock_hit1 = Mock()
        mock_hit1.id = "result-frame1"
        mock_hit1.score = 0.95
        mock_hit1.payload = {"video_id": "matched-video-1", "frame_number": 10}

        mock_hit2 = Mock()
        mock_hit2.id = "result-frame2"
        mock_hit2.score = 0.88
        mock_hit2.payload = {"video_id": "matched-video-1", "frame_number": 15}

        # Return different results for each frame search
        mock_search.side_effect = [[mock_hit1], [mock_hit2]]

        # Make request
        response = client.post(
            "/search-by-user-content/user-video",
            json={"user_id": self.user_id, "video_id": self.video_id, "limit": 5},
            headers=self.headers,
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # One video result

        video_result = data[0]
        assert video_result["video_id"] == "matched-video-1"
        assert video_result["total_frames"] == 2
        assert len(video_result["frame_results"]) == 2

        # Check frames are sorted by frame_number
        frames = video_result["frame_results"]
        assert frames[0]["frame_number"] == 1
        assert frames[1]["frame_number"] == 2
        assert frames[0]["score"] == 0.95
        assert frames[1]["score"] == 0.88

        # Verify service calls
        mock_fetch_all_embeddings.assert_called_once_with(
            collection="user_videos", user_id=self.user_id, video_id=self.video_id
        )
        assert mock_search.call_count == 2

    @patch("controllers.search_by_user_content.image.qdrant_service.fetch_embedding")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_user_image_not_found(self, mock_verify_api_key, mock_fetch_embedding):
        """Test image search when embedding not found."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock embedding fetch failure
        mock_fetch_embedding.side_effect = ValueError("No entry found")

        # Make request
        response = client.post(
            "/search-by-user-content/user-image",
            json={"user_id": self.user_id, "image_id": "non-existent-image", "limit": 5},
            headers=self.headers,
        )

        # Verify error response
        assert response.status_code == 500
        assert "Error retrieving image embedding" in response.json()["detail"]

    @patch("controllers.search_by_user_content.video.qdrant_service.fetch_all_video_embeddings")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_user_video_not_found(self, mock_verify_api_key, mock_fetch_all_embeddings):
        """Test video search when video not found."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock video embeddings fetch failure
        mock_fetch_all_embeddings.side_effect = ValueError("No video frames found")

        # Make request
        response = client.post(
            "/search-by-user-content/user-video",
            json={"user_id": self.user_id, "video_id": "non-existent-video", "limit": 5},
            headers=self.headers,
        )

        # Verify error response
        assert response.status_code == 500
        assert "Error retrieving video embeddings" in response.json()["detail"]

    @patch("controllers.search_by_user_content.video.qdrant_service.fetch_all_video_embeddings")
    @patch("auth.apikey.verify_api_key")
    def test_search_by_user_video_empty_embeddings(
        self, mock_verify_api_key, mock_fetch_all_embeddings
    ):
        """Test video search when no embeddings returned."""
        # Mock API key verification
        mock_verify_api_key.return_value = True

        # Mock empty embeddings
        mock_fetch_all_embeddings.return_value = []

        # Make request
        response = client.post(
            "/search-by-user-content/user-video",
            json={"user_id": self.user_id, "video_id": self.video_id, "limit": 5},
            headers=self.headers,
        )

        # Verify error response
        assert response.status_code == 404
        assert "No frames found for video" in response.json()["detail"]

    def test_search_by_user_image_unauthorized(self):
        """Test image search without API key."""
        response = client.post(
            "/search-by-user-content/user-image",
            json={"user_id": self.user_id, "image_id": self.image_id, "limit": 5},
        )

        # Should get unauthorized response
        assert response.status_code == 401

    def test_search_by_user_video_unauthorized(self):
        """Test video search without API key."""
        response = client.post(
            "/search-by-user-content/user-video",
            json={"user_id": self.user_id, "video_id": self.video_id, "limit": 5},
        )

        # Should get unauthorized response
        assert response.status_code == 401
