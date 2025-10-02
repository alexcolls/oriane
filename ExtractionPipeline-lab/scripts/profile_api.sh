#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# Start the API in the background
uvicorn api.pipeline.src.api.app:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for the API to be ready
sleep 5

# Send a request to the API
curl -X POST -H "Content-Type: application/json" -H "X-API-Key: test-key" -d '{
  "items": [
    {
      "platform": "youtube",
      "code": "dQw4w9WgXcQ"
    }
  ]
}' http://localhost:8000/jobs

# Run the performance tests
python3 -m pyinstrument -r html -o artifacts/profiles/baseline.html -m pytest tests/perf/test_large_job.py

# Stop the API
kill $API_PID

