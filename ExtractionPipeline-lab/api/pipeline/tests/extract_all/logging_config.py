#!/usr/bin/env python3
"""
Centralized logging configuration with RotatingFileHandler and stdout streaming.
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


class LoggingConfig:
    """Centralized logging configuration manager."""
    
    def __init__(self, log_level: str = 'INFO', log_dir: str = './logs'):
        self.log_level = getattr(logging, log_level.upper())
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging with both file and console handlers."""
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear any existing handlers
        root_logger.handlers.clear()
        
        # Console handler (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / 'application.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Error log file handler
        error_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / 'errors.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
        
        # Set up specific loggers for different modules
        self._setup_module_loggers()
    
    def _setup_module_loggers(self):
        """Set up specific loggers for different modules."""
        
        # API client logger
        api_logger = logging.getLogger('api_client')
        api_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / 'api_client.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        api_handler.setLevel(logging.DEBUG)
        api_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        ))
        api_logger.addHandler(api_handler)
        
        # Job monitor logger
        job_logger = logging.getLogger('job_monitor')
        job_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / 'job_monitor.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        job_handler.setLevel(logging.DEBUG)
        job_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        ))
        job_logger.addHandler(job_handler)
        
        # S3 utils logger
        s3_logger = logging.getLogger('s3_utils')
        s3_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / 's3_utils.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        s3_handler.setLevel(logging.DEBUG)
        s3_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        ))
        s3_logger.addHandler(s3_handler)
        
        # Qdrant utils logger
        qdrant_logger = logging.getLogger('qdrant_utils')
        qdrant_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / 'qdrant_utils.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        qdrant_handler.setLevel(logging.DEBUG)
        qdrant_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        ))
        qdrant_logger.addHandler(qdrant_handler)
        
        # State manager logger
        state_logger = logging.getLogger('state')
        state_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / 'state_manager.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        state_handler.setLevel(logging.DEBUG)
        state_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        ))
        state_logger.addHandler(state_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the given name."""
        return logging.getLogger(name)
    
    def set_level(self, level: str):
        """Set the logging level for all handlers."""
        new_level = getattr(logging, level.upper())
        root_logger = logging.getLogger()
        root_logger.setLevel(new_level)
        
        for handler in root_logger.handlers:
            handler.setLevel(new_level)
    
    @staticmethod
    def setup_basic_logging(log_level: str = 'INFO', log_dir: str = './logs'):
        """Set up basic logging configuration."""
        return LoggingConfig(log_level, log_dir)
