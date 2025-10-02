import json
import logging
import sys
import time
from pathlib import Path

from config.env_config import settings
from rich.logging import RichHandler

LOG_FILE = settings.logs_dir / f"run-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
LOG_FILE.parent.mkdir(exist_ok=True, parents=True)

_FMT_RICH = "%(message)s"
_FMT_FILE = json.dumps(
    {"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "msg": "%(message)s"}
)


def configure_logging(level: str = "INFO") -> logging.Logger:
    logging.basicConfig(
        level=level,
        format=_FMT_RICH,
        handlers=[
            RichHandler(rich_tracebacks=True, markup=True, show_path=False),
            logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
        ],
    )
    # override file handler to write JSONL
    for h in logging.getLogger().handlers:
        if isinstance(h, logging.FileHandler):
            h.setFormatter(logging.Formatter(_FMT_FILE, "%Y-%m-%dT%H:%M:%S"))
    return logging.getLogger("video-pipeline")
