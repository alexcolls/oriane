#!/usr/bin/env bun

import { promises as fs } from "fs";
import path from "path";
import { spawn } from "bun";
import sharp from "sharp";
import ffprobeStatic from "ffprobe-static";
import { glob } from "glob";

// ─── Config ──────────────────────────────────────────────────────────────────
const INPUT_DIR              = "cropped_videos2";
const OUTPUT_DIR             = "output/cropped_12_advanced_bun_hq";
const MIN_FRAMES             = 4;
const THRESHOLD              = 0.12;
const BLANK_FRACTION_THRESH  = 0.5;   // drop if >50% of pixels share the same gray value
const IMAGE_CROP_TOL         = 10;    // for margin-cropping
const FFMPEG                 = "ffmpeg";
const FFPROBE                = ffprobeStatic.path;

interface RawImage {
  data: Buffer;
  info: { width: number; height: number; channels: number };
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Load a JPEG into raw pixels + metadata */
async function loadRaw(imagePath: string): Promise<RawImage> {
  return sharp(imagePath)
    .raw()
    .toBuffer({ resolveWithObject: true }) as Promise<RawImage>;
}

/** Load raw from an in-memory Buffer */
async function loadRawFromBuffer(buffer: Buffer): Promise<RawImage> {
  return sharp(buffer)
    .raw()
    .toBuffer({ resolveWithObject: true }) as Promise<RawImage>;
}

/**
 * Detect crop rect by stripping uniform margins:
 * returns { x,y,w,h } or null if no crop needed.
 */
function detectImageCrop(raw: RawImage, tol: number = IMAGE_CROP_TOL) {
  const { data, info } = raw;
  const { width: w, height: h, channels: c } = info;

  // check if one line (list of byte-offsets) is within tol to its median color
  function isBlankLine(offsets: number[]): boolean {
    const med = new Array<number>(c).fill(0);
    // compute median per channel
    for (let ch = 0; ch < c; ch++) {
      const vals = offsets.map(off => data[off + ch]).sort((a,b)=>a-b);
      med[ch] = vals[(vals.length-1)>>1];
    }
    // ensure every pixel in line is within tol
    for (const off of offsets) {
      let sum = 0;
      for (let ch = 0; ch < c; ch++) {
        sum += Math.abs(data[off+ch] - med[ch]);
      }
      if (sum > tol) return false;
    }
    return true;
  }

  let x0 = 0, x1 = w, y0 = 0, y1 = h;
  // left
  for (; x0 < w; x0++) {
    const offs = Array.from({ length: h }, (_, y) => (y*w + x0)*c);
    if (!isBlankLine(offs)) break;
  }
  // right
  for (; x1 > x0; x1--) {
    const offs = Array.from({ length: h }, (_, y) => (y*w + (x1-1))*c);
    if (!isBlankLine(offs)) break;
  }
  // top
  for (; y0 < h; y0++) {
    const offs = Array.from({ length: w }, (_, x) => (y0*w + x)*c);
    if (!isBlankLine(offs)) break;
  }
  // bottom
  for (; y1 > y0; y1--) {
    const offs = Array.from({ length: w }, (_, x) => ((y1-1)*w + x)*c);
    if (!isBlankLine(offs)) break;
  }

  if (x0===0 && y0===0 && x1===w && y1===h) return null;
  if (x0>=x1 || y0>=y1) return null;
  return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
}

/**
 * Returns true if more than BLANK_FRACTION_THRESH of pixels share the same gray value.
 */
function isMostlyBlankGray(data: Buffer): boolean {
  const counts = new Map<number, number>();
  for (const v of data) {
    counts.set(v, (counts.get(v) || 0) + 1);
  }
  const maxCount = Math.max(...counts.values());
  return maxCount / data.length >= BLANK_FRACTION_THRESH;
}

/** Probe fps & frame count via ffprobe */
async function probeVideo(videoPath: string) {
  const args = [
    "-v","error",
    "-select_streams","v:0",
    "-show_entries","stream=avg_frame_rate,nb_frames",
    "-of","json",
    videoPath,
  ];
  const proc = spawn({ cmd: [FFPROBE, ...args], stdout: "pipe" });
  const jsonText = await new Response(proc.stdout).text();
  await proc.exited;
  const streams = JSON.parse(jsonText).streams || [];
  const { avg_frame_rate="25/1", nb_frames="0" } = streams[0] || {};
  const [num,den] = avg_frame_rate.split("/").map(Number);
  return { fps: den? num/den : 25, total: parseInt(nb_frames,10) || 0 };
}

/** Run ffmpeg scene-detect; returns [(path, pts), …] */
async function ffmpegExtractWithPts(
  videoPath: string,
  outDir: string,
  threshold: number
): Promise<Array<[string, number]>> {
  // clear old data
  await fs.rm(outDir, { recursive: true, force: true });
  await fs.mkdir(outDir, { recursive: true });

  const pattern = path.join(outDir, "%d.jpg");
  const args = [
    "-hide_banner","-loglevel","error",
    "-i", videoPath,
    "-vf", `select='gt(scene,${threshold})'`,
    "-vsync","vfr",
    "-frame_pts","1",
    "-q:v","2",
    pattern,
  ];
  const proc = spawn({ cmd: [FFMPEG, ...args], stdout: "ignore", stderr: "inherit" });
  const code = await proc.exited;
  if (code !== 0) throw new Error(`ffmpeg failed with code ${code}`);

  const entries: Array<[string, number]> = [];
  for (const file of await glob(path.join(outDir,"*.jpg"))) {
    entries.push([file, parseInt(path.basename(file,".jpg"),10)]);
  }
  entries.sort((a,b)=>a[1]-b[1]);
  return entries;
}

/** Fallback sampling */
async function extractFallbackFrames(
  videoPath: string,
  outDir: string,
  fps: number,
  total: number,
  startIdx: number
): Promise<number> {
  const step = Math.max(1, Math.floor(total/(MIN_FRAMES+1)));
  let idx = startIdx;

  for (let i=1; i<=MIN_FRAMES && idx<=MIN_FRAMES; i++) {
    const frameNo = i*step;
    const seconds = frameNo/fps;
    const tmp = path.join(outDir, `tmp_${idx}.jpg`);
    const proc = spawn({
      cmd: [
        FFMPEG,
        "-hide_banner","-loglevel","error",
        "-ss", seconds.toString(),
        "-i", videoPath,
        "-frames:v","1",
        "-q:v","2",
        tmp,
      ],
      stdout:"ignore", stderr:"inherit"
    });
    await proc.exited;

    // crop & gray
    const imgBuf = await fs.readFile(tmp);
    const rawOrig = await loadRawFromBuffer(imgBuf);
    const rect    = detectImageCrop(rawOrig);
    let transformer = sharp(imgBuf);
    if (rect) {
      transformer = transformer.extract({
        left:   rect.x,
        top:    rect.y,
        width:  rect.w,
        height: rect.h,
      });
    }

    const grayBuf = await transformer
      .clone()
      .greyscale()
      .raw()
      .toBuffer();
    await fs.unlink(tmp);

    if (isMostlyBlankGray(grayBuf)) continue;

    const outName = path.join(outDir, `${idx}_${seconds.toFixed(2)}.png`);
    await transformer
      .png()
      .toFile(outName);
    idx++;
  }

  return idx-1;
}

async function processVideo(videoPath: string) {
  const base = path.basename(videoPath, path.extname(videoPath));
  const outDir = path.join(OUTPUT_DIR, base);
  console.log(`Processing ${videoPath} → ${outDir}…`);

  const { fps, total } = await probeVideo(videoPath);

  // 1) Scene cuts
  const entries = await ffmpegExtractWithPts(videoPath, outDir, THRESHOLD);
  console.log(`  FFmpeg produced ${entries.length} raw frames`);

  // 2) Crop margins, filter & rename
  let idx = 1;
  for (const [oldPath, pts] of entries) {
    // 1) read into memory
    const imgBuf = await fs.readFile(oldPath);
    // 2) detect crop on raw pixels
    const rawOrig  = await loadRawFromBuffer(imgBuf);
    const rect     = detectImageCrop(rawOrig);
    // 3) build pipeline from Buffer, so we can delete the file immediately
    let transformer = sharp(imgBuf);
    if (rect) {
      transformer = transformer.extract({
        left:   rect.x,
        top:    rect.y,
        width:  rect.w,
        height: rect.h,
      });
    }
    // 4) test blank in-memory
    const grayBuf = await transformer
      .clone()
      .greyscale()
      .raw()
      .toBuffer();
    // 5) now safe to delete the temp file on disk
    await fs.unlink(oldPath);

    if (isMostlyBlankGray(grayBuf)) continue;

    const seconds = pts/fps;
    const newName = path.join(outDir, `${idx}_${seconds.toFixed(2)}.png`);
    // write out the final cropped frame
    await transformer
      .png()
      .toFile(newName);
    idx++;
  }

  // 3) Fallback if too few
  if (idx <= MIN_FRAMES) {
    console.log(`  << fallback to time-based sampling >>`);
    const finalCount = await extractFallbackFrames(videoPath, outDir, fps, total, idx);
    console.log(`  Total after fallback: ${finalCount} frames`);
  } else {
    console.log(`  Done with ${idx-1} frames (≥${MIN_FRAMES})`);
  }
}

(async () => {
  await fs.mkdir(OUTPUT_DIR, { recursive: true });
  for (const fname of (await fs.readdir(INPUT_DIR)).sort()) {
    if (!fname.toLowerCase().endsWith(".mp4")) continue;
    await processVideo(path.join(INPUT_DIR, fname));
  }
  console.log("All done.");
})();
