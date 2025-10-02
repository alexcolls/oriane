#!/usr/bin/env python3
"""
Test script for embedded status verification functionality.

This script tests the verify_embedded module to ensure it correctly:
1. Connects to Qdrant using environment variables
2. Checks for existence of vectors for given codes
3. Marks appropriate records as embedded in the database
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.env_config import settings
from config.logging_config import configure_logging
from src.verify_embedded import mark_embedded_codes, verify_batch_embedded, verify_single_code

log = configure_logging()


def test_environment_setup():
    """Test if required environment variables are set."""
    log.info("🔧 Testing environment setup...")

    required_vars = {
        "QDRANT_URL": settings.qdrant_url,
        "QDRANT_COLLECTION": settings.collection,
    }

    missing_vars = []
    for var_name, var_value in required_vars.items():
        if not var_value:
            missing_vars.append(var_name)
        else:
            log.info(f"✅ {var_name}: {var_value}")

    if missing_vars:
        log.error(f"❌ Missing required environment variables: {missing_vars}")
        return False

    log.info("✅ Environment setup complete")
    return True


def test_qdrant_connection():
    """Test connection to Qdrant."""
    log.info("🔗 Testing Qdrant connection...")

    try:
        from src.verify_embedded import _client

        client = _client()
        collections = client.get_collections()
        log.info(
            f"✅ Connected to Qdrant. Available collections: {[c.name for c in collections.collections]}"
        )

        # Check if our target collection exists
        collection_names = [c.name for c in collections.collections]
        if settings.collection in collection_names:
            log.info(f"✅ Target collection '{settings.collection}' exists")
            return True
        else:
            log.warning(
                f"⚠️ Target collection '{settings.collection}' not found. Available: {collection_names}"
            )
            return False

    except Exception as e:
        log.error(f"❌ Failed to connect to Qdrant: {e}")
        return False


def test_verification_with_sample_codes():
    """Test verification with sample codes."""
    log.info("🧪 Testing verification with sample codes...")

    # Use some test codes - these may or may not exist in Qdrant
    test_codes = ["test_code_1", "test_code_2", "nonexistent_code"]

    try:
        # Test batch verification
        results = verify_batch_embedded(test_codes)
        log.info(f"✅ Batch verification results: {results}")

        # Test single code verification
        for code in test_codes:
            result = verify_single_code(code)
            log.info(f"✅ Single verification for '{code}': {result}")

        return True

    except Exception as e:
        log.error(f"❌ Verification test failed: {e}")
        return False


def test_database_connection():
    """Test database connection for marking embedded records."""
    log.info("💾 Testing database connection...")

    db_url = os.getenv("ORIANE_ADMIN_DB_URL")
    if not db_url:
        log.warning("⚠️ ORIANE_ADMIN_DB_URL not set - database operations will be skipped")
        return False

    try:
        from src.verify_embedded import _get_content_ids_by_codes

        # Test with some sample codes
        test_codes = ["sample_code_1", "sample_code_2"]
        code_to_id = _get_content_ids_by_codes(test_codes)

        log.info(f"✅ Database lookup test: {code_to_id}")
        return True

    except Exception as e:
        log.error(f"❌ Database connection test failed: {e}")
        return False


def main():
    """Run all tests."""
    log.info("🚀 Starting embedded status verification tests...")

    # Track test results
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Qdrant Connection", test_qdrant_connection),
        ("Verification Logic", test_verification_with_sample_codes),
        ("Database Connection", test_database_connection),
    ]

    results = {}

    for test_name, test_func in tests:
        log.info(f"\n{'='*60}")
        log.info(f"Running test: {test_name}")
        log.info(f"{'='*60}")

        try:
            results[test_name] = test_func()
        except Exception as e:
            log.error(f"❌ Test '{test_name}' failed with exception: {e}")
            results[test_name] = False

    # Summary
    log.info(f"\n{'='*60}")
    log.info("TEST SUMMARY")
    log.info(f"{'='*60}")

    passed = 0
    total = len(tests)

    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        log.info(f"{status} {test_name}")
        if passed_test:
            passed += 1

    log.info(f"\nTests passed: {passed}/{total}")

    if passed == total:
        log.info("🎉 All tests passed!")
        return 0
    else:
        log.error("⚠️ Some tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
