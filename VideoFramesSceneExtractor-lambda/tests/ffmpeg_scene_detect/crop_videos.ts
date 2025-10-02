#!/usr/bin/env ts-node
/* ------------------------------------------------------------------
 *  Smart MP4 auto-cropper (FFmpeg-only) – keeps 1 FPS sampling logic
 * ----------------------------------------------------------------*/
import { spawnSync } from "child_process";
import fg            from "fast-glob";
import path          from "path";
import fs            from "fs/promises";
import os            from "os";

/* ────── CONFIG ────── */
const CFG = {
  INPUT_DIR  : "../videos",
  OUTPUT_DIR : "cropped_videos_bun",
  SAMPLE_FPS : 1,        // one frame per second
  ROUND      : 2,        // make final width/height divisible by N
  LIMIT_SOFT : 24,       // conservative 1st pass
  LIMIT_HARD : 6,        // aggressive 2nd pass
  MIN_CROP_RATIO : 0.10, // need ≥10 % trim to bother
  CONCURRENCY : Math.max(os.cpus().length - 1, 1)
};
/*─────────────────────*/

interface Box { w:number; h:number; x:number; y:number; }
const parseCrop = (s:string):Box | null => {
  const m = s.match(/crop=(\\d+):(\\d+):(\\d+):(\\d+)/);
  return m ? { w:+m[1], h:+m[2], x:+m[3], y:+m[4] } : null;
};

function detectAll(src:string, limit:number): Box[] {
  /* sample 1 fps then cropdetect; collect every crop line */
  const stderr = runFFmpeg([
    "-i", src,
    "-vf", `fps=${CFG.SAMPLE_FPS},cropdetect=${limit}:${CFG.ROUND}:0`,
    "-an", "-t", "99999", "-f", "null", "-" // analyse whole clip
  ]);
  return [...stderr.matchAll(/crop=\\S+/g)]
           .map(m => parseCrop(m[0])!)
           .filter(Boolean);
}

function union(boxes:Box[]):Box {
  const x0 = Math.min(...boxes.map(b=>b.x));
  const y0 = Math.min(...boxes.map(b=>b.y));
  const x1 = Math.max(...boxes.map(b=>b.x + b.w));
  const y1 = Math.max(...boxes.map(b=>b.y + b.h));
  // round to multiple of ROUND (2 or 4) to keep encoder happy
  const round = CFG.ROUND;
  const w = Math.ceil((x1 - x0) / round) * round;
  const h = Math.ceil((y1 - y0) / round) * round;
  return { x:x0, y:y0, w, h };
}

function shouldCrop(orig:Box, crop:Box) {
  return (orig.w - crop.w)/orig.w >= CFG.MIN_CROP_RATIO ||
         (orig.h - crop.h)/orig.h >= CFG.MIN_CROP_RATIO;
}

/* ------------ helpers (replace old versions) ------------ */
function sh(cmd: string, args: string[]): string {
  const { status, stdout, stderr } =
    spawnSync(cmd, args, { encoding: "utf8" });
  if (status !== 0) throw new Error(stderr.trim() || stdout.trim());
  return stdout.trim();
}

/** Run ffmpeg, return *combined* stderr+stdout (useful for cropdetect). */
function runFFmpeg(args: string[]): string {
  return sh("ffmpeg", ["-hide_banner", "-loglevel", "error", ...args]);
}

/** Robust width/height probe via ffprobe (never regex FFmpeg text). */
function probeWH(src: string): Box {
  const out = sh("ffprobe", [
    "-v", "error",
    "-select_streams", "v:0",
    "-show_entries", "stream=width,height",
    "-of", "csv=p=0", src,
  ]);                       // returns "1920,1080" (or similar)
  const [w, h] = out.split(/[\\s,]+/).map(Number);
  if (!w || !h) throw new Error(`ffprobe failed for ${src}`);
  return { w, h, x: 0, y: 0 };
}
/* --------------------------------------------------------- */

async function doCrop(src:string){
  const name = path.basename(src);
  const dst  = path.join(CFG.OUTPUT_DIR, name);
  process.stdout.write(`→ ${name}  `);

  const orig = probeWH(src);

  /* pass 1: conservative */
  const boxes1 = detectAll(src, CFG.LIMIT_SOFT);
  let crop = boxes1.length ? union(boxes1) : null;
  let how  = "median-like";

  /* pass 2 if needed */
  if (!crop || !shouldCrop(orig, crop)){
    const boxes2 = detectAll(src, CFG.LIMIT_HARD);
    if (boxes2.length){
      const u = union(boxes2);
      if (shouldCrop(orig, u)){ crop=u; how="edge-like"; }
    }
  }

  if (!crop){
    process.stdout.write("no crop → copy\n");
    await fs.copyFile(src, dst);
    return;
  }

  process.stdout.write(`crop[${how}]=${crop.w}:${crop.h}:${crop.x}:${crop.y}  `);

  runFFmpeg([
    "-i", src,
    "-vf", `crop=${crop.w}:${crop.h}:${crop.x}:${crop.y}`,
    "-c:v", "libx264", "-crf", "18",
    "-c:a", "copy",
    dst
  ]);
  console.log("done");
}

/* ── parallel batch ── */
(async()=>{
  await fs.mkdir(CFG.OUTPUT_DIR, { recursive:true });
  const files = await fg("*.mp4", { cwd:CFG.INPUT_DIR, absolute:true });

  const running:Promise<void>[] = [];
  for (const f of files){
    const p = doCrop(f).catch(console.error);
    running.push(p);
    if (running.length >= CFG.CONCURRENCY)
      await Promise.race(running);
    // purge finished
    for (let i=running.length-1;i>=0;--i)
      if (!!running[i].then) running.splice(i,1);
  }
  await Promise.all(running);
  console.log("✅ All videos processed.");
})();
