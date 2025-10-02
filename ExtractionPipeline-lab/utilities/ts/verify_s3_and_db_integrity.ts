import {
  ListObjectsV2Command,
  S3Client,
  ListObjectsV2CommandOutput,
} from '@aws-sdk/client-s3';
import { Client as PgClient } from 'pg';
import { writeFileSync } from 'fs';
import path from 'path';
import dotenv from 'dotenv';

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

// ─── Configuration ────────────────────────────────────────────────────────────
const {
  DB_HOST,
  DB_PORT = '5432',
  DB_NAME,
  DB_USER,
  DB_PASSWORD,
  S3_VIDEOS_BUCKET: S3_BUCKET,
  AWS_REGION = 'us-east-1',
} = process.env;

if (!DB_HOST || !DB_NAME || !DB_USER || !DB_PASSWORD) {
  throw new Error('DB_HOST, DB_NAME, DB_USER and DB_PASSWORD must be set');
}

const pg = new PgClient({
  host: DB_HOST,
  port: parseInt(DB_PORT, 10),
  database: DB_NAME,
  user: DB_USER,
  password: DB_PASSWORD,
});

// ─── Fetch codes from Postgres ────────────────────────────────────────────────
async function fetchShortcodesFromDB(): Promise<Set<string>> {
  console.log('📦 Fetching shortcodes from Postgres...');
  const shortcodes = new Set<string>();
  await pg.connect();

  const pageSize = 1000;
  let offset = 0;

  while (true) {
    const res = await pg.query(
      `SELECT code
         FROM insta_content
        ORDER BY code
       OFFSET $1
        LIMIT $2`,
      [offset, pageSize]
    );

    if (res.rows.length === 0) break;

    for (const { code } of res.rows) {
      shortcodes.add(code);
    }
    offset += pageSize;
  }

  console.log(`✅ Fetched ${shortcodes.size} shortcodes from DB.`);
  return shortcodes;
}

// ─── Scan S3 for orphan folders ───────────────────────────────────────────────
async function findOrphanFolders() {
  const videoCodes = await fetchShortcodesFromDB();
  console.log('🚀 Starting S3 scan...');

  const s3 = new S3Client({ region: AWS_REGION });
  let ContinuationToken: string | undefined = undefined;
  const orphanFolders = new Set<string>();
  const seenFolders = new Set<string>();
  let batch = 0;

  do {
    batch++;
    console.log(`📄 Fetching batch ${batch} from S3...`);
    const resp: ListObjectsV2CommandOutput = await s3.send(
      new ListObjectsV2Command({
        Bucket: S3_BUCKET,
        ContinuationToken,
      })
    );

    for (const obj of resp.Contents ?? []) {
      if (!obj.Key) continue;
      const parts = obj.Key.split('/').filter(Boolean);
      if (parts.length < 2) continue;

      const folder = `${parts[0]}/${parts[1]}`;
      if (seenFolders.has(folder)) continue;
      seenFolders.add(folder);

      if (!videoCodes.has(parts[1])) {
        orphanFolders.add(folder);
      }
    }

    console.log(`✅ Batch ${batch}: ${orphanFolders.size} orphans so far.`);
    ContinuationToken = resp.IsTruncated ? resp.NextContinuationToken : undefined;
  } while (ContinuationToken);

  console.log(`🎯 Done! Found ${orphanFolders.size} orphan folders.`);

  const csv = [
    'platform,shortcode',
    ...[...orphanFolders].map(f => f.replace('/', ','))
  ].join('\n');

  const outPath = path.resolve(__dirname, 'verify_s3_and_db_integrity.csv');
  writeFileSync(outPath, csv);

  console.log(`✅ Orphan folders saved to ${outPath}`);
  await pg.end();
}

// ─── Kick it off ───────────────────────────────────────────────────────────────
findOrphanFolders().catch(err => {
  console.error('❌ Verification failed:', err);
  process.exit(1);
});
