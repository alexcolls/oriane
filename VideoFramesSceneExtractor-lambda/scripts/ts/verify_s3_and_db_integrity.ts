import { ListObjectsV2Command, S3Client } from '@aws-sdk/client-s3';
import { createClient } from '@supabase/supabase-js';
import { writeFileSync } from 'fs';
import path from 'path';
import dotenv from 'dotenv';
dotenv.config({ path: path.resolve(__dirname, '../.env') });

const supabaseUrl = process.env.SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

async function fetchShortcodesFromSupabase(): Promise<Set<string>> {
  console.log('📦 Fetching shortcodes from Supabase...');
  const shortcodes = new Set<string>();
  let from = 0;
  const pageSize = 1000;

  while (true) {
    const { data, error } = await supabase
      .from('insta_content')
      .select('code')
      .range(from, from + pageSize - 1);

    if (error) {
      throw new Error(`Supabase fetch error: ${error.message}`);
    }
    if (!data || data.length === 0) break;

    for (const row of data) {
      shortcodes.add(row.code);
    }

    from += pageSize;
  }

  console.log(`✅ Fetched ${shortcodes.size} shortcodes from Supabase.`);
  return shortcodes;
}

async function findOrphanFolders() {
  const supabaseShortcodes = await fetchShortcodesFromSupabase();
  console.log('🚀 Starting S3 scan...');

  let ContinuationToken: string | undefined = undefined;
  const orphanFolders = new Set<string>();
  const knownFolders = new Set<string>();
  let batch = 0;

  do {
    batch++;
    console.log(`📄 Fetching batch ${batch}...`);
    const s3 = new S3Client({ region: 'us-east-1' });
    const BUCKET = process.env.S3_BUCKET_VIDEOS;
    const listResp = await s3.send(
      new ListObjectsV2Command({
        Bucket: BUCKET,
        ContinuationToken,
      })
    );

    const keys = (listResp.Contents ?? []).map((o) => o.Key!).filter(Boolean);

    for (const key of keys) {
      const parts = key.split('/').filter(Boolean);
      if (parts.length >= 2) {
        const platform = parts[0];
        const shortcode = parts[1];
        const folderPrefix = `${platform}/${shortcode}`;

        if (!knownFolders.has(folderPrefix)) {
          knownFolders.add(folderPrefix);

          if (!supabaseShortcodes.has(shortcode)) {
            orphanFolders.add(folderPrefix);
          }
        }
      }
    }

    console.log(`✅ Batch ${batch}: Found ${orphanFolders.size} orphan folders so far.`);

    ContinuationToken = listResp.IsTruncated
      ? listResp.NextContinuationToken
      : undefined;
  } while (ContinuationToken);

  console.log(`🎯 Done! Found ${orphanFolders.size} orphan folders (no DB record).`);

  const csvContent = 'platform,shortcode\n' + 
    [...orphanFolders]
      .map(folder => {
        const [platform, shortcode] = folder.split('/');
        return `${platform},${shortcode}`;
      })
      .join('\n');

  const outputPath = path.resolve(__dirname, 'verify_s3_and_db_integrity.csv');
  writeFileSync(outputPath, csvContent);

  console.log(`✅ Orphan folders saved to ${outputPath}`);
}

findOrphanFolders().catch((err) => {
  console.error('❌ Failed to verify S3 and DB integrity:', err);
  process.exit(1);
});
