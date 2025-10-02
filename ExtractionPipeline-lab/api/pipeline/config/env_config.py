from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("api/.env", override=True)


def _env_path(var: str, default: Path) -> Path:
    """Return Path from env-var or default."""
    return Path(os.getenv(var, str(default))).expanduser().resolve()


@dataclass(slots=True, frozen=True)
class Settings:
    # ───────────── API ─────────────────────────────────────────────
    api_name: str = os.getenv("API_NAME", "Oriane Search API")
    api_port: int = int(os.getenv("API_PORT", 8000))
    api_username: str = os.getenv("API_USERNAME", "")
    api_password: str = os.getenv("API_PASSWORD", "")
    api_key: str = os.getenv("API_KEY", "")
    max_videos_per_request: int = int(os.getenv("MAX_VIDEOS_PER_REQUEST", 1000))
    pipeline_max_parallel_jobs: int = int(os.getenv("PIPELINE_MAX_PARALLEL_JOBS", 2))

    # ───────────── Extraction Pipeline  ─────────────────────────────────────────────

    ## ───────────── base root (all artefacts live here) ─────────────
    output_root: Path = _env_path("VP_OUTPUT_DIR", Path(".output"))

    ## ───────────── derived sub-folders (can be overridden) ─────────
    tmp_dir: Path = _env_path("VP_TMP_DIR", output_root / "tmp" / "videos")
    frames_dir: Path = _env_path("VP_FRAMES_DIR", output_root / "tmp" / "frames")
    logs_dir: Path = _env_path("VP_LOGS_DIR", output_root / "logs")
    reports_dir: Path = _env_path("VP_REPORTS_DIR", output_root / "reports")

    ## ───────────── AWS / S3 ─────────────────────────────────────────
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    s3_bucket_name: str = os.getenv("S3_BUCKET_NAME", "oriane-contents")
    s3_app_bucket: str = os.getenv("S3_APP_BUCKET", "oriane-app")
    s3_frames_bucket: str = os.getenv("S3_FRAMES_BUCKET", "oriane-frames")

    ## ───────────── AWS Batch ────────────────────────────────────────
    BATCH_JOB_QUEUE: str = os.getenv("BATCH_JOB_QUEUE", "")
    BATCH_JOB_DEFINITION: str = os.getenv("BATCH_JOB_DEFINITION", "")

    ## ───────────── performance knobs ───────────────────────────────
    sample_fps: float = float(os.getenv("VP_SAMPLE_FPS", 0.1))
    max_workers: int = int(os.getenv("VP_MAX_WORKERS", 4))
    batch_size: int = int(os.getenv("VP_BATCH_SIZE", 8))

    ## ───────────── feature switches ────────────────────────────────
    crop_enabled: bool = os.getenv("VP_ENABLE_CROP", "1") != "0"
    dedup_enabled: bool = os.getenv("VP_ENABLE_DEDUP", "1") != "0"

    ## ───────────── Qdrant / vectors ────────────────────────────────
    qdrant_url: str = os.getenv("QDRANT_URL", "")
    qdrant_key: str = os.getenv("QDRANT_KEY", "")
    collection: str = os.getenv("QDRANT_COLLECTION", "watched_frames")
    dim: int = int(os.getenv("QDRANT_DIM", 512))

    ## ─────────────── ffmpeg cropping knobs ─────────────────────
    crop_probes: int = int(os.getenv("VP_CROP_PROBES", 3))
    crop_clip_secs: int = int(os.getenv("VP_CROP_CLIP_SECS", 2))
    crop_safe_margin: int = int(os.getenv("VP_CROP_SAFE_MARGIN", 4))
    crop_hwaccel: str = os.getenv("VP_CROP_HWACCEL", "cuda")
    crop_detect_args: str = os.getenv("VP_CROP_CROPDETECT", "24:16:0")
    crop_encoder: str = os.getenv("VP_CROP_ENCODER", "h264_nvenc")
    crop_preset: str = os.getenv("VP_CROP_PRESET", "p5")
    crop_tune: str = os.getenv("VP_CROP_TUNE", "hq")
    crop_cq: str = os.getenv("VP_CROP_CQ", "23")
    min_crop_ratio: float = float(os.getenv("VP_MIN_CROP_RATIO", 0.10))
    downscale: float = float(os.getenv("VP_DOWNSCALE", 0.5))

    ## ─────────────── CV thresholds / filters ───────────────────
    scene_thresh: float = float(os.getenv("VP_SCENE_THRESH", 0.22))
    min_frames: int = int(os.getenv("VP_MIN_FRAMES", 3))
    tolerance: int = int(os.getenv("VP_TOLERANCE", 5))
    edge_thresh: int = int(os.getenv("VP_EDGE_THRESH", 10))
    dhash_size: int = int(os.getenv("VP_DHASH_SIZE", 8))
    solid_std_thresh: float = float(os.getenv("VP_SOLID_STD", 5.0))
    solid_min_dim: int = int(os.getenv("VP_SOLID_MIN_DIM", 10))

    ## ───────────── model selection ─────────────────────────────────
    clip_model: str = os.getenv("CLIP_MODEL", "jinaai/jina-clip-v2")

    ## ───────────── CORS ─────────────────────────────────────────────
    cors_origins: list[str] = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(","))

    ## ───────────── create folders eagerly ──────────────────────────
    _dirs: tuple[Path, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_dirs",
            (
                self.output_root,
                self.tmp_dir.parent,  # ensure tmp/ exists
                self.tmp_dir,
                self.frames_dir,
                self.logs_dir,
                self.reports_dir,
            ),
        )
        for d in self._dirs:
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()  # immutable singleton
