#!/usr/bin/env bun

import { promises as fs } from "fs";
import path from "path";
import { spawn } from "bun";
import { glob } from "glob";
import ffprobeStatic from "ffprobe-static";

const INPUT_DIR  = "../videos";
const OUTPUT_DIR = "cropped_videos3";
const FFMPEG     = "ffmpeg";
const FFPROBE    = ffprobeStatic.path;

// pick crop via cropdetect=limit:round:reset
async function detectCrop(file: string): Promise<[number,number,number,number]> {
  const p = spawn({
    cmd: [
      FFMPEG,
      "-hide_banner","-loglevel","info",
      "-i", file,
      // use TOLERANCE=5, round to 2, reset every second
      "-vf", "cropdetect=5:2:1",
      "-f", "null","-"
    ],
    stderr: "pipe"
  });
  const log = await new Response(p.stderr).text();
  await p.exited;

  const crops = Array.from(log.matchAll(/crop=(\d+):(\d+):(\d+):(\d+)/g))
    .map(m => m.slice(1).map(Number) as [number,number,number,number]);
  if (!crops.length) throw new Error("cropdetect found no hints");

  // most frequent
  const counts = new Map<string,number>();
  for (const c of crops) {
    const key = c.join(",");
    counts.set(key,(counts.get(key)||0)+1);
  }
  const [best] = Array.from(counts.entries()).sort((a,b)=>b[1]-a[1])[0];
  return best.split(",").map(n=>+n) as [number,number,number,number];
}

async function cropVideo(src: string, dst: string, [w,h,x,y]: [number,number,number,number]) {
  await fs.mkdir(path.dirname(dst),{ recursive:true });
  await spawn({
    cmd:[
      FFMPEG,
      "-hide_banner","-loglevel","error",
      "-i", src,
      "-vf", `crop=${w}:${h}:${x}:${y}`,
      "-c:a","copy",
      dst
    ],
    stdout:"ignore", stderr:"inherit"
  }).exited;
}

async function batch() {
  await fs.mkdir(OUTPUT_DIR,{ recursive:true });
  const files = await glob(path.join(INPUT_DIR,"*.mp4"));
  for (const src of files.sort()) {
    const name = path.basename(src);
    const dst  = path.join(OUTPUT_DIR,name);
    process.stdout.write(`→ ${name} `);
    try {
      const crop = await detectCrop(src);
      process.stdout.write(`crop=${crop.join(",")} `);
      await cropVideo(src,dst,crop);
      console.log("done");
    } catch (err) {
      console.log(`error (${(err as Error).message}), copying`);
      await fs.copyFile(src,dst);
    }
  }
  console.log("✅ All done");
}

if (import.meta.main) batch().catch(e=>{
  console.error(e);
  process.exit(1);
});
