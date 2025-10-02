#!/usr/bin/env python3
"""
Migration Validation Script
===========================

This script validates that the Qdrant migration was successful by checking:
1. No payload.path starts with "oriane-frames/"
2. All points contain uuid & created_at fields
3. Field rename verified (path format updated)
4. UUIDs are properly formatted
5. Timestamps are valid ISO format

Usage:
    python validate_migration.py --qdrant-url http://localhost:6333 --api-key test-key --collection watched_frames_test
"""

import argparse
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
from uuid import UUID

from qdrant_client import QdrantClient


class MigrationValidator:
    """Validates the results of payload migration."""

    def __init__(self, qdrant_url: str, api_key: str, collection_name: str):
        self.client = QdrantClient(url=qdrant_url, api_key=api_key)
        self.collection_name = collection_name

    def validate_uuid_format(self, uuid_str: str) -> bool:
        """Validate UUID format."""
        try:
            UUID(uuid_str)
            return True
        except (ValueError, TypeError):
            return False

    def validate_timestamp_format(self, timestamp_str: str) -> bool:
        """Validate ISO timestamp format."""
        try:
            # Try parsing as ISO format
            datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return True
        except (ValueError, TypeError):
            return False

    def validate_path_format(self, path: str) -> Tuple[bool, str]:
        """
        Validate path format.

        Returns:
            (is_valid, error_message)
        """
        if not path:
            return False, "Path is empty"

        if path.startswith("oriane-frames/"):
            return False, "Path still uses old 'oriane-frames/' prefix"

        # Check if path follows expected format: platform/code/filename
        parts = path.split("/")
        if len(parts) < 3:
            return False, f"Path format incorrect: {path} (expected: platform/code/filename)"

        platform = parts[0]
        if platform not in ["instagram", "youtube", "tiktok"]:  # Add other platforms as needed
            return False, f"Unknown platform in path: {platform}"

        return True, ""

    def scan_all_points(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Scan all points in the collection.

        Returns:
            List of all points with their payloads
        """
        print(f"🔍 Scanning all points in collection '{self.collection_name}'...")

        all_points = []
        offset = 0

        while True:
            try:
                response = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=limit,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )

                points = response[0]

                if not points:
                    break

                for point in points:
                    all_points.append({
                        "id": point.id,
                        "payload": point.payload or {}
                    })

                offset += len(points)

                if len(points) < limit:
                    break

            except Exception as e:
                print(f"❌ Error scanning points at offset {offset}: {e}")
                break

        print(f"📊 Found {len(all_points)} total points")
        return all_points

    def validate_point(self, point_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single point's payload.

        Returns:
            Dictionary with validation results
        """
        results = {
            "point_id": point_id,
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # Check 1: UUID field exists and is valid
        if "uuid" not in payload:
            results["valid"] = False
            results["errors"].append("Missing 'uuid' field")
        else:
            if not self.validate_uuid_format(payload["uuid"]):
                results["valid"] = False
                results["errors"].append(f"Invalid UUID format: {payload['uuid']}")

        # Check 2: created_at field exists and is valid
        if "created_at" not in payload:
            results["valid"] = False
            results["errors"].append("Missing 'created_at' field")
        else:
            if not self.validate_timestamp_format(payload["created_at"]):
                results["valid"] = False
                results["errors"].append(f"Invalid timestamp format: {payload['created_at']}")

        # Check 3: Path format validation
        if "path" not in payload:
            results["valid"] = False
            results["errors"].append("Missing 'path' field")
        else:
            path_valid, path_error = self.validate_path_format(payload["path"])
            if not path_valid:
                results["valid"] = False
                results["errors"].append(f"Path validation failed: {path_error}")

        # Check 4: Required fields
        required_fields = ["video_code", "frame_number", "frame_second"]
        for field in required_fields:
            if field not in payload:
                results["warnings"].append(f"Missing recommended field: {field}")

        # Check 5: Data type validation
        if "frame_number" in payload and not isinstance(payload["frame_number"], int):
            results["warnings"].append(f"frame_number should be int, got {type(payload['frame_number'])}")

        if "frame_second" in payload and not isinstance(payload["frame_second"], (int, float)):
            results["warnings"].append(f"frame_second should be number, got {type(payload['frame_second'])}")

        return results

    def run_validation(self) -> Dict[str, Any]:
        """
        Run complete validation of the collection.

        Returns:
            Summary of validation results
        """
        print(f"🔍 Starting validation of collection '{self.collection_name}'")

        # Get collection info
        try:
            info = self.client.get_collection(self.collection_name)
            print(f"📊 Collection has {info.points_count} total points")
        except Exception as e:
            print(f"❌ Error getting collection info: {e}")
            return {"error": str(e)}

        # Scan all points
        points = self.scan_all_points()

        if not points:
            return {
                "total_points": 0,
                "valid_points": 0,
                "invalid_points": 0,
                "warnings": 0,
                "errors": []
            }

        # Validate each point
        validation_results = []
        valid_count = 0
        invalid_count = 0
        total_warnings = 0

        print(f"🔍 Validating {len(points)} points...")

        for point_data in points:
            point_id = point_data["id"]
            payload = point_data["payload"]

            result = self.validate_point(point_id, payload)
            validation_results.append(result)

            if result["valid"]:
                valid_count += 1
            else:
                invalid_count += 1

            total_warnings += len(result["warnings"])

        # Collect all errors for summary
        all_errors = []
        for result in validation_results:
            for error in result["errors"]:
                all_errors.append(f"Point {result['point_id']}: {error}")

        # Summary
        summary = {
            "total_points": len(points),
            "valid_points": valid_count,
            "invalid_points": invalid_count,
            "warnings": total_warnings,
            "errors": all_errors,
            "success_rate": (valid_count / len(points)) * 100 if points else 0
        }

        return summary

    def print_validation_report(self, summary: Dict[str, Any]):
        """Print a detailed validation report."""
        print("\n" + "="*60)
        print("🔍 MIGRATION VALIDATION REPORT")
        print("="*60)

        if "error" in summary:
            print(f"❌ Validation failed: {summary['error']}")
            return

        print(f"📊 Total points: {summary['total_points']}")
        print(f"✅ Valid points: {summary['valid_points']}")
        print(f"❌ Invalid points: {summary['invalid_points']}")
        print(f"⚠️  Warnings: {summary['warnings']}")
        print(f"📈 Success rate: {summary['success_rate']:.1f}%")

        if summary['invalid_points'] == 0:
            print("\n🎉 ALL POINTS PASSED VALIDATION!")
            print("✅ Migration appears to be successful")
        else:
            print(f"\n❌ {summary['invalid_points']} points failed validation")

            if summary['errors']:
                print("\n🔍 ERRORS FOUND:")
                for error in summary['errors'][:10]:  # Show first 10 errors
                    print(f"   • {error}")

                if len(summary['errors']) > 10:
                    print(f"   ... and {len(summary['errors']) - 10} more errors")

        print("\n" + "="*60)

    def run_specific_checks(self) -> Dict[str, bool]:
        """
        Run specific checks mentioned in the task.

        Returns:
            Dictionary with specific check results
        """
        print("🎯 Running specific validation checks...")

        points = self.scan_all_points()

        checks = {
            "no_oriane_frames_paths": True,
            "all_have_uuid": True,
            "all_have_created_at": True,
            "paths_properly_renamed": True
        }

        for point_data in points:
            payload = point_data["payload"]

            # Check 1: No paths start with "oriane-frames/"
            if payload.get("path", "").startswith("oriane-frames/"):
                checks["no_oriane_frames_paths"] = False

            # Check 2: All points have uuid
            if "uuid" not in payload:
                checks["all_have_uuid"] = False

            # Check 3: All points have created_at
            if "created_at" not in payload:
                checks["all_have_created_at"] = False

            # Check 4: Paths are properly renamed (should start with platform name)
            path = payload.get("path", "")
            if path and not any(path.startswith(platform) for platform in ["instagram", "youtube", "tiktok"]):
                checks["paths_properly_renamed"] = False

        return checks

    def print_specific_checks_report(self, checks: Dict[str, bool]):
        """Print report for specific checks."""
        print("\n" + "="*60)
        print("🎯 SPECIFIC CHECKS REPORT")
        print("="*60)

        check_descriptions = {
            "no_oriane_frames_paths": "No payload.path starts with 'oriane-frames/'",
            "all_have_uuid": "All points contain uuid field",
            "all_have_created_at": "All points contain created_at field",
            "paths_properly_renamed": "Field rename verified (path format updated)"
        }

        for check_name, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            description = check_descriptions.get(check_name, check_name)
            print(f"{status} {description}")

        all_passed = all(checks.values())
        print(f"\n{'🎉 ALL CHECKS PASSED!' if all_passed else '❌ SOME CHECKS FAILED'}")
        print("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate Qdrant migration results")
    parser.add_argument("--qdrant-url", required=True, help="Qdrant server URL")
    parser.add_argument("--api-key", required=True, help="Qdrant API key")
    parser.add_argument("--collection", required=True, help="Collection name")
    parser.add_argument("--specific-checks-only", action="store_true", help="Only run specific checks from task")

    args = parser.parse_args()

    # Create validator
    validator = MigrationValidator(
        qdrant_url=args.qdrant_url,
        api_key=args.api_key,
        collection_name=args.collection
    )

    if args.specific_checks_only:
        # Run only specific checks
        checks = validator.run_specific_checks()
        validator.print_specific_checks_report(checks)
    else:
        # Run full validation
        summary = validator.run_validation()
        validator.print_validation_report(summary)

        # Also run specific checks
        checks = validator.run_specific_checks()
        validator.print_specific_checks_report(checks)


if __name__ == "__main__":
    main()
