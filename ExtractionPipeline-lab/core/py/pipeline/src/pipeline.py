from __future__ import annotations

import hashlib
import math
import re
import time
import uuid
from pathlib import Path
from typing import List

import src.border_cropping as border_cropping
import src.deduplicate_frames as deduplicate_frames
import src.infer_embeds as infer_embeds
import src.scene_framing as scene_framing
import src.store_embeds as store_embeds
import src.upload_frames as upload_frames
from config.env_config import settings
from config.logging_config import configure_logging
from config.profiler import profile

log = configure_logging()
_FRAME_RE = re.compile(r"^(?P<idx>\d+)_(?P<sec>\d+\.\d+)\.png$")


class VideoPipeline:
    """Process one video through the 5 logical stages (with optional 1 & 3)."""

    # ─────────────────── orchestrator ────────────────────
    @profile
    def run(self, video: Path) -> None:
        t0 = time.perf_counter()
        log.info(f"[vid] ▶ {video.name}")

        # Track progress through pipeline stages
        total_steps = 5
        current_step = 0

        def log_step_start(step_name: str, step_num: int, details: str = ""):
            progress_pct = (step_num / total_steps) * 100
            details_str = f" | {details}" if details else ""
            step_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
            step_emoji = step_emojis[step_num - 1] if step_num <= len(step_emojis) else "🔢"
            log.info(f"{step_emoji} 🔄 {step_name} ({progress_pct:.0f}%){details_str}")

        def log_step_success(step_name: str, step_num: int, details: str = ""):
            progress_pct = (step_num / total_steps) * 100
            details_str = f" | {details}" if details else ""
            step_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
            step_emoji = step_emojis[step_num - 1] if step_num <= len(step_emojis) else "🔢"
            log.info(f"{step_emoji} ✅ {step_name} complete ({progress_pct:.0f}%){details_str}")

        def log_step_skip(step_name: str, step_num: int, reason: str = ""):
            progress_pct = (step_num / total_steps) * 100
            reason_str = f" | {reason}" if reason else ""
            step_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
            step_emoji = step_emojis[step_num - 1] if step_num <= len(step_emojis) else "🔢"
            log.info(f"{step_emoji} ⏭️ {step_name} skipped ({progress_pct:.0f}%){reason_str}")

        # ---------- Phase 1: crop (optional) ----------
        current_step += 1
        if settings.crop_enabled:
            log_step_start("border cropping", current_step)
            work_clip = settings.tmp_dir / video.name
            border_cropping.crop_video(video, work_clip)
            log_step_success("border cropping", current_step)
        else:
            log_step_skip("border cropping", current_step, "VP_ENABLE_CROP=0")
            work_clip = video

        # ---------- Phase 2: scene extraction ----------
        current_step += 1
        log_step_start("scene extraction", current_step)
        frame_dir = settings.frames_dir / video.stem
        frames = scene_framing.extract_frames(work_clip, frame_dir)

        if not frames:
            log.warning(f"⚠️ [vid] {video.name}: 0 candidate frames – skipping")
            return
        log_step_success("scene extraction", current_step, f"{len(frames)} frames")

        # ---------- Phase 3: deduplicate (optional) ----------
        current_step += 1
        if settings.dedup_enabled:
            log_step_start("frame deduplication", current_step, f"{len(frames)} frames")
            frames = deduplicate_frames.remove_duplicates(frames)
            log_step_success("frame deduplication", current_step, f"{len(frames)} frames kept")
        else:
            log_step_skip("frame deduplication", current_step, "VP_ENABLE_DEDUP=0")

        if not frames:
            log.warning(f"⚠️ [vid] {video.name}: 0 frames after dedup – skipping")
            return

        # ─── kick-off asynchronous S3 upload ───
        current_step += 1
        log_step_start("S3 upload (async)", current_step, f"{len(frames)} frames")
        upload_frames.upload_frames_async(
            frames,
            platform="instagram",  # or pass variable if you ingest other platforms
            code=video.stem,  # video.stem == the IG shortcode
            max_workers=settings.max_workers,  # reuse same thread count
        )
        log_step_success("S3 upload (async)", current_step, "initiated")

        # ---------- Phase 4: CLIP embeddings (sequential batches) ----------
        current_step += 1
        log_step_start("CLIP embeddings", current_step, f"{len(frames)} frames")
        vectors = self._encode_frames_in_batches(frames)
        log_step_success("CLIP embeddings", current_step, f"{len(vectors)} vectors")

        # ---------- Phase 5: Qdrant upsert ----------
        current_step += 1
        log_step_start("Qdrant upsert", current_step, f"{len(vectors)} vectors")
        store_embeds.upsert_embeddings(self._make_points(video, frames, vectors))
        log_step_success("Qdrant upsert", current_step, f"{len(vectors)} vectors stored")

        duration = time.perf_counter() - t0
        log.info(f"[vid] ✅ {video.name} done in {duration:.1f}s  " f"(frames={len(frames)})")

    # ─────────────────── resource throttling helpers ─────────────────────────
    def _encode_frames_in_batches(
        self,
        frames: List[Path],
        batch_size: int = None,
        sleep_between_batches: float = None,
    ) -> List[List[float]]:
        """
        Process frames in sequential batches to avoid GPU/memory exhaustion.

        Args:
            frames: List of frame paths to encode
            batch_size: Frames per batch (defaults to settings.batch_size)
            sleep_between_batches: Seconds to sleep between batches

        Returns:
            List of embedding vectors in same order as input frames
        """
        if not frames:
            return []

        batch_size = batch_size or settings.batch_size
        sleep_between_batches = sleep_between_batches or settings.sleep_between_batches
        total_frames = len(frames)
        num_batches = math.ceil(total_frames / batch_size)

        log.info(
            f"[embed] Processing {total_frames} frames in {num_batches} sequential batches "
            f"(batch_size={batch_size}, sleep={sleep_between_batches}s)"
        )

        all_vectors = []

        for batch_idx in range(num_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_frames)
            batch_frames = frames[start_idx:end_idx]

            batch_progress = ((batch_idx + 1) / num_batches) * 100
            log.info(
                f"[embed] Processing batch {batch_idx + 1}/{num_batches} "
                f"({len(batch_frames)} frames, {batch_progress:.1f}%)"
            )

            # Process this batch with internal parallelism handled by infer_embeds
            batch_vectors = infer_embeds.encode_image_batch(
                batch_frames, batch_size=batch_size  # This controls internal parallelism
            )

            all_vectors.extend(batch_vectors)

            # Sleep between batches to allow GPU/memory recovery
            if batch_idx < num_batches - 1:  # Don't sleep after last batch
                log.debug(f"[embed] Sleeping {sleep_between_batches}s before next batch...")
                time.sleep(sleep_between_batches)

        log.info(f"[embed] Completed sequential processing of {len(all_vectors)} vectors")
        return all_vectors

    # ─────────────────── helper ─────────────────────────
    def _make_points(
        self,
        video: Path,
        frames: List[Path],
        vectors: List[List[float]],
        platform: str = "instagram",
    ) -> List[dict]:
        """Prepare Qdrant points with deterministic SHA-1 IDs."""
        items = []
        for fp, vec in zip(frames, vectors, strict=True):
            m = _FRAME_RE.match(fp.name)
            if not m:  # should never happen with our naming
                continue
            idx = int(m["idx"])
            sec = float(m["sec"])
            sha = hashlib.sha1(f"{video.stem}:{idx}".encode()).hexdigest()
            point_id = str(uuid.UUID(sha[:32]))  # RFC-4122, deterministic
            items.append(
                {
                    "id": point_id,
                    "vector": vec,
                    "payload": {
                        "platform": platform,
                        "video_code": video.stem,
                        "frame_number": idx,
                        "frame_second": sec,
                        "path": f"{settings.s3_frames_bucket}/{str(fp.relative_to(settings.frames_dir))}",
                    },
                }
            )
        return items
