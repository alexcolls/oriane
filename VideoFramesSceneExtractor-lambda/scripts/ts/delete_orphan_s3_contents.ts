import { S3Client, ListObjectsV2Command, DeleteObjectsCommand } from '@aws-sdk/client-s3';
import { readFileSync, writeFileSync } from 'fs';
import { createInterface } from 'readline';
import path from 'path';
import dotenv from 'dotenv';
dotenv.config({ path: path.resolve(__dirname, '../.env') });

const s3 = new S3Client({ region: 'us-east-1' });
const BUCKET = process.env.S3_BUCKET_VIDEOS!;
const CSV_PATH = path.resolve(__dirname, 'verify_s3_and_db_integrity.csv');

const PARALLEL_LIMIT = 12;

async function confirmDelete(): Promise<boolean> {
  const rl = createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    rl.question('⚠️  Are you sure you want to DELETE orphan folders listed in verify_s3_and_db_integrity.csv? (y/N) ', (answer) => {
      rl.close();
      const response = answer.trim().toLowerCase();
      resolve(response === 'y' || response === 'yes');
    });
  });
}

async function deleteFolder(prefix: string) {
  let ContinuationToken: string | undefined = undefined;
  let totalDeleted = 0;

  do {
    const listResp = await s3.send(
      new ListObjectsV2Command({
        Bucket: BUCKET,
        Prefix: prefix,
        ContinuationToken,
      })
    );

    const objectsToDelete = (listResp.Contents ?? []).map((o) => ({ Key: o.Key! }));

    if (objectsToDelete.length > 0) {
      const deleteResp = await s3.send(
        new DeleteObjectsCommand({
          Bucket: BUCKET,
          Delete: { Objects: objectsToDelete },
        })
      );

      totalDeleted += deleteResp.Deleted?.length ?? 0;

      if (deleteResp.Errors && deleteResp.Errors.length) {
        console.error(`❌ Errors deleting objects under ${prefix}:`, deleteResp.Errors);
      }
    }

    ContinuationToken = listResp.IsTruncated ? listResp.NextContinuationToken : undefined;
  } while (ContinuationToken);

  return totalDeleted;
}

async function deleteOrphanFolders() {
  const confirm = await confirmDelete();
  if (!confirm) {
    console.log('❌ Aborted. No folders deleted.');
    process.exit(0);
  }

  console.log('📄 Reading orphan folders CSV...');
  const csvData = readFileSync(CSV_PATH, 'utf-8');
  const header = csvData.trim().split('\n')[0]; // Save header
  let orphanLines = csvData.trim().split('\n').slice(1); // Skip header

  console.log(`🧹 Starting deletion of ${orphanLines.length} orphan folders...`);

  let foldersDeleted = 0;
  let objectsDeleted = 0;

  for (let i = 0; i < orphanLines.length; i += PARALLEL_LIMIT) {
    const chunk = orphanLines.slice(i, i + PARALLEL_LIMIT);

    const promises = chunk.map(async (line) => {
      const [platform, shortcode] = line.split(',');
      const prefix = `${platform}/${shortcode}/`;

      const deletedCount = await deleteFolder(prefix);
      return { prefix, shortcode, deletedCount };
    });

    const results = await Promise.allSettled(promises);

    const successfullyDeletedShortcodes: string[] = [];

    for (const result of results) {
      if (result.status === 'fulfilled') {
        foldersDeleted++;
        objectsDeleted += result.value.deletedCount ?? 0;
        successfullyDeletedShortcodes.push(result.value.shortcode);
      } else {
        console.error('❌ Failed to delete folder:', result.reason);
      }
    }
    orphanLines = orphanLines.filter(line => {
      const [, shortcode] = line.split(',');
      return !successfullyDeletedShortcodes.includes(shortcode);
    });

    const newCsvContent = [header, ...orphanLines].join('\n');
    writeFileSync(CSV_PATH, newCsvContent);

    if (foldersDeleted % 100 === 0) {
      console.log(`✅ Deleted ${foldersDeleted} folders, ${objectsDeleted} objects so far...`);
    }
  }

  console.log('🎯 Deletion completed!');
  console.log(`✅ Total folders deleted: ${foldersDeleted}`);
  console.log(`✅ Total objects deleted: ${objectsDeleted}`);
}

deleteOrphanFolders().catch((err) => {
  console.error('❌ Failed to delete orphan folders:', err);
  process.exit(1);
});
