import AWS from 'aws-sdk';
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import * as fs from 'fs';
import * as path from 'path';
import { exec as execCallback } from 'child_process';
import { promisify } from 'util';
import dotenv from 'dotenv';

dotenv.config();
process.env.PATH = '/opt/bin:' + process.env.PATH;

const exec = promisify(execCallback);
const DEBUG = true;
const CONCURRENCY_LIMIT = 5;
const DEFAULT_FRAME_INTERVAL = 1;
const JPEG_QUALITY = 95;
const S3_BUCKET_VIDEOS = process.env.S3_BUCKET_VIDEOS || 'oriane-contents';
const S3_BUCKET_FRAMES = process.env.S3_BUCKET_FRAMES || 'oriane-contents';

const s3 = new AWS.S3();

const SUPABASE_URL = process.env.SUPABASE_URL || '';
const SUPABASE_KEY = process.env.SUPABASE_KEY || '';
const supabase: SupabaseClient = createClient(SUPABASE_URL, SUPABASE_KEY);

type ProcessResult = {
  status: string;
  success: boolean;
  shortcode: string;
  platform: string;
  message: string;
};

function debugLog(...args: any[]): void {
  if (DEBUG) {
    console.log(...args);
  }
}

async function runWithConcurrency<T>(
  tasks: (() => Promise<T>)[],
  limit: number
): Promise<T[]> {
  const results: T[] = [];
  let index = 0;

  async function next() {
    if (index >= tasks.length) return;
    const current = index++;
    try {
      results[current] = await tasks[current]();
    } catch (err) {
      results[current] = err as T;
    }
    await next();
  }

  const workers = [];
  for (let i = 0; i < limit; i++) {
    workers.push(next());
  }
  await Promise.all(workers);

  return results;
}

function mapQuality(quality: number): number {
  return Math.round(31 - ((quality - 1) / 99) * 29);
}

async function fetchVideoInfo(shortcode: string): Promise<boolean> {
  try {
    const { data, error } = await supabase
      .from('insta_content')
      .select('is_downloaded, is_extracted')
      .eq('code', shortcode)
      .maybeSingle();

    if (error) {
      console.error('❌ fetchVideoInfo error:', error);
      return false;
    }

    if (!data) {
      debugLog(`⚠️ No row for shortcode=${shortcode}`);
      return false;
    }

    return data.is_downloaded && !data.is_extracted;
  } catch (e) {
    console.error('❌ fetchVideoInfo exception:', e);
    return false;
  }
}

async function updateSupabaseDownloadStatus(code: string): Promise<void> {
  try {
    const { error } = await supabase
      .from('insta_content')
      .update({ is_downloaded: true })
      .eq('code', code);

    if (error) {
      console.error('❌ updateDownloadStatus error:', error);
    } else {
      debugLog(`✅ Marked is_downloaded=true for ${code}`);
    }
  } catch (e) {
    console.error('❌ updateDownloadStatus exception:', e);
  }
}

async function updateSupabaseAfterExtraction(code: string): Promise<void> {
  try {
    const { error } = await supabase
      .from('insta_content')
      .update({ is_extracted: true })
      .eq('code', code)
      .maybeSingle();

    if (error) {
      console.error('❌ updateExtracted error:', error);
    } else {
      debugLog(`✅ Marked is_extracted=true for ${code}`);
    }
  } catch (e) {
    console.error('❌ updateExtracted exception:', e);
  }
}

async function downloadVideoFromS3(
  platform: string,
  code: string
): Promise<string | null> {
  const key = `${platform}/${code}/video.mp4`;
  const localPath = `/tmp/${platform}_${code}.mp4`;
  try {
    const data = await s3
      .getObject({ Bucket: S3_BUCKET_VIDEOS, Key: key })
      .promise();
    await fs.promises.writeFile(localPath, data.Body as Buffer);
    debugLog(`✅ Downloaded ${key}`);
    return localPath;
  } catch (e) {
    console.error(`❌ downloadVideoFromS3 error for ${key}:`, e);
    return null;
  }
}

async function extractFrames(
  videoPath: string,
  outputDir: string,
  ext = 'jpg',
  quality = JPEG_QUALITY,
  maxSeconds: number | null = null,
  interval = DEFAULT_FRAME_INTERVAL
): Promise<string[]> {
  try {
    await fs.promises.mkdir(outputDir, { recursive: true });

    const q = mapQuality(quality);
    let cmd = `ffmpeg -hide_banner -loglevel error -i "${videoPath}" -vf fps=1/${interval} `;

    if (maxSeconds !== null) {
      cmd += `-t ${maxSeconds} `;
    }

    cmd += `-q:v ${q} -start_number 0 "${path.join(
      outputDir,
      `%d.${ext}`
    )}"`;

    debugLog(`🔧 Running command: ${cmd}`);
    await exec(cmd);

    const files = await fs.promises.readdir(outputDir);
    const framePaths = files
      .filter((f) => path.extname(f).toLowerCase() === `.${ext}`)
      .map((f) => path.join(outputDir, f))
      .sort(
        (a, b) =>
          parseInt(path.basename(a), 10) -
          parseInt(path.basename(b), 10)
      );

    debugLog(`✅ Extracted ${framePaths.length} frames`);
    return framePaths;
  } catch (e) {
    console.error('❌ extractFrames error:', e);
    throw e;
  }
}

