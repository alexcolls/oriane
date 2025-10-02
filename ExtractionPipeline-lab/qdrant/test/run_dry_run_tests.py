#!/usr/bin/env python3
"""
Master Dry-Run Test Script
=========================

This script orchestrates the complete dry-run and unit testing process for Qdrant migration:

1. Connects to remote Qdrant instance
2. Creates test collection with appropriate schema
3. Loads sample "bad" points into the collection
4. Runs migration in dry-run mode first, then live mode
5. Validates migration results
6. Tests embed_entrypoint.py with dummy PNG files
7. Validates that new points match target schema
8. Cleans up test collection

Usage:
    python run_dry_run_tests.py --test-dir /path/to/test/scripts
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

class DryRunTestOrchestrator:
    """Orchestrates the complete dry-run testing process."""

    def __init__(self, test_dir: str):
        self.test_dir = Path(test_dir)

        # Load environment variables from core pipeline .env file
        env_file = Path("/home/quantium/labs/oriane/ExtractionPipeline/core/py/pipeline/.env")
        if env_file.exists():
            load_dotenv(env_file)

        # Get remote Qdrant configuration from environment
        self.qdrant_url = os.getenv("QDRANT_URL", "http://qdrant.admin.oriane.xyz:6333/")
        self.api_key = os.getenv("QDRANT_KEY", "")
        self.collection_name = "watched_frames_test"

        # Validate configuration
        if not self.qdrant_url or not self.api_key:
            raise ValueError("QDRANT_URL and QDRANT_KEY must be set in environment")

        print(f"📡 Using remote Qdrant: {self.qdrant_url}")
        print(f"🔑 API Key: {self.api_key[:10]}...")

    def validate_qdrant_connection(self) -> bool:
        """Validate connection to remote Qdrant instance."""
        print("🔍 Validating connection to remote Qdrant...")

        try:
            # Test connection to remote Qdrant
            health_check = subprocess.run(
                ["curl", "-f", "-H", f"Api-Key: {self.api_key}", f"{self.qdrant_url}/collections"],
                capture_output=True,
                timeout=10
            )
            if health_check.returncode == 0:
                print("✅ Remote Qdrant connection validated")
                return True
            else:
                print(f"❌ Failed to connect to remote Qdrant: {health_check.stderr.decode()}")
                return False
        except subprocess.TimeoutExpired:
            print("❌ Remote Qdrant connection timeout")
            return False
        except Exception as e:
            print(f"❌ Error connecting to remote Qdrant: {e}")
            return False

    def cleanup_test_collection(self):
        """Clean up test collection from remote Qdrant."""
        print("🧹 Cleaning up test collection...")

        try:
            # Delete test collection
            result = subprocess.run([
                "curl", "-X", "DELETE",
                "-H", f"Api-Key: {self.api_key}",
                f"{self.qdrant_url}/collections/{self.collection_name}"
            ], capture_output=True, timeout=10)

            if result.returncode == 0:
                print("✅ Test collection cleaned up")
            else:
                print(f"⚠️  Warning: Could not delete test collection: {result.stderr.decode()}")
        except Exception as e:
            print(f"⚠️  Warning: Error cleaning up collection: {e}")

    def create_test_collection(self) -> bool:
        """Create test collection with appropriate schema."""
        print("📊 Creating test collection...")

        create_script = self.test_dir.parent / "create.py"
        if not create_script.exists():
            print(f"❌ Create script not found: {create_script}")
            return False

        try:
            result = subprocess.run([
                "python3", str(create_script),
                "--qdrant-url", self.qdrant_url,
                "--api-key", self.api_key,
                "--collection", self.collection_name
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Failed to create collection:")
                print(result.stderr)
                return False

            print("✅ Test collection created successfully")
            return True

        except Exception as e:
            print(f"❌ Error creating collection: {e}")
            return False

    def generate_test_data(self) -> bool:
        """Generate test data with bad points."""
        print("📦 Generating test data...")

        generator_script = self.test_dir / "generate_test_data.py"

        try:
            result = subprocess.run([
                "python3", str(generator_script),
                "--qdrant-url", self.qdrant_url,
                "--api-key", self.api_key,
                "--collection", self.collection_name,
                "--bad-points", "30",
                "--good-points", "5",
                "--clear"
            ], capture_output=True, text=True)

            print("📄 Generator output:")
            print(result.stdout)

            if result.returncode != 0:
                print(f"❌ Failed to generate test data:")
                print(result.stderr)
                return False

            print("✅ Test data generated successfully")
            return True

        except Exception as e:
            print(f"❌ Error generating test data: {e}")
            return False

    def run_migration_dry_run(self) -> bool:
        """Run migration in dry-run mode."""
        print("🔄 Running migration in dry-run mode...")

        migration_script = self.test_dir / "migrate_payload_structure.py"

        try:
            result = subprocess.run([
                "python3", str(migration_script),
                "--qdrant-url", self.qdrant_url,
                "--api-key", self.api_key,
                "--collection", self.collection_name,
                "--dry-run"
            ], capture_output=True, text=True)

            print("📄 Dry-run output:")
            print(result.stdout)

            if result.returncode != 0:
                print(f"❌ Dry-run failed:")
                print(result.stderr)
                return False

            print("✅ Dry-run completed successfully")
            return True

        except Exception as e:
            print(f"❌ Error during dry-run: {e}")
            return False

    def run_migration_live(self) -> bool:
        """Run migration in live mode."""
        print("🚀 Running migration in live mode...")

        migration_script = self.test_dir / "migrate_payload_structure.py"

        try:
            result = subprocess.run([
                "python3", str(migration_script),
                "--qdrant-url", self.qdrant_url,
                "--api-key", self.api_key,
                "--collection", self.collection_name
            ], capture_output=True, text=True)

            print("📄 Migration output:")
            print(result.stdout)

            if result.returncode != 0:
                print(f"❌ Migration failed:")
                print(result.stderr)
                return False

            print("✅ Migration completed successfully")
            return True

        except Exception as e:
            print(f"❌ Error during migration: {e}")
            return False

    def validate_migration(self) -> bool:
        """Validate migration results."""
        print("🔍 Validating migration results...")

        validation_script = self.test_dir / "validate_migration.py"

        try:
            result = subprocess.run([
                "python3", str(validation_script),
                "--qdrant-url", self.qdrant_url,
                "--api-key", self.api_key,
                "--collection", self.collection_name
            ], capture_output=True, text=True)

            print("📄 Validation output:")
            print(result.stdout)

            if result.returncode != 0:
                print(f"❌ Validation failed:")
                print(result.stderr)
                return False

            # Check if all specific checks passed
            if "ALL CHECKS PASSED!" in result.stdout:
                print("✅ Migration validation passed")
                return True
            else:
                print("❌ Migration validation failed")
                return False

        except Exception as e:
            print(f"❌ Error during validation: {e}")
            return False

    def test_embed_entrypoint(self) -> bool:
        """Test embed_entrypoint.py with dummy PNG files."""
        print("🖼️  Testing embed_entrypoint.py...")

        # Find embed_entrypoint.py
        embed_script = self.test_dir.parent / "embed_entrypoint.py"
        if not embed_script.exists():
            print(f"❌ embed_entrypoint.py not found: {embed_script}")
            return False

        test_script = self.test_dir / "test_embed_entrypoint.py"

        try:
            result = subprocess.run([
                "python3", str(test_script),
                "--qdrant-url", self.qdrant_url,
                "--api-key", self.api_key,
                "--collection", self.collection_name,
                "--embed-script", str(embed_script),
                "--num-files", "3"
            ], capture_output=True, text=True)

            print("📄 Embed test output:")
            print(result.stdout)

            if result.stderr:
                print("📄 Embed test errors:")
                print(result.stderr)

            if result.returncode != 0:
                print(f"❌ Embed entrypoint test failed")
                return False

            print("✅ Embed entrypoint test passed")
            return True

        except Exception as e:
            print(f"❌ Error testing embed_entrypoint: {e}")
            return False

    def run_complete_test_suite(self) -> bool:
        """Run the complete test suite."""
        print("🎯 Starting complete dry-run test suite")
        print("="*60)

        test_results = {}

        try:
            # Step 1: Validate remote Qdrant connection
            step_name = "Validate Qdrant Connection"
            print(f"\n📍 STEP 1: {step_name}")
            test_results[step_name] = self.validate_qdrant_connection()
            if not test_results[step_name]:
                return False

            # Step 2: Create test collection
            step_name = "Create Collection"
            print(f"\n📍 STEP 2: {step_name}")
            test_results[step_name] = self.create_test_collection()
            if not test_results[step_name]:
                return False

            # Step 3: Generate test data
            step_name = "Generate Test Data"
            print(f"\n📍 STEP 3: {step_name}")
            test_results[step_name] = self.generate_test_data()
            if not test_results[step_name]:
                return False

            # Step 4: Run dry-run migration
            step_name = "Migration Dry-Run"
            print(f"\n📍 STEP 4: {step_name}")
            test_results[step_name] = self.run_migration_dry_run()
            if not test_results[step_name]:
                return False

            # Step 5: Run live migration
            step_name = "Migration Live"
            print(f"\n📍 STEP 5: {step_name}")
            test_results[step_name] = self.run_migration_live()
            if not test_results[step_name]:
                return False

            # Step 6: Validate migration
            step_name = "Validate Migration"
            print(f"\n📍 STEP 6: {step_name}")
            test_results[step_name] = self.validate_migration()
            if not test_results[step_name]:
                return False

            # Step 7: Test embed_entrypoint.py
            step_name = "Test Embed Entrypoint"
            print(f"\n📍 STEP 7: {step_name}")
            test_results[step_name] = self.test_embed_entrypoint()
            if not test_results[step_name]:
                return False

            return True

        finally:
            # Always clean up
            self.cleanup_test_collection()

            # Print final results
            print("\n" + "="*60)
            print("🎯 FINAL TEST RESULTS")
            print("="*60)

            all_passed = True
            for step, passed in test_results.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"{status} {step}")
                if not passed:
                    all_passed = False

            if all_passed:
                print("\n🎉 ALL TESTS PASSED!")
                print("✅ Dry-run validation successful")
            else:
                print("\n❌ SOME TESTS FAILED!")

            print("="*60)

            return all_passed


def check_dependencies():
    """Check that required dependencies are available."""
    print("🔍 Checking dependencies...")

    # Check for required Python packages
    required_packages = [
        "qdrant_client",
        "numpy",
        "PIL",  # Pillow is imported as PIL
        "dotenv"  # python-dotenv for environment loading
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install with: pip install qdrant-client numpy Pillow python-dotenv")
        return False

    # Check for curl (needed for Qdrant API calls)
    try:
        result = subprocess.run(["curl", "--version"], capture_output=True)
        if result.returncode != 0:
            print("❌ curl not found or not working")
            return False
    except FileNotFoundError:
        print("❌ curl not installed (required for Qdrant API calls)")
        return False

    print("✅ All dependencies available")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run complete dry-run and unit tests")
    parser.add_argument("--test-dir",
                       default="/home/quantium/labs/oriane/ExtractionPipeline/qdrant/test",
                       help="Directory containing test scripts")

    args = parser.parse_args()

    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        sys.exit(1)

    # Create orchestrator
    orchestrator = DryRunTestOrchestrator(args.test_dir)

    # Run complete test suite
    success = orchestrator.run_complete_test_suite()

    if success:
        print("\n🎉 COMPLETE TEST SUITE PASSED!")
        sys.exit(0)
    else:
        print("\n❌ COMPLETE TEST SUITE FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
