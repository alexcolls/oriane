# 🧪 API Scripts Documentation

This directory contains helpful scripts for running tests and starting the API server.

## Scripts Overview

### 🧪 `run-tests.sh` - Test Runner

A comprehensive test runner with beautiful emoji logging and detailed reporting.

**Features:**
- ✅ Runs all test suites individually and provides detailed feedback
- 🎨 Beautiful colored output with emojis
- 📊 Comprehensive test summary with pass/fail/skip counts
- ⏱️ Execution time tracking
- 📝 Saves detailed logs with timestamps
- 🔍 Automatic dependency checking
- 📁 Test asset validation

**Usage:**
```bash
# Run all tests
./run-tests.sh
```

**Example Output:**
```
🧪 ORIANE API TEST SUITE
═══════════════════════════════════════════
Starting comprehensive test run...

🔧 Checking environment...
✅ Virtual environment already active
✅ All test assets found

🏃 RUNNING INDIVIDUAL TEST SUITES
🔐 Running Authentication Unit Tests...
✅ Authentication Unit Tests passed!

📊 Results:
✅ Passed: 62
Failed: 0
⚠️  Skipped: 2
📈 Total: 64 tests
⏱️  Duration: 121s

🎉 ALL TESTS PASSED! 🎉
Ready for deployment! 🚀
```

### 🚀 `run.sh` - Server Runner

Runs tests and starts the FastAPI development server.

**Features:**
- 🧪 Automatically runs tests before starting server
- 🚀 Starts FastAPI server with auto-reload
- ⚠️ Optional test skipping for quick development
- 🎨 Colored output with helpful information

**Usage:**
```bash
# Run tests then start server (recommended)
./run.sh

# Start server without running tests (for quick development)
./run.sh --skip-tests
```

**What it does:**
1. Activates the virtual environment
2. Runs the complete test suite (unless `--skip-tests` is used)
3. Starts the FastAPI server on `http://localhost:8000`
4. Enables auto-reload for development

## Test Structure

The test runner executes these test suites:

### 🔐 Authentication Unit Tests (`test_auth.py`)
- Basic authentication functions
- API key validation
- Credential verification

### 🔗 Authentication Integration Tests (`test_auth_integration.py`)
- Full authentication flows
- HTTP header validation
- Cross-authentication scenarios
- Edge cases and error handling

### 🛡️ API Endpoint Authentication Tests (`test_api_endpoints_auth.py`)
- Real endpoint authentication
- API key enforcement
- Mixed authentication scenarios

### 📁 Add Content Endpoint Tests (`test_add_content.py`)
- Image upload functionality
- Video upload functionality
- Batch upload operations
- File validation and error handling
- S3 integration testing

## Test Assets

The tests use real assets located in `tests/assets/`:
- `image.png` - PNG image for testing
- `image.jpeg` - JPEG image for testing (with conversion)
- `video.mp4` - Video file for testing

## Development Workflow

### For Development:
```bash
# Quick start (skip tests for faster iteration)
./run.sh --skip-tests
```

### For Testing:
```bash
# Run only tests
./run-tests.sh
```

### For Deployment:
```bash
# Full validation before deployment
./run.sh
```

## Logs and Output

### Test Logs
- Detailed test results are saved to `test-results-YYYYMMDD-HHMMSS.log`
- Logs include full pytest output for debugging

### Console Output
- Real-time colored output with emojis
- Progress indicators for each test suite
- Comprehensive summary with statistics

## Troubleshooting

### Virtual Environment Issues
If you see virtual environment errors:
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Missing Test Assets
If test assets are missing:
```bash
# The script will warn you and create the directory
# Add your test files to tests/assets/
```

### Test Failures
- Review the detailed log file for specific error messages
- Check the colored console output for quick failure identification
- Fix failing tests before deployment

## Environment Requirements

- Python 3.12+
- Virtual environment (`.venv`)
- Test dependencies (pytest, fastapi, etc.)
- Test assets in `tests/assets/`

## Script Permissions

Make sure scripts are executable:
```bash
chmod +x run-tests.sh run.sh
```

---

**Happy Testing! 🧪✨**
