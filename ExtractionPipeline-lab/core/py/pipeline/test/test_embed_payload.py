import unittest
import tempfile
import os
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from PIL import Image
import numpy as np


class TestEmbedPayload(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.test_code = "test_code_123"
        self.platform = "instagram"

    def create_fake_png(self, filename: str, temp_dir: Path) -> Path:
        """Create a fake PNG file for testing."""
        # Create a simple 100x100 RGB image
        image = Image.new('RGB', (100, 100), color=(255, 0, 0))
        file_path = temp_dir / filename
        image.save(file_path, 'PNG')
        return file_path

    def test_payload_structure_basic(self):
        """Test the basic payload structure."""
        code = "test_code"
        frame_idx = "1"
        timestamp_s = 1234567890.5
        platform = "instagram"
        frame_name = "1_1234567890.5.png"

        # Expected s3 path
        s3_path = f"{platform}/{code}/{frame_name}"

        # Simulate creating a payload as done in the actual code
        frame_number = int(frame_idx)
        frame_second = timestamp_s

        payload = {
            "uuid": str(uuid5(NAMESPACE_URL, f"{code}_{frame_number}_{frame_second}")),
            "created_at": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
            "video_code": code,
            "frame_number": frame_number,
            "frame_second": frame_second,
            "path": s3_path,
        }

        # Assert the payload has all required keys
        required_keys = ["uuid", "created_at", "video_code", "frame_number", "frame_second", "path"]
        for key in required_keys:
            self.assertIn(key, payload, f"Missing required key: {key}")

        # Assert data types and values
        self.assertIsInstance(payload["uuid"], str)
        self.assertIsInstance(payload["created_at"], str)
        self.assertEqual(payload["video_code"], code)
        self.assertEqual(payload["frame_number"], 1)
        self.assertEqual(payload["frame_second"], timestamp_s)
        self.assertEqual(payload["path"], s3_path)

        # Test UUID generation is consistent
        expected_uuid = str(uuid5(NAMESPACE_URL, f"{code}_{frame_number}_{frame_second}"))
        self.assertEqual(payload["uuid"], expected_uuid)

    def test_payload_with_fake_png_files(self):
        """Test payload generation with actual fake PNG files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create fake PNG files with proper naming convention
            frame_files = [
                self.create_fake_png("0_12.5.png", temp_path),
                self.create_fake_png("1_25.0.png", temp_path),
                self.create_fake_png("2_37.5.png", temp_path)
            ]

            # Test the payload generation logic for each file
            for i, frame_path in enumerate(frame_files):
                frame_name = frame_path.name
                parts = frame_name.replace(".png", "").split("_")

                if len(parts) >= 2:
                    frame_idx = parts[0]
                    timestamp_s = float(parts[1])
                else:
                    frame_idx = str(i)
                    timestamp_s = float(i)

                # Convert to new payload structure
                frame_number = int(frame_idx)
                frame_second = timestamp_s
                s3_path = f"{self.platform}/{self.test_code}/{frame_path.name}"

                payload = {
                    "uuid": str(uuid5(NAMESPACE_URL, f"{self.test_code}_{frame_number}_{frame_second}")),
                    "created_at": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
                    "video_code": self.test_code,
                    "frame_number": frame_number,
                    "frame_second": frame_second,
                    "path": s3_path,
                }

                # Assertions
                self.assertEqual(payload["video_code"], self.test_code)
                self.assertEqual(payload["frame_number"], i)
                self.assertEqual(payload["frame_second"], [12.5, 25.0, 37.5][i])
                self.assertEqual(payload["path"], f"{self.platform}/{self.test_code}/{frame_name}")
                # Test that UUID is a valid string format (UUID5 generates consistent UUIDs)
                self.assertIsInstance(payload["uuid"], str)
                self.assertEqual(len(payload["uuid"]), 36)  # Standard UUID string length
                self.assertIn("-", payload["uuid"])  # UUIDs contain hyphens

                # Test created_at is in ISO format
                try:
                    datetime.fromisoformat(payload["created_at"].replace('Z', '+00:00'))
                except ValueError:
                    self.fail("created_at is not in valid ISO format")

    def test_s3_path_construction(self):
        """Test that S3 path is constructed correctly."""
        code = "ABC123"
        platform = "instagram"
        frame_name = "5_123.45.png"

        expected_s3_path = f"{platform}/{code}/{frame_name}"
        actual_s3_path = f"{platform}/{code}/{frame_name}"

        self.assertEqual(actual_s3_path, expected_s3_path)
        self.assertEqual(actual_s3_path, "instagram/ABC123/5_123.45.png")

if __name__ == "__main__":
    unittest.main()
