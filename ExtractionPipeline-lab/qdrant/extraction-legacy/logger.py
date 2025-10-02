"""
Logging configuration for the extraction pipeline.

This module sets up logging with:
- Rotating file handler for persistent logs
- Rich console output for enhanced terminal display
- Structured logging for batch operations including batch number, DB ID range,
  success/fail counts, and elapsed time
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text


class ExtractionFormatter(logging.Formatter):
    """Custom formatter for extraction pipeline logs."""

    def __init__(self):
        super().__init__()
        self.base_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with extraction-specific information."""
        # Base formatting
        formatted = super().format(record)

        # Add extraction-specific fields if they exist
        if hasattr(record, "batch_number"):
            formatted = f"[Batch {record.batch_number}] {formatted}"

        if hasattr(record, "db_id_range"):
            formatted = f"[IDs {record.db_id_range}] {formatted}"

        if hasattr(record, "success_count") and hasattr(record, "fail_count"):
            formatted = (
                f"{formatted} (Success: {record.success_count}, Failed: {record.fail_count})"
            )

        if hasattr(record, "elapsed_time"):
            formatted = f"{formatted} [Elapsed: {record.elapsed_time:.2f}s]"

        return formatted


class ExtractionLogger:
    """Logger class for the extraction pipeline."""

    def __init__(self, log_level: str = "INFO"):
        """
        Initialize the extraction logger.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_level = getattr(logging, log_level.upper())
        self.logger = logging.getLogger("extraction_pipeline")
        self.logger.setLevel(self.log_level)

        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()

        self.console = Console()
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up file and console handlers."""
        # File handler with rotation
        log_dir = Path("/home/quantium/labs/oriane/ExtractionPipeline/qdrant/scripts/extract/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "extract.log"

        # Rotating file handler (10MB max, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
        )
        file_handler.setLevel(self.log_level)

        # File formatter
        file_formatter = ExtractionFormatter()
        file_formatter.datefmt = "%Y-%m-%d %H:%M:%S"
        file_handler.setFormatter(file_formatter)

        # Rich console handler
        console_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )
        console_handler.setLevel(self.log_level)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_batch_start(self, batch_number: int, db_id_range: str, total_records: int):
        """Log the start of a batch operation."""
        self.logger.info(
            f"Starting batch processing - Total records: {total_records}",
            extra={"batch_number": batch_number, "db_id_range": db_id_range},
        )

    def log_batch_progress(
        self,
        batch_number: int,
        db_id_range: str,
        processed: int,
        total: int,
        success_count: int,
        fail_count: int,
    ):
        """Log batch processing progress."""
        progress_pct = (processed / total) * 100 if total > 0 else 0
        self.logger.info(
            f"Batch progress: {processed}/{total} ({progress_pct:.1f}%)",
            extra={
                "batch_number": batch_number,
                "db_id_range": db_id_range,
                "success_count": success_count,
                "fail_count": fail_count,
            },
        )

    def log_batch_complete(
        self,
        batch_number: int,
        db_id_range: str,
        success_count: int,
        fail_count: int,
        elapsed_time: float,
    ):
        """Log the completion of a batch operation."""
        total_processed = success_count + fail_count
        success_rate = (success_count / total_processed) * 100 if total_processed > 0 else 0

        self.logger.info(
            f"Batch completed - Total processed: {total_processed}, Success rate: {success_rate:.1f}%",
            extra={
                "batch_number": batch_number,
                "db_id_range": db_id_range,
                "success_count": success_count,
                "fail_count": fail_count,
                "elapsed_time": elapsed_time,
            },
        )

    def log_batch_error(
        self,
        batch_number: int,
        db_id_range: str,
        error: str,
        success_count: int = 0,
        fail_count: int = 0,
    ):
        """Log a batch error."""
        self.logger.error(
            f"Batch failed: {error}",
            extra={
                "batch_number": batch_number,
                "db_id_range": db_id_range,
                "success_count": success_count,
                "fail_count": fail_count,
            },
        )

    def log_extraction_stats(self, stats: Dict[str, Any]):
        """Log overall extraction statistics."""
        self.logger.info(f"Extraction statistics: {stats}", extra={"extraction_stats": stats})

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, extra=kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, extra=kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, extra=kwargs)


# Global logger instance
extraction_logger = None


def get_logger(log_level: str = "INFO") -> ExtractionLogger:
    """
    Get the global extraction logger instance.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        ExtractionLogger instance
    """
    global extraction_logger
    if extraction_logger is None:
        extraction_logger = ExtractionLogger(log_level)
    return extraction_logger


def setup_logging(log_level: str = "INFO") -> ExtractionLogger:
    """
    Set up logging for the extraction pipeline.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        ExtractionLogger instance
    """
    return get_logger(log_level)


# Example usage context manager for batch operations
class BatchContext:
    """Context manager for batch operations with automatic logging."""

    def __init__(
        self,
        batch_number: int,
        db_id_range: str,
        total_records: int,
        logger: Optional[ExtractionLogger] = None,
    ):
        """
        Initialize batch context.

        Args:
            batch_number: Batch number
            db_id_range: Database ID range being processed
            total_records: Total number of records in batch
            logger: Logger instance (uses global if None)
        """
        self.batch_number = batch_number
        self.db_id_range = db_id_range
        self.total_records = total_records
        self.logger = logger or get_logger()
        self.success_count = 0
        self.fail_count = 0
        self.start_time = None

    def __enter__(self):
        """Enter batch context."""
        self.start_time = datetime.now()
        self.logger.log_batch_start(self.batch_number, self.db_id_range, self.total_records)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit batch context."""
        elapsed_time = (datetime.now() - self.start_time).total_seconds()

        if exc_type is not None:
            error_msg = f"{exc_type.__name__}: {exc_val}"
            self.logger.log_batch_error(
                self.batch_number, self.db_id_range, error_msg, self.success_count, self.fail_count
            )
        else:
            self.logger.log_batch_complete(
                self.batch_number,
                self.db_id_range,
                self.success_count,
                self.fail_count,
                elapsed_time,
            )

    def record_success(self):
        """Record a successful operation."""
        self.success_count += 1

    def record_failure(self):
        """Record a failed operation."""
        self.fail_count += 1

    def log_progress(self, processed: int):
        """Log current progress."""
        self.logger.log_batch_progress(
            self.batch_number,
            self.db_id_range,
            processed,
            self.total_records,
            self.success_count,
            self.fail_count,
        )


if __name__ == "__main__":
    # Example usage
    logger = setup_logging("DEBUG")

    # Example batch operation
    with BatchContext(1, "1-1000", 1000, logger) as batch:
        logger.info("Processing batch...")

        # Simulate some processing
        for i in range(10):
            if i % 3 == 0:
                batch.record_failure()
            else:
                batch.record_success()

            if i % 5 == 0:
                batch.log_progress(i + 1)

    logger.info("Extraction pipeline completed")
