import {
  S3Client,
  ListObjectsV2Command,
  ListObjectsV2CommandOutput
} from '@aws-sdk/client-s3';
import { writeFileSync } from 'fs';
import path from 'path';
import dotenv from 'dotenv';

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const BUCKET = process.env.S3_VIDEOS_BUCKET || 'oriane-contents';
const s3 = new S3Client({});

/**
 * List and count the unique "platform/shortcode/" folders.
 */
async function countTopLevelPlatformShortcodeFolders() {
  console.log(`🚀 Starting to list top-level folders in bucket "${BUCKET}"...`);

  let ContinuationToken: string | undefined = undefined;
  const topLevelFolders = new Set<string>();
  let totalObjectsListed = 0;
  let batch = 0;

  do {
    batch++;
    console.log(`📄 Fetching batch ${batch}...`);
    const listResp: ListObjectsV2CommandOutput = await s3.send(
      new ListObjectsV2Command({
        Bucket: BUCKET,
        ContinuationToken,
      })
    );

    const keys = (listResp.Contents ?? []).map((o) => o.Key!).filter(Boolean);
    totalObjectsListed += keys.length;

    for (const key of keys) {
      const parts = key.split('/').filter(Boolean);
      if (parts.length >= 2) {
        // Only take the platform/shortcode folder, ignore deeper paths
        const folderPrefix = `${parts[0]}/${parts[1]}/`;
        topLevelFolders.add(folderPrefix);
      }
    }

    console.log(`✅ Batch ${batch}: Listed ${totalObjectsListed} total objects so far, found ${topLevelFolders.size} unique folders.`);

    ContinuationToken = listResp.IsTruncated
      ? listResp.NextContinuationToken
      : undefined;
  } while (ContinuationToken);

  console.log(`🎯 Done!`);
  console.log(`📦 Found ${topLevelFolders.size} unique platform/shortcode folders.`);

  const csvContent = 'platform,shortcode\n' +
    [...topLevelFolders]
      .map(folder => {
        const [platform, shortcode] = folder.split('/');
        return `${platform},${shortcode}`;
      })
      .join('\n');

  const outputPath = path.resolve(__dirname, 'count_s3_contents.csv');
  writeFileSync(outputPath, csvContent);

  console.log(`✅ Folders count saved to ${outputPath}`);
}


countTopLevelPlatformShortcodeFolders().catch((err) => {
  console.error('❌ Failed to count platform/shortcode folders:', err);
  process.exit(1);
});
