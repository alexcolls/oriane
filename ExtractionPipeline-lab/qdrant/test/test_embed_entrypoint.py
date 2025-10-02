#!/usr/bin/env python3
"""
Test Script for embed_entrypoint.py
===================================

This script creates dummy PNG files and tests the modified embed_entrypoint.py
to verify that new points match the target schema.

It creates:
1. Dummy PNG files in a temporary directory
2. Runs embed_entrypoint.py against these files
3. Validates that resulting Qdrant points have the correct structure
"""

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import time

import numpy as np
from PIL import Image
from qdrant_client import QdrantClient


class EmbedEntrypointTester:
    """Tests embed_entrypoint.py with dummy data."""

    def __init__(self, qdrant_url: str, api_key: str, collection_name: str):
        self.client = QdrantClient(url=qdrant_url, api_key=api_key)
        self.collection_name = collection_name
        self.temp_dir = None

    def create_dummy_png_files(self, num_files: int = 5, video_codes: List[str] = None) -> str:
        """
        Create dummy PNG files for testing.

        Args:
            num_files: Number of PNG files to create per video code
            video_codes: List of video codes to create files for

        Returns:
            Path to temporary directory containing PNG files
        """
        if video_codes is None:
            video_codes = ["TEST001", "TEST002"]

        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="embed_test_")
        print(f"📁 Creating dummy PNG files in {self.temp_dir}")

        total_files = 0

        for video_code in video_codes:
            # Create subdirectory for this video
            video_dir = Path(self.temp_dir) / video_code
            video_dir.mkdir(exist_ok=True)

            for i in range(num_files):
                # Create dummy image
                width, height = 224, 224  # Standard input size for many models

                # Generate random image data
                image_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
                image = Image.fromarray(image_array)

                # Save as PNG
                frame_filename = f"frame_{i+1:06d}.png"
                frame_path = video_dir / frame_filename
                image.save(frame_path, "PNG")

                total_files += 1

        print(f"✅ Created {total_files} dummy PNG files")
        return self.temp_dir

    def cleanup_temp_dir(self):
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"🗑️  Cleaned up temporary directory")

    def clear_test_collection(self):
        """Clear test collection before running test."""
        try:
            # Try to delete all points
            response = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000,
                with_payload=False,
                with_vectors=False
            )

            points = response[0]
            if points:
                point_ids = [point.id for point in points]
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )
                print(f"🗑️  Cleared {len(point_ids)} existing points from collection")
            else:
                print("ℹ️  Collection was already empty")

        except Exception as e:
            print(f"⚠️  Warning: Could not clear collection: {e}")

    def run_embed_entrypoint(self, png_directory: str, embed_script_path: str) -> bool:
        """
        Run embed_entrypoint.py against the dummy PNG files.

        Args:
            png_directory: Directory containing PNG files
            embed_script_path: Path to embed_entrypoint.py script

        Returns:
            True if successful, False otherwise
        """
        print(f"🚀 Running embed_entrypoint.py against {png_directory}")

        try:
            # Build command - need to check the actual interface of embed_entrypoint.py
            cmd = [
                "python3",
                embed_script_path,
                "--input-dir", png_directory,
                "--qdrant-url", self.client._client.base_url,
                "--collection", self.collection_name,
            ]

            # Check if we need API key
            if hasattr(self.client, 'api_key') and self.client.api_key:
                cmd.extend(["--api-key", self.client.api_key])

            print(f"📝 Command: {' '.join(cmd)}")

            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            print(f"📤 Exit code: {result.returncode}")

            if result.stdout:
                print("📄 STDOUT:")
                print(result.stdout)

            if result.stderr:
                print("📄 STDERR:")
                print(result.stderr)

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print("❌ Command timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"❌ Error running embed_entrypoint.py: {e}")
            return False

    def validate_generated_points(self) -> Dict[str, Any]:
        """
        Validate that the points generated by embed_entrypoint.py match the target schema.

        Returns:
            Validation results
        """
        print("🔍 Validating generated points...")

        # Wait a moment for points to be indexed
        time.sleep(2)

        try:
            # Get all points from collection
            response = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True,
                with_vectors=True
            )

            points = response[0]
            print(f"📊 Found {len(points)} points in collection")

            if not points:
                return {
                    "success": False,
                    "error": "No points found in collection",
                    "points_count": 0
                }

            # Validate each point
            validation_results = {
                "success": True,
                "points_count": len(points),
                "valid_points": 0,
                "invalid_points": 0,
                "errors": [],
                "schema_compliance": {
                    "has_uuid": 0,
                    "has_created_at": 0,
                    "has_video_code": 0,
                    "has_frame_number": 0,
                    "has_frame_second": 0,
                    "has_proper_path": 0,
                    "has_vector": 0
                }
            }

            for point in points:
                payload = point.payload or {}
                vector = point.vector

                point_valid = True
                point_errors = []

                # Check required fields
                required_fields = ["uuid", "created_at", "video_code", "frame_number", "frame_second", "path"]
                for field in required_fields:
                    if field in payload:
                        validation_results["schema_compliance"][f"has_{field}"] += 1
                    else:
                        point_valid = False
                        point_errors.append(f"Missing required field: {field}")

                # Check vector
                if vector and len(vector) > 0:
                    validation_results["schema_compliance"]["has_vector"] += 1
                else:
                    point_valid = False
                    point_errors.append("Missing or empty vector")

                # Check path format
                path = payload.get("path", "")
                if path and not path.startswith("oriane-frames/"):
                    validation_results["schema_compliance"]["has_proper_path"] += 1
                elif path.startswith("oriane-frames/"):
                    point_valid = False
                    point_errors.append(f"Path uses old format: {path}")

                # Check UUID format
                uuid_str = payload.get("uuid", "")
                if uuid_str:
                    try:
                        from uuid import UUID
                        UUID(uuid_str)
                    except ValueError:
                        point_valid = False
                        point_errors.append(f"Invalid UUID format: {uuid_str}")

                # Check timestamp format
                created_at = payload.get("created_at", "")
                if created_at:
                    try:
                        from datetime import datetime
                        datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except ValueError:
                        point_valid = False
                        point_errors.append(f"Invalid timestamp format: {created_at}")

                if point_valid:
                    validation_results["valid_points"] += 1
                else:
                    validation_results["invalid_points"] += 1
                    validation_results["errors"].extend([f"Point {point.id}: {error}" for error in point_errors])

            # Overall success
            validation_results["success"] = validation_results["invalid_points"] == 0

            return validation_results

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "points_count": 0
            }

    def print_validation_report(self, results: Dict[str, Any]):
        """Print validation report."""
        print("\n" + "="*60)
        print("🔍 EMBED_ENTRYPOINT VALIDATION REPORT")
        print("="*60)

        if "error" in results:
            print(f"❌ Validation failed: {results['error']}")
            return

        print(f"📊 Total points generated: {results['points_count']}")
        print(f"✅ Valid points: {results['valid_points']}")
        print(f"❌ Invalid points: {results['invalid_points']}")

        if results['success']:
            print("\n🎉 ALL POINTS PASSED VALIDATION!")
            print("✅ embed_entrypoint.py generates correct schema")
        else:
            print(f"\n❌ {results['invalid_points']} points failed validation")

            if results['errors']:
                print("\n🔍 ERRORS FOUND:")
                for error in results['errors'][:10]:
                    print(f"   • {error}")

                if len(results['errors']) > 10:
                    print(f"   ... and {len(results['errors']) - 10} more errors")

        # Schema compliance report
        print(f"\n📋 SCHEMA COMPLIANCE:")
        schema = results.get('schema_compliance', {})
        total = results['points_count']

        for field, count in schema.items():
            percentage = (count / total) * 100 if total > 0 else 0
            status = "✅" if count == total else "❌"
            print(f"   {status} {field}: {count}/{total} ({percentage:.1f}%)")

        print("="*60)

    def run_full_test(self, embed_script_path: str, num_files: int = 5) -> bool:
        """
        Run the complete test suite.

        Args:
            embed_script_path: Path to embed_entrypoint.py
            num_files: Number of PNG files to generate per video

        Returns:
            True if all tests pass, False otherwise
        """
        try:
            # Step 1: Create dummy PNG files
            png_dir = self.create_dummy_png_files(num_files=num_files)

            # Step 2: Clear test collection
            self.clear_test_collection()

            # Step 3: Run embed_entrypoint.py
            embed_success = self.run_embed_entrypoint(png_dir, embed_script_path)

            if not embed_success:
                print("❌ embed_entrypoint.py failed to run successfully")
                return False

            # Step 4: Validate generated points
            validation_results = self.validate_generated_points()
            self.print_validation_report(validation_results)

            return validation_results.get('success', False)

        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            return False
        finally:
            # Always clean up
            self.cleanup_temp_dir()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test embed_entrypoint.py with dummy PNG files")
    parser.add_argument("--qdrant-url", required=True, help="Qdrant server URL")
    parser.add_argument("--api-key", required=True, help="Qdrant API key")
    parser.add_argument("--collection", required=True, help="Collection name")
    parser.add_argument("--embed-script", required=True, help="Path to embed_entrypoint.py script")
    parser.add_argument("--num-files", type=int, default=5, help="Number of PNG files to generate per video")

    args = parser.parse_args()

    # Create tester
    tester = EmbedEntrypointTester(
        qdrant_url=args.qdrant_url,
        api_key=args.api_key,
        collection_name=args.collection
    )

    # Run full test
    success = tester.run_full_test(
        embed_script_path=args.embed_script,
        num_files=args.num_files
    )

    if success:
        print("\n🎉 ALL TESTS PASSED!")
        exit(0)
    else:
        print("\n❌ SOME TESTS FAILED!")
        exit(1)


if __name__ == "__main__":
    main()