async function saveFrameToS3(
  framePath: string,
  platform: string,
  code: string,
  frameNum: string,
  interval: number
): Promise<void> {
  const ext = path.extname(framePath).slice(1);
  const key = `${platform}/${code}/frames/${interval}sec/${frameNum}.${ext}`;

  try {
    const body = await fs.promises.readFile(framePath);
    await s3.upload({
      Bucket: S3_BUCKET_FRAMES,
      Key: key,
      Body: body,
    }).promise();

    debugLog(`✅ Uploaded ${key}`);
    await fs.promises.unlink(framePath);
  } catch (e) {
    console.error(`❌ saveFrameToS3 error for ${frameNum}:`, e);
  }
}

async function processVideo(
  code: string,
  platform: string,
  frameInterval = DEFAULT_FRAME_INTERVAL,
  ext = 'jpg'
): Promise<ProcessResult> {
  debugLog(`▶️ processVideo for ${code}`);

  const videoPath = await downloadVideoFromS3(platform, code);

  if (!videoPath) {
    await updateSupabaseDownloadStatus(code);
    return {
      status: 'skipped',
      success: false,
      shortcode: code,
      platform,
      message: 'Video missing – marked is_downloaded.',
    };
  }

  const outputDir = `/tmp/${platform}_${code}_frames`;
  let frames: string[];

  try {
    frames = await extractFrames(
      videoPath,
      outputDir,
      ext,
      JPEG_QUALITY,
      null,
      frameInterval
    );
  } catch (e: any) {
    await supabase
      .from('insta_content')
      .update({ extract_error: e.message })
      .eq('code', code);

    await fs.promises.unlink(videoPath).catch(() => {});
    return {
      status: 'error',
      success: false,
      shortcode: code,
      platform,
      message: 'Frame extraction failed.',
    };
  }

  if (frames.length === 0) {
    await supabase
      .from('insta_content')
      .update({ extract_error: 'No frames extracted.' })
      .eq('code', code);

    await fs.promises.unlink(videoPath).catch(() => {});
    return {
      status: 'error',
      success: false,
      shortcode: code,
      platform,
      message: 'No frames extracted.',
    };
  }

  try {
    await Promise.all(
      frames.map((fp) =>
        saveFrameToS3(
          fp,
          platform,
          code,
          path.parse(fp).name,
          frameInterval
        )
      )
    );
  } catch (e: any) {
    console.error(`❌ Upload failure for ${code}:`, e);

    await supabase
      .from('insta_content')
      .update({ extract_error: `Upload failed: ${e.message}` })
      .eq('code', code);

    await fs.promises.unlink(videoPath).catch(() => {});
    return {
      status: 'error',
      success: false,
      shortcode: code,
      platform,
      message: 'Frame upload failed.',
    };
  }

  await fs.promises.rm(outputDir, { recursive: true, force: true }).catch(() => {});
  await fs.promises.unlink(videoPath).catch(() => {});

  await updateSupabaseAfterExtraction(code);

  return {
    status: 'frames extracted',
    success: true,
    shortcode: code,
    platform,
    message: 'Frames extracted.',
  };
}

export const handler = async (event: any): Promise<any> => {
  try {
    const tasks = event.Records.map((record: { body: string }) => async () => {
      const { shortcode, platform, frame_interval, ext } = JSON.parse(
        record.body
      );

      if (!shortcode || !platform) {
        throw new Error('Missing or invalid shortcode/platform');
      }

      if (!(await fetchVideoInfo(shortcode))) {
        return {
          status: 'skipped',
          success: false,
          shortcode,
          platform,
          message: 'Not fetched or already extracted',
        };
      }

      return processVideo(
        shortcode,
        platform,
        frame_interval || DEFAULT_FRAME_INTERVAL,
        ext || 'jpg'
      );
    });

    const results = await runWithConcurrency(
      tasks,
      CONCURRENCY_LIMIT
    );

    return { status: 'completed', results };
  } catch (e: any) {
    console.error('❌ handler error:', e);
    return { status: 'error', message: e.message };
  }
};
