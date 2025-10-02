#!/usr/bin/env python3
"""
Configuration loader with environment variables and defaults.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Settings:
    """Configuration management with .env file support and typed getters."""
    
    def __init__(self):
        """Initialize configuration by loading from ../../../.env file."""
        # Load .env file from ../../../.env relative to this file
        env_path = Path(__file__).parent / "../../../.env"
        
        if env_path.exists():
            load_dotenv(env_path)
        else:
            # Try alternative path if the expected one doesn't exist
            alt_env_path = Path(__file__).parent / "../../.env"
            if alt_env_path.exists():
                load_dotenv(alt_env_path)
    
    def get_aws_access_key_id(self) -> Optional[str]:
        """Get AWS access key ID."""
        return os.getenv('AWS_ACCESS_KEY_ID')
    
    def get_aws_secret_access_key(self) -> Optional[str]:
        """Get AWS secret access key."""
        return os.getenv('AWS_SECRET_ACCESS_KEY')
    
    def get_aws_region(self) -> str:
        """Get AWS region."""
        return os.getenv('AWS_REGION', 'us-east-1')
    
    def get_qdrant_url(self) -> Optional[str]:
        """Get Qdrant URL."""
        return os.getenv('QDRANT_URL')
    
    def get_qdrant_key(self) -> Optional[str]:
        """Get Qdrant API key."""
        return os.getenv('QDRANT_KEY')
    
    def get_qdrant_collection(self) -> str:
        """Get Qdrant collection name."""
        return os.getenv('QDRANT_COLLECTION', 'watched_frames')
    
    def get_s3_bucket(self) -> Optional[str]:
        """Get S3 bucket name."""
        return os.getenv('S3_FRAMES_BUCKET') or os.getenv('S3_VIDEOS_BUCKET')
    
    def get_s3_prefix(self) -> str:
        """Get S3 prefix."""
        return os.getenv('S3_PREFIX', '')
    
    def get_pipeline_api_url(self) -> Optional[str]:
        """Get Pipeline API URL."""
        return os.getenv('PIPELINE_API_URL')
    
    def get_api_key(self) -> Optional[str]:
        """Get API key."""
        return os.getenv('API_KEY')
    
    def get_batch_limit(self) -> int:
        """Get batch limit with default of 100."""
        return int(os.getenv('BATCH_LIMIT', '100'))
    
    def get_status_interval(self) -> int:
        """Get status interval in seconds with default of 60."""
        return int(os.getenv('STATUS_INTERVAL', '60'))
    
    def get_http_timeout(self) -> int:
        """Get HTTP timeout in seconds with default of 15."""
        return int(os.getenv('HTTP_TIMEOUT', '15'))
    
    @property
    def aws_credentials(self) -> dict:
        """Get AWS credentials as a dictionary for boto3."""
        return {
            'aws_access_key_id': self.get_aws_access_key_id(),
            'aws_secret_access_key': self.get_aws_secret_access_key(),
            'region_name': self.get_aws_region()
        }


class Config:
    """Configuration wrapper for the extraction pipeline."""
    
    def __init__(self, env_file=None, limit=None, interval=None, timeout=None, log_level=None):
        """Initialize configuration."""
        self.settings = Settings()
        
        # Override with CLI arguments if provided
        self.limit = limit or self.settings.get_batch_limit()
        self.interval = interval or self.settings.get_status_interval()
        self.timeout = timeout or self.settings.get_http_timeout()
        self.log_level = log_level or 'INFO'
        
        # State file paths in working directory
        self.state_file = Path('./state.json')
        self.processed_file = Path('./processed.json')
        self.pending_file = Path('./pending.json')
        
        # Directory paths for responses and logs
        self.responses_dir = Path('./responses')
        self.logs_dir = Path('./logs')
        
        # AWS and API settings
        self.aws_credentials = self.settings.aws_credentials
        self.aws_access_key_id = self.settings.get_aws_access_key_id()
        self.aws_secret_access_key = self.settings.get_aws_secret_access_key()
        self.aws_region = self.settings.get_aws_region()
        self.s3_bucket = self.settings.get_s3_bucket()
        self.s3_prefix = self.settings.get_s3_prefix()
        self.pipeline_api_url = self.settings.get_pipeline_api_url()
        self.api_key = self.settings.get_api_key()
        self.qdrant_url = self.settings.get_qdrant_url()
        self.qdrant_key = self.settings.get_qdrant_key()
        self.qdrant_collection = self.settings.get_qdrant_collection()
        self.batch_limit = self.settings.get_batch_limit()


# Expose a single settings object for other modules
settings = Settings()
