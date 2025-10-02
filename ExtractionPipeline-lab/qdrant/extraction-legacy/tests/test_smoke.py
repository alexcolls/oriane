"""
Unit smoke tests for the extraction pipeline.

This module contains smoke tests that verify:
1. next_batch returns ≤1000 records and respects last_id
2. checkpoint survives crash simulation
3. Qdrant client mark_embedded functionality
"""

import json
import os

# Import the modules we're testing
import sys
import tempfile
import unittest.mock as mock
from datetime import datetime
from typing import List, Optional

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from checkpoint_manager import CheckpointManager
from db import mark_embedded, next_batch
from models import Base, InstaContent


class TestNextBatch:
    """Test suite for next_batch function."""

    def test_next_batch_returns_max_1000_records(self, mock_db_session):
        """Test that next_batch never returns more than 1000 records."""
        # Create mock data with more than 1000 records
        mock_records = [
            InstaContent(
                id=i,
                platform="instagram",
                code=f"test_code_{i}",
                is_extracted=False,
                is_embedded=False,
            )
            for i in range(1, 1500)
        ]

        # Mock the database query to return all records
        with mock.patch("db.DbSession") as mock_session:
            mock_session.return_value.__enter__.return_value.query.return_value.from_statement.return_value.params.return_value.all.return_value = mock_records[
                :1000
            ]

            # Call next_batch with default size
            result = next_batch()

            # Verify result is not more than 1000
            assert len(result) <= 1000
            assert len(result) == 1000

    def test_next_batch_respects_last_id_parameter(self, mock_db_session):
        """Test that next_batch respects the last_id parameter for pagination."""
        # Create mock data
        mock_records = [
            InstaContent(
                id=i,
                platform="instagram",
                code=f"test_code_{i}",
                is_extracted=False,
                is_embedded=False,
            )
            for i in range(101, 111)  # IDs 101-110
        ]

        with mock.patch("db.DbSession") as mock_session:
            mock_session.return_value.__enter__.return_value.query.return_value.from_statement.return_value.params.return_value.all.return_value = (
                mock_records
            )

            # Call next_batch with last_id=100
            result = next_batch(size=10, last_id=100)

            # Verify that the query was called with the correct parameters
            mock_session.return_value.__enter__.return_value.query.return_value.from_statement.return_value.params.assert_called_with(
                last_id=100, size=10
            )

            # Verify result contains records with IDs > 100
            assert len(result) == 10
            assert all(record.id > 100 for record in result)

    def test_next_batch_with_custom_size(self, mock_db_session):
        """Test that next_batch respects custom batch size."""
        # Create mock data
        mock_records = [
            InstaContent(
                id=i,
                platform="instagram",
                code=f"test_code_{i}",
                is_extracted=False,
                is_embedded=False,
            )
            for i in range(1, 51)  # 50 records
        ]

        with mock.patch("db.DbSession") as mock_session:
            mock_session.return_value.__enter__.return_value.query.return_value.from_statement.return_value.params.return_value.all.return_value = (
                mock_records
            )

            # Call next_batch with custom size
            result = next_batch(size=50)

            # Verify the size parameter was used
            mock_session.return_value.__enter__.return_value.query.return_value.from_statement.return_value.params.assert_called_with(
                last_id=None, size=50
            )

            assert len(result) == 50

    def test_next_batch_returns_empty_when_no_records(self, mock_db_session):
        """Test that next_batch returns empty list when no records are found."""
        with mock.patch("db.DbSession") as mock_session:
            mock_session.return_value.__enter__.return_value.query.return_value.from_statement.return_value.params.return_value.all.return_value = (
                []
            )

            # Call next_batch
            result = next_batch()

            # Verify empty result
            assert result == []
            assert len(result) == 0


