"""Tests for video processing service focusing on UUID folder usage and S3 key building."""

import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Set test environment variables before importing the service
os.environ["API_USERNAME"] = "test_user"
os.environ["API_PASSWORD"] = "test_password"
os.environ["API_KEY"] = "test_api_key_123"

from services.video_processing_service import VideoProcessingService, process_user_video


class TestVideoProcessingService:
    """Test suite for video processing service with focus on UUID folder usage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = VideoProcessingService()
        self.test_user_id = str(uuid.uuid4())
        self.test_video_id = str(uuid.uuid4())
        self.test_video_folder = str(uuid.uuid4())  # This is the UUID folder
        self.test_video_path = f"users/{self.test_user_id}/vid/{self.test_video_id}.mp4"

    @patch("services.video_processing_service.upload_to_s3_service")
    def test_upload_frames_to_s3_builds_correct_path_with_uuid_folder(
        self, mock_upload_to_s3_service
    ):
        """Test that _upload_frames_to_s3 builds S3 path with UUID folder correctly."""
        # Setup mock frame paths
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create mock frame files
            frame1_path = temp_path / "1_12.34.png"
            frame2_path = temp_path / "2_25.67.png"

            # Create empty files for testing
            frame1_path.write_bytes(b"fake_frame_data_1")
            frame2_path.write_bytes(b"fake_frame_data_2")

            frame_paths = [frame1_path, frame2_path]

            # Mock the upload_to_s3_service function to succeed
            mock_upload_to_s3_service.upload_file_to_s3.return_value = None

            # Call the method under test
            result = self.service._upload_frames_to_s3(
                frame_paths=frame_paths,
                user_id=self.test_user_id,
                video_folder=self.test_video_folder,  # UUID folder
            )

            # Verify the correct number of frames were processed
            assert len(result) == 2

            # Verify S3 paths are built correctly with UUID folder
            expected_base_path = f"users/{self.test_user_id}/vid/{self.test_video_folder}"

            # Check first frame
            assert result[0]["s3_path"] == f"{expected_base_path}/1_12.34.png"
            assert result[0]["frame_number"] == 1
            assert result[0]["frame_second"] == 12.34

            # Check second frame
            assert result[1]["s3_path"] == f"{expected_base_path}/2_25.67.png"
            assert result[1]["frame_number"] == 2
            assert result[1]["frame_second"] == 25.67

            # Verify upload_to_s3_service was called with correct S3 keys
            upload_calls = mock_upload_to_s3_service.upload_file_to_s3.call_args_list
            assert len(upload_calls) == 2

            # Check first upload call
            first_call_kwargs = upload_calls[0][1]
            assert first_call_kwargs["object_name"] == f"{expected_base_path}/1_12.34.png"

            # Check second upload call
            second_call_kwargs = upload_calls[1][1]
            assert second_call_kwargs["object_name"] == f"{expected_base_path}/2_25.67.png"

    def test_parse_frame_filename_correctly(self):
        """Test that frame filenames are parsed correctly."""
        # Test valid filename
        result = self.service._parse_frame_filename("1_12.34.png")
        assert result is not None
        assert result["frame_number"] == 1
        assert result["frame_second"] == 12.34

        # Test another valid filename
        result = self.service._parse_frame_filename("25_125.67.png")
        assert result is not None
        assert result["frame_number"] == 25
        assert result["frame_second"] == 125.67

        # Test invalid filename
        result = self.service._parse_frame_filename("invalid_filename.png")
        assert result is None

        # Test filename without timestamp
        result = self.service._parse_frame_filename("1.png")
        assert result is None

    @patch("services.video_processing_service.video_processing_service.process_video")
    def test_process_user_video_uses_video_folder_parameter(self, mock_process_video):
        """Test that process_user_video correctly passes video_folder parameter."""
        # Mock return value
        mock_process_video.return_value = {
            "frames_extracted": 5,
            "frames_uploaded": 5,
            "embeddings_stored": 5,
            "processing_status": "completed",
        }

        # Call the public API function
        result = process_user_video(
            video_s3_path=self.test_video_path,
            user_id=self.test_user_id,
            video_folder=self.test_video_folder,  # UUID folder
            video_id=self.test_video_id,
        )

        # Verify the underlying method was called with correct parameters
        mock_process_video.assert_called_once_with(
            video_path=self.test_video_path,
            user_id=self.test_user_id,
            video_folder=self.test_video_folder,  # Should receive UUID folder
            video_id=self.test_video_id,
        )

        # Verify return value
        assert result["frames_extracted"] == 5
        assert result["processing_status"] == "completed"

    @patch("services.video_processing_service.qdrant_service")
    def test_store_embeddings_in_qdrant_with_uuid_folder(self, mock_qdrant_service):
        """Test that embeddings are stored correctly with UUID folder reference."""
        # Mock Qdrant client
        mock_client = Mock()
        mock_qdrant_service._client.return_value = mock_client

        # Mock embeddings and frame info
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        frame_info = [
            {
                "frame_number": 1,
                "frame_second": 12.34,
                "s3_path": f"users/{self.test_user_id}/vid/{self.test_video_folder}/1_12.34.png",
                "s3_url": f"https://bucket.s3.region.amazonaws.com/users/{self.test_user_id}/vid/{self.test_video_folder}/1_12.34.png",
            },
            {
                "frame_number": 2,
                "frame_second": 25.67,
                "s3_path": f"users/{self.test_user_id}/vid/{self.test_video_folder}/2_25.67.png",
                "s3_url": f"https://bucket.s3.region.amazonaws.com/users/{self.test_user_id}/vid/{self.test_video_folder}/2_25.67.png",
            },
        ]

        # Call the method
        result = self.service._store_embeddings_in_qdrant(
            embeddings=embeddings,
            frame_info=frame_info,
            user_id=self.test_user_id,
            video_id=self.test_video_id,
            video_folder=self.test_video_folder,
        )

        # Verify Qdrant upsert was called
        mock_client.upsert.assert_called_once()
        call_args = mock_client.upsert.call_args

        # Verify collection name
        assert call_args[1]["collection_name"] == "user_videos"

        # Verify points were created correctly
        points = call_args[1]["points"]
        assert len(points) == 2

        # Check that S3 paths contain the UUID folder
        point1_payload = points[0].payload
        point2_payload = points[1].payload

        assert self.test_video_folder in point1_payload["path"]
        assert self.test_video_folder in point2_payload["path"]
        assert point1_payload["user_id"] == self.test_user_id
        assert point1_payload["video_id"] == self.test_video_id
        assert point2_payload["user_id"] == self.test_user_id
        assert point2_payload["video_id"] == self.test_video_id

        # Verify return value
        assert result == 2

    def test_video_processing_service_docstring_mentions_video_folder(self):
        """Test that docstrings mention video_folder (UUID) instead of timestamp."""
        # Check main process_video method docstring
        docstring = self.service.process_video.__doc__
        assert "video_folder" in docstring
        assert "UUID folder name" in docstring
        assert "video_timestamp" not in docstring  # Should not mention old parameter

        # Check public API function docstring
        docstring = process_user_video.__doc__
        assert "video_folder" in docstring
        assert "UUID folder name" in docstring
        assert "video_timestamp" not in docstring  # Should not mention old parameter

    def test_s3_path_pattern_documentation_updated(self):
        """Test that S3 path pattern comments mention video_folder correctly."""
        # This test verifies the internal documentation/comments are updated
        # We can check this by examining the _upload_frames_to_s3 method
        import inspect

        # Get the source code of the method
        source = inspect.getsource(self.service._upload_frames_to_s3)

        # Verify the S3 path pattern comment is updated
        assert "users/{user_id}/vid/{video_folder}/" in source
        assert "video_timestamp" not in source  # Should not mention old parameter
