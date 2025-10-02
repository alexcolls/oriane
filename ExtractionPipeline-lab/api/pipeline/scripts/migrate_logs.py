import json
from pathlib import Path

# Path to the file containing job data (for demonstration)
JOB_DATA_PATH = Path('path_to_job_data.json')


def migrate_logs(file_path):
    """
    Migrate old log entries from string format to a list of structured LogEntry objects.

    This function will modify job data stored in JSON format, updating any fields named
    'log' (a string) to 'logs' (a list of structured log entries), if applicable.
    """
    # Load the job data
    job_data = json.loads(file_path.read_text()) if file_path.exists() else {}

    # Traverse each job entry and convert logs if needed
    for job_id, job_info in job_data.items():
        # Example log string format (backward compatibility)
        if 'log' in job_info:
            # Create a structured log entry list
            logs = [{
                'ts': '2023-10-01T00:00:00',  # Placeholder timestamp
                'level': 'INFO',  # Placeholder level
                'msg': job_info['log']  # Original log message
            }]
            job_info['logs'] = logs  # Replace with structured logs
            del job_info['log']  # Remove old log key

    # Write the updated job data back to file
    file_path.write_text(json.dumps(job_data, indent=2))


if __name__ == '__main__':
    migrate_logs(JOB_DATA_PATH)
    print(f'Completed log migration for jobs in {JOB_DATA_PATH}')
