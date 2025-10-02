import { 
  S3Client,
  ListObjectsV2Command
} from '@aws-sdk/client-s3';
import dotenv from 'dotenv';
import { writeFileSync } from 'fs';
import path from 'path';
dotenv.config();

const BUCKET = process.env.S3_BUCKET_FRAMES || 'oriane-contents';
const s3 = new S3Client({});

const PLATFORMS = ['instagram', 'tiktok', 'youtube'];

async function scanPlatform(platform: string) {
  console.log(`🚀 Scanning platform: ${platform}`);
  let ContinuationToken: string | undefined = undefined;
  const prefixes = new Set<string>();
  let batch = 0;

  do {
    batch++;
    const listResp = await s3.send(
      new ListObjectsV2Command({
        Bucket: BUCKET,
        Prefix: `${platform}/`,
        ContinuationToken,
      })
    );

    const framesKeys = (listResp.Contents ?? [])
      .filter((o) => o.Key?.includes('/frames/'))
      .map((o) => o.Key!);

    for (const key of framesKeys) {
      const prefix = key.split('/frames/')[0]; // "platform/shortcode"
      prefixes.add(prefix);
    }

    console.log(`✅ [${platform}] Batch ${batch}: Found ${prefixes.size} frame folders so far.`);

    ContinuationToken = listResp.IsTruncated
      ? listResp.NextContinuationToken
      : undefined;
  } while (ContinuationToken);

  console.log(`🎯 Done scanning platform: ${platform}`);
  return prefixes;
}

async function countRemainingFramesFoldersOptimized() {
  console.log(`🚀 Starting optimized scan for frames folders...`);

  const results = await Promise.all(
    PLATFORMS.map((platform) => scanPlatform(platform))
  );

  const allPrefixes = new Set<string>();
  for (const prefixes of results) {
    for (const prefix of prefixes) {
      allPrefixes.add(prefix);
    }
  }

  console.log(`🎯 All platforms done!`);
  console.log(`📦 Found ${allPrefixes.size} unique "frames" folders remaining.`);
  console.log([...allPrefixes]);

  const csvContent = 'platform,shortcode\n' + 
    [...allPrefixes]
      .map(folder => {
        const [platform, shortcode] = folder.split('/');
        return `${platform},${shortcode}`;
      })
      .join('\n');

  const outputPath = path.resolve(__dirname, 'count_frames_dirs.csv');
  writeFileSync(outputPath, csvContent);

  console.log(`✅ Count of frames folders saved to ${outputPath}`);
}

countRemainingFramesFoldersOptimized().catch((err) => {
  console.error('❌ Failed to count frames folders:', err);
  process.exit(1);
});