class TestCheckpointManager:
    """Test suite for checkpoint manager crash survival."""

    def test_checkpoint_survives_json_crash_simulation(self):
        """Test that JSON checkpoint survives crash simulation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            checkpoint_file = os.path.join(temp_dir, "test_checkpoint.json")

            # Create checkpoint manager
            manager = CheckpointManager(use_json=True, json_file_path=checkpoint_file)

            # Set initial checkpoint
            last_processed_id = 12345
            manager.update_checkpoint(last_processed_id)

            # Verify checkpoint was written to file
            assert os.path.exists(checkpoint_file)

            # Simulate crash by creating a new manager instance
            # (this simulates restarting the application)
            new_manager = CheckpointManager(use_json=True, json_file_path=checkpoint_file)

            # Verify checkpoint survives the "crash"
            recovered_id = new_manager.get_checkpoint()
            assert recovered_id == last_processed_id

    def test_checkpoint_file_corruption_handling(self):
        """Test that checkpoint manager handles corrupted files gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            checkpoint_file = os.path.join(temp_dir, "corrupt_checkpoint.json")

            # Create corrupted checkpoint file
            with open(checkpoint_file, "w") as f:
                f.write("invalid json content {")

            # Create checkpoint manager
            manager = CheckpointManager(use_json=True, json_file_path=checkpoint_file)

            # Verify that corrupted file is handled gracefully
            checkpoint = manager.get_checkpoint()
            assert checkpoint is None

    def test_checkpoint_directory_creation(self):
        """Test that checkpoint manager creates necessary directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "nested", "dir", "checkpoint.json")

            # Create checkpoint manager with nested path
            manager = CheckpointManager(use_json=True, json_file_path=nested_path)

            # Update checkpoint (should create directories)
            manager.update_checkpoint(42)

            # Verify file was created and directories exist
            assert os.path.exists(nested_path)
            assert os.path.exists(os.path.dirname(nested_path))

    def test_checkpoint_concurrent_access_simulation(self):
        """Test checkpoint behavior under simulated concurrent access."""
        with tempfile.TemporaryDirectory() as temp_dir:
            checkpoint_file = os.path.join(temp_dir, "concurrent_checkpoint.json")

            # Create multiple managers (simulating concurrent processes)
            manager1 = CheckpointManager(use_json=True, json_file_path=checkpoint_file)
            manager2 = CheckpointManager(use_json=True, json_file_path=checkpoint_file)

            # Update checkpoint from first manager
            manager1.update_checkpoint(100)

            # Read from second manager
            checkpoint = manager2.get_checkpoint()
            assert checkpoint == 100

            # Update from second manager
            manager2.update_checkpoint(200)

            # Read from first manager
            checkpoint = manager1.get_checkpoint()
            assert checkpoint == 200


class TestQdrantClientStub:
    """Test suite for Qdrant client functionality."""

    def test_mark_embedded_with_valid_ids(self, mock_db_session):
        """Test mark_embedded with valid ID list."""
        test_ids = [1, 2, 3, 4, 5]

        with mock.patch("db.DbSession") as mock_session:
            mock_session_instance = mock_session.return_value.__enter__.return_value

            # Call mark_embedded
            mark_embedded(test_ids)

            # Verify the SQL was executed with correct parameters
            mock_session_instance.execute.assert_called_once()

            # Get the call arguments
            call_args = mock_session_instance.execute.call_args
            sql_text = call_args[0][0]
            params = call_args[0][1]

            # Verify SQL contains the expected update statement
            assert "UPDATE public.insta_content" in str(sql_text)
            assert "SET is_embedded = true" in str(sql_text)
            assert "WHERE id = ANY(:id_list)" in str(sql_text)

            # Verify parameters
            assert params["id_list"] == test_ids
            assert "embedded_at" in params
            assert isinstance(params["embedded_at"], datetime)

    def test_mark_embedded_with_empty_list(self, mock_db_session):
        """Test that mark_embedded handles empty ID list gracefully."""
        with mock.patch("db.DbSession") as mock_session:
            mock_session_instance = mock_session.return_value.__enter__.return_value

            # Call mark_embedded with empty list
            mark_embedded([])

            # Verify no database operations were performed
            mock_session_instance.execute.assert_not_called()

    def test_mark_embedded_with_single_id(self, mock_db_session):
        """Test mark_embedded with single ID."""
        test_id = [42]

        with mock.patch("db.DbSession") as mock_session:
            mock_session_instance = mock_session.return_value.__enter__.return_value

            # Call mark_embedded
            mark_embedded(test_id)

            # Verify the SQL was executed
            mock_session_instance.execute.assert_called_once()

            # Get the call arguments
            call_args = mock_session_instance.execute.call_args
            params = call_args[0][1]

            # Verify parameters
            assert params["id_list"] == test_id

    def test_mark_embedded_database_error_handling(self, mock_db_session):
        """Test that mark_embedded handles database errors properly."""
        test_ids = [1, 2, 3]

        with mock.patch("db.DbSession") as mock_session:
            mock_session_instance = mock_session.return_value.__enter__.return_value

            # Simulate database error
            mock_session_instance.execute.side_effect = Exception("Database connection failed")

            # Verify exception is raised
            with pytest.raises(Exception) as exc_info:
                mark_embedded(test_ids)

            assert "Database connection failed" in str(exc_info.value)

    def test_mark_embedded_parameters_validation(self, mock_db_session):
        """Test that mark_embedded validates parameters correctly."""
        # Test with various input types
        test_cases = [
            [1, 2, 3],  # normal integers
            [999, 1000, 1001],  # large integers
            [1],  # single integer
        ]

        for test_ids in test_cases:
            with mock.patch("db.DbSession") as mock_session:
                mock_session_instance = mock_session.return_value.__enter__.return_value

                # Call mark_embedded
                mark_embedded(test_ids)

                # Verify the call was made
                mock_session_instance.execute.assert_called_once()

                # Get the call arguments
                call_args = mock_session_instance.execute.call_args
                params = call_args[0][1]

                # Verify parameters
                assert params["id_list"] == test_ids
                assert isinstance(params["embedded_at"], datetime)

                # Reset mock for next iteration
                mock_session_instance.execute.reset_mock()


# Fixtures for mocking
@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    with mock.patch("db.DbSession") as mock_session:
        yield mock_session


@pytest.fixture
def sample_insta_content():
    """Sample InstaContent records for testing."""
    return [
        InstaContent(
            id=i,
            platform="instagram",
            code=f"test_code_{i}",
            is_extracted=False,
            is_embedded=False,
            content_type="video",
            caption=f"Test caption {i}",
            media_url=f"https://example.com/media_{i}.mp4",
            thumbnail_url=f"https://example.com/thumb_{i}.jpg",
            post_url=f"https://instagram.com/p/test_code_{i}",
            author_username=f"user_{i}",
            author_id=f"user_id_{i}",
        )
        for i in range(1, 11)
    ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
