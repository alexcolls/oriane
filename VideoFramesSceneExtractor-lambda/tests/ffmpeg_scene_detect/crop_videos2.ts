#!/usr/bin/env ts-node
/* -----------------------------------------------------------
 *  Fast MP4 auto-cropper using only FFmpeg’s cropdetect
 *  No OpenCV, no native modules – portable & bun-friendly
 * --------------------------------------------------------- */

import { spawnSync } from "child_process";
import path from "path";
import fg   from "fast-glob";
import fs   from "fs/promises";
import os   from "os";

/* ─────── CONFIG ─────── */
const CFG = {
  INPUT_DIR  : "../videos",       // source MP4s
  OUTPUT_DIR : "cropped_videos_bun",  // destination
  // cropdetect args → limit:round:reset
  // 24 = ignore up to ~9 % brightness difference
  CROPDETECT : "24:16:0",
  SAMPLE_FRAMES : 150,            // analyse this many frames (~5 s @30 fps)
  CONCURRENCY   : Math.max(os.cpus().length - 1, 1),
};
/* ────────────────────── */

function sh(cmd: string, args: string[], inherit = false) {
  const opts = inherit ? { stdio: "inherit" } : { encoding: "utf8" };
  const { status, stdout, stderr } = spawnSync(cmd, args, opts as any);
  if (status !== 0) throw new Error(stderr.toString().trim());
  return stdout.toString();
}

/** Run cropdetect and return e.g. "crop=1920:804:0:138" or `null`. */
function detectCrop(src: string): string | null {
  const out = sh("ffmpeg", [
    "-v", "error",
    "-i", src,
    "-vf", `cropdetect=${CFG.CROPDETECT}`,
    "-frames:v", String(CFG.SAMPLE_FRAMES),
    "-f", "null", "-"            // discard output
  ]);
  const match = out.match(/crop=(\\S+)/);
  return match ? match[1] : null;
}

async function processFile(src: string) {
  const base = path.basename(src);
  const dst  = path.join(CFG.OUTPUT_DIR, base);
  process.stdout.write(`→ ${base}  `);

  const crop = detectCrop(src);

  if (!crop) {
    // Nothing to trim – copy straight through
    await fs.copyFile(src, dst);
    console.log("no crop, copied");
    return;
  }

  process.stdout.write(`crop=${crop}  `);

  // Apply the crop in a second pass (video re-encode, audio copy)
  sh("ffmpeg", [
    "-hide_banner", "-loglevel", "error",
    "-i", src,
    "-vf", `crop=${crop}`,
    "-c:v", "libx264", "-crf", "18",   // visually lossless H.264
    "-c:a", "copy",
    dst
  ], true);

  console.log("done");
}

(async () => {
  await fs.mkdir(CFG.OUTPUT_DIR, { recursive: true });
  const files = await fg("*.mp4", { cwd: CFG.INPUT_DIR, absolute: true });

  const running: Promise<void>[] = [];

  for (const f of files) {
    const job = processFile(f).then(() => {
      // drop the completed job from the pool
      running.splice(running.indexOf(job), 1);
    });

    running.push(job);

    // wait until at least one slot frees up
    if (running.length >= CFG.CONCURRENCY) {
      await Promise.race(running);
    }
  }

  // wait for the final batch
  await Promise.all(running);

  console.log("✅  All videos processed.");
})();
