import pytest
import requests


def test_large_job():
    # This test assumes the API is running at http://localhost:8000
    # and that the API key is set to \"test-key\"
    # It also assumes that the test is run from the root of the project
    # so that the test data can be found.

    # Create a large job
    large_job = {
        "items": [
            {
                "platform": "youtube",
                "code": f"video_{i}"
            } for i in range(100)
        ]
    }

    # Send the job to the API
    response = requests.post(
        "http://localhost:8000/jobs",
        json=large_job,
        headers={
            "X-API-Key": "test-key"
        }
    )

    # Check that the job was created successfully
    assert response.status_code == 202

