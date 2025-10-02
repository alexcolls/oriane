#!/usr/bin/env python3
"""
Test script to validate the FastAPI app implementation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required imports work correctly."""
    try:
        from auth.apikey import verify_api_key
        from config.env_config import settings
        from controllers.jobs import router as jobs_router
        from main import app
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_configuration():
    """Test that the app is configured correctly."""
    try:
        from main import app
        from config.env_config import settings
        
        # Test app title
        expected_title = settings.api_name + " Pipeline"
        assert app.title == expected_title, f"Expected title '{expected_title}', got '{app.title}'"
        
        # Test that router is included
        job_routes = [route for route in app.routes if hasattr(route, 'path') and route.path.startswith('/jobs')]
        assert len(job_routes) > 0, "Jobs router not found in app routes"
        
        print("✅ App configuration tests passed")
        return True
    except Exception as e:
        print(f"❌ App configuration test failed: {e}")
        return False

def test_authentication():
    """Test that authentication dependency is correctly configured."""
    try:
        from auth.apikey import verify_api_key
        from main import app
        
        # Check that routes have the authentication dependency
        job_routes = [route for route in app.routes if hasattr(route, 'path') and route.path.startswith('/jobs')]
        for route in job_routes:
            if hasattr(route, 'dependencies'):
                dependency_found = any(
                    str(dep).find('verify_api_key') >= 0 
                    for dep in route.dependencies
                )
                assert dependency_found, f"verify_api_key dependency not found in route {route.path}"
        
        print("✅ Authentication tests passed")
        return True
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def test_cors_configuration():
    """Test that CORS is configured correctly."""
    try:
        from main import app
        from config.env_config import settings
        
        # Check CORS middleware
        cors_middleware = None
        for middleware in app.user_middleware:
            if 'CORSMiddleware' in str(middleware.cls):
                cors_middleware = middleware
                break
        
        assert cors_middleware is not None, "CORS middleware not found"
        print("✅ CORS configuration tests passed")
        return True
    except Exception as e:
        print(f"❌ CORS configuration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Running FastAPI Pipeline implementation tests...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_app_configuration,
        test_authentication,
        test_cors_configuration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
        print()
    
    print("=" * 50)
    print(f"Tests completed: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Implementation is correct.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
