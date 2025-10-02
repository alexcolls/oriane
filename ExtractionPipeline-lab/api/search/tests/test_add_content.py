"""Tests for add-content endpoints using real test assets."""

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

client = TestClient(app)

# Define paths for test assets
ASSET_DIRECTORY = "tests/assets/"
VIDEO_FILE = os.path.join(ASSET_DIRECTORY, "video.mp4")
IMAGE_PNG = os.path.join(ASSET_DIRECTORY, "image.png")
IMAGE_JPEG = os.path.join(ASSET_DIRECTORY, "image.jpeg")

# Test constants
USER_ID = "test-user-123"
VALID_HEADERS = {"X-API-Key": "test_api_key_123"}
INVALID_HEADERS = {"X-API-Key": "wrong_key"}


class TestImageUploadEndpoints:
    """Test suite for image upload endpoints."""

    def test_single_image_upload_png(self):
        """Test uploading a single PNG image."""
        with open(IMAGE_PNG, "rb") as image_file:
            response = client.post(
                f"/add-content/image/{USER_ID}",
                files={"file": ("test_image.png", image_file, "image/png")},
                headers=VALID_HEADERS,
            )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "image_id" in data
        assert "image_url" in data
        assert "status" in data

        # Verify response content
        assert data["status"] == "stored"
        assert "successfully" in data["message"].lower()
        assert data["image_url"].startswith("https://")
        assert ".png" in data["image_url"]
        assert USER_ID in data["image_url"]

        # Assert file key pattern: users/<user_id>/img/<uuid>.png
        # UUID consistency: filename=<image_id>.png, Qdrant id=image_id
        image_id = data["image_id"]
        expected_key_pattern = f"users/{USER_ID}/img/{image_id}.png"
        assert (
            expected_key_pattern in data["image_url"]
        ), f"File key pattern should be 'users/<user_id>/img/<uuid>.png', got URL: {data['image_url']}"

    def test_single_image_upload_jpeg(self):
        """Test uploading a single JPEG image."""
        with open(IMAGE_JPEG, "rb") as image_file:
            response = client.post(
                f"/add-content/image/{USER_ID}",
                files={"file": ("test_image.jpeg", image_file, "image/jpeg")},
                headers=VALID_HEADERS,
            )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "image_id" in data
        assert "image_url" in data
        assert "status" in data

        # Verify response content
        assert data["status"] == "stored"
        assert data["image_url"].startswith("https://")
        # Note: JPEG gets converted to PNG, so URL should have .png
        assert ".png" in data["image_url"]

    def test_batch_image_upload(self):
        """Test uploading multiple images in a batch."""
        files = []

        # Open both test images
        with open(IMAGE_PNG, "rb") as png_file, open(IMAGE_JPEG, "rb") as jpeg_file:
            files = [
                ("files", ("test1.png", png_file.read(), "image/png")),
                ("files", ("test2.jpeg", jpeg_file.read(), "image/jpeg")),
            ]

            response = client.post(
                f"/add-content/image/batch/{USER_ID}", files=files, headers=VALID_HEADERS
            )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "successful_uploads" in data
        assert "failed_uploads" in data
        assert "total_processed" in data

        # Verify response content
        assert data["total_processed"] == 2
        assert len(data["successful_uploads"]) == 2
        assert len(data["failed_uploads"]) == 0

        # Verify each successful upload has required fields
        for upload in data["successful_uploads"]:
            assert "image_id" in upload
            assert "image_url" in upload
            assert "filename" in upload

            # Assert file key pattern: users/<user_id>/img/<uuid>.png
            # UUID consistency: filename=<image_id>.png, Qdrant id=image_id
            image_id = upload["image_id"]
            expected_key_pattern = f"users/{USER_ID}/img/{image_id}.png"
            assert (
                expected_key_pattern in upload["image_url"]
            ), f"File key pattern should be 'users/<user_id>/img/<uuid>.png', got URL: {upload['image_url']}"

    def test_image_upload_without_api_key(self):
        """Test that image upload requires API key."""
        with open(IMAGE_PNG, "rb") as image_file:
            response = client.post(
                f"/add-content/image/{USER_ID}",
                files={"file": ("test.png", image_file, "image/png")},
                # No headers = no API key
            )

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "API key is required"

    def test_image_upload_with_invalid_api_key(self):
        """Test that image upload fails with invalid API key."""
        with open(IMAGE_PNG, "rb") as image_file:
            response = client.post(
                f"/add-content/image/{USER_ID}",
                files={"file": ("test.png", image_file, "image/png")},
                headers=INVALID_HEADERS,
            )

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid API key"

    def test_image_upload_invalid_file_type(self):
        """Test that non-image files are rejected."""
        # Create a fake text file
        fake_file = io.BytesIO(b"This is not an image")

        response = client.post(
            f"/add-content/image/{USER_ID}",
            files={"file": ("test.txt", fake_file, "text/plain")},
            headers=VALID_HEADERS,
        )

        assert response.status_code == 400
        data = response.json()
        assert "must be an image" in data["detail"]

    def test_image_upload_empty_file(self):
        """Test that empty files are rejected."""
        empty_file = io.BytesIO(b"")

        response = client.post(
            f"/add-content/image/{USER_ID}",
            files={"file": ("empty.png", empty_file, "image/png")},
            headers=VALID_HEADERS,
        )

        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower()

    def test_batch_upload_with_mixed_valid_invalid_files(self):
        """Test batch upload with a mix of valid and invalid files."""
        # Create a mix of valid and invalid files
        valid_image = io.BytesIO()
        # Create a simple test image
        test_img = Image.new("RGB", (100, 100), color="red")
        test_img.save(valid_image, format="PNG")
        valid_image.seek(0)

        invalid_file = io.BytesIO(b"This is not an image")

        files = [
            ("files", ("valid.png", valid_image.getvalue(), "image/png")),
            ("files", ("invalid.txt", invalid_file.getvalue(), "text/plain")),
        ]

        response = client.post(
            f"/add-content/image/batch/{USER_ID}", files=files, headers=VALID_HEADERS
        )

        assert response.status_code == 201
        data = response.json()

        # Should have 1 success and 1 failure
        assert data["total_processed"] == 2
        assert len(data["successful_uploads"]) == 1
        assert len(data["failed_uploads"]) == 1

        # Verify the failure reason
        failed_upload = data["failed_uploads"][0]
        assert failed_upload["filename"] == "invalid.txt"
        assert "must be an image" in failed_upload["error"]


