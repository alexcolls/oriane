# Oriane Pipeline Test

This repository contains an end-to-end test script for the Oriane pipeline API that submits jobs, polls for completion, and reports progress.

**Author:** Alex Colls

## Prerequisites

- **Python 3**: The script requires Python 3 to run. Make sure you have `python3` installed on your system.
- **Network access**: The script needs internet connectivity to communicate with the Oriane pipeline API.

## Configuration

### Environment Variables

The test script uses environment variables defined in the `.env` file. To configure the test:

1. **Edit the `.env` file** in the project root directory:
   ```bash
   nano .env
   ```

2. **Configure the following variables**:
   ```
   API_URL=https://pipeline.api.qdrant.admin.oriane.xyz
   API_KEY=your-actual-api-key-here
   ```

   - `API_URL`: The base URL for the Oriane pipeline API
   - `API_KEY`: Your authentication key for the API

3. **Save and close** the file after making your changes.

## Running the Test

Execute the test using the provided bash script:

```bash
./run_test.sh
```

The script will:
- Automatically install required Python dependencies (`python-dotenv`, `requests`)
- Load environment variables from the `.env` file
- Execute the end-to-end test

## Expected Console Output

When you run the test, you should see output similar to:

```
[2024-01-15 10:30:45] Starting end-to-end pipeline test
[2024-01-15 10:30:45] Using API URL: https://pipeline.api.qdrant.admin.oriane.xyz
[2024-01-15 10:30:45] Loaded payload with 2 items
[2024-01-15 10:30:45] Submitting job to https://pipeline.api.qdrant.admin.oriane.xyz/process
[2024-01-15 10:30:46] Job submitted successfully. Job ID: job-abc123def456
[2024-01-15 10:30:46] Starting to poll job status for job ID: job-abc123def456
[2024-01-15 10:30:46] Job status: PROCESSING | progress 0%
[2024-01-15 10:30:56] Job status: PROCESSING | progress 25%
[2024-01-15 10:31:06] Job status: PROCESSING | progress 50%
[2024-01-15 10:31:16] Job status: PROCESSING | progress 75%
[2024-01-15 10:31:26] Job status: PROCESSING | progress 100%
[2024-01-15 10:31:36] Job status: COMPLETED | progress 100%
[2024-01-15 10:31:36] SUCCESS: Job completed successfully!
[2024-01-15 10:31:36] Test completed successfully!
```

### Success Indicators

- ✅ **Successful submission**: Job ID is returned after submission
- ✅ **Progress updates**: Regular status updates with increasing progress percentages
- ✅ **Completion**: Final status shows "COMPLETED" with "SUCCESS" message

### Error Scenarios

If you encounter errors, the output might show:

```
[2024-01-15 10:30:45] ERROR: Missing API_URL or API_KEY environment variables
```
→ Check your `.env` file configuration

```
[2024-01-15 10:30:45] ERROR: JSON payload file not found at /home/quantium/oriane_pipeline_test/input-payload.json
```
→ Ensure the input payload file exists

```
[2024-01-15 10:30:46] ERROR: Failed to submit job. Status: 401
```
→ Check your API key is correct and valid

```
[2024-01-15 10:35:46] TIMEOUT: Job polling timed out after 30 minutes
```
→ The job took longer than expected; check API status or increase timeout

## File Structure

```
oriane_pipeline_test/
├── .env                    # Environment configuration
├── README.md              # This documentation
├── run_test.sh            # Test execution script
├── test_script.py         # Main test logic
└── input-payload.json     # Test data payload
```