class TestVideoUploadEndpoints:
    """Test suite for video upload endpoints."""

    def test_video_upload_success(self):
        """Test uploading a video file."""
        with open(VIDEO_FILE, "rb") as video_file:
            response = client.post(
                f"/add-content/video/{USER_ID}",
                files={"file": ("test_video.mp4", video_file, "video/mp4")},
                headers=VALID_HEADERS,
            )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "video_id" in data
        assert "video_url" in data
        assert "status" in data

        # Verify response content
        # Status can be "processed" (if processing succeeds) or "upload_completed_processing_failed" (if processing fails)
        assert data["status"] in ["processed", "upload_completed_processing_failed"]
        assert "successfully" in data["message"].lower() or "uploaded" in data["message"].lower()
        assert data["video_url"].startswith("https://")
        assert ".mp4" in data["video_url"]
        assert USER_ID in data["video_url"]

        # If processing succeeded, check processing details
        if data["status"] == "processed":
            assert "processing_details" in data
            details = data["processing_details"]
            assert "frames_extracted" in details
            assert "frames_uploaded" in details
            assert "embeddings_stored" in details
            assert details["processing_status"] == "completed"

        # If processing failed, should still have video uploaded
        elif data["status"] == "upload_completed_processing_failed":
            assert "processing_details" in data
            assert "error" in data["processing_details"]

    def test_video_upload_without_api_key(self):
        """Test that video upload requires API key."""
        with open(VIDEO_FILE, "rb") as video_file:
            response = client.post(
                f"/add-content/video/{USER_ID}",
                files={"file": ("test.mp4", video_file, "video/mp4")},
                # No headers = no API key
            )

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "API key is required"

    def test_video_upload_with_invalid_api_key(self):
        """Test that video upload fails with invalid API key."""
        with open(VIDEO_FILE, "rb") as video_file:
            response = client.post(
                f"/add-content/video/{USER_ID}",
                files={"file": ("test.mp4", video_file, "video/mp4")},
                headers=INVALID_HEADERS,
            )

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid API key"

    def test_video_upload_invalid_file_type(self):
        """Test that non-video files are rejected."""
        # Create a fake text file
        fake_file = io.BytesIO(b"This is not a video")

        response = client.post(
            f"/add-content/video/{USER_ID}",
            files={"file": ("test.txt", fake_file, "text/plain")},
            headers=VALID_HEADERS,
        )

        assert response.status_code == 400
        data = response.json()
        assert "must be a video" in data["detail"]

    def test_video_upload_empty_file(self):
        """Test that empty video files are rejected."""
        empty_file = io.BytesIO(b"")

        response = client.post(
            f"/add-content/video/{USER_ID}",
            files={"file": ("empty.mp4", empty_file, "video/mp4")},
            headers=VALID_HEADERS,
        )

        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower()


class TestContentUploadEdgeCases:
    """Test edge cases and error conditions."""

    def test_invalid_user_id_formats(self):
        """Test various user ID formats to ensure they're handled properly."""
        test_user_ids = [
            "user-123",
            "user_with_underscores",
            "user.with.dots",
            "user123",
            "f47ac10b-58cc-4372-a567-0e02b2c3d479",  # UUID format
        ]

        for user_id in test_user_ids:
            with open(IMAGE_PNG, "rb") as image_file:
                response = client.post(
                    f"/add-content/image/{user_id}",
                    files={"file": ("test.png", image_file, "image/png")},
                    headers=VALID_HEADERS,
                )

            # Should work for all valid user ID formats
            assert response.status_code == 201
            data = response.json()
            assert user_id in data["image_url"]

    def test_large_batch_upload_limit(self):
        """Test that batch uploads respect the 50-file limit."""
        # Create a simple test image
        test_image = io.BytesIO()
        img = Image.new("RGB", (10, 10), color="blue")
        img.save(test_image, format="PNG")
        test_image_bytes = test_image.getvalue()

        # Create 51 files (should exceed limit)
        files = [("files", (f"test{i}.png", test_image_bytes, "image/png")) for i in range(51)]

        response = client.post(
            f"/add-content/image/batch/{USER_ID}", files=files, headers=VALID_HEADERS
        )

        assert response.status_code == 400
        data = response.json()
        assert "50" in data["detail"]  # Should mention the limit
        assert "maximum" in data["detail"].lower()

    def test_empty_batch_upload(self):
        """Test that empty batch uploads are rejected."""
        response = client.post(
            f"/add-content/image/batch/{USER_ID}",
            files=[],  # Empty files list
            headers=VALID_HEADERS,
        )

        # FastAPI returns 422 for validation errors, which is correct for missing required fields
        assert response.status_code == 422
        data = response.json()
        # The error message will be different for validation errors
        assert "detail" in data
