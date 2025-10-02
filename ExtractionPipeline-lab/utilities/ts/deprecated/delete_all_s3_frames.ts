/*** DEPRECATED
 * because frames are now stored in a separate bucket
 * no longer in oriane-contents, now uses oriane-frames s3
 ***/

/* It will remove all frames from S3.
/* BE CAREFUL RUNNING THIS! */

import {
  S3Client,
  ListObjectsV2Command,
  DeleteObjectsCommand,
  ListObjectsV2CommandOutput
} from "@aws-sdk/client-s3";
import * as readline from "readline";
import path from "path";
import dotenv from "dotenv";

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const BUCKET = process.env.S3_VIDEOS_BUCKET || "oriane-contents";
const s3 = new S3Client({});

/**
 * Delete every object whose key contains "/frames/".
 * After each batch, logs the number of deleted frames per
 * "{platform}/{shortcode}" prefix.
 */
async function deleteAllFrames() {
  let ContinuationToken: string | undefined = undefined;
  do {
    // 1) List up to 1,000 objects at a time
    const listResp: ListObjectsV2CommandOutput = await s3.send(
      new ListObjectsV2Command({
        Bucket: BUCKET,
        ContinuationToken,
      })
    );
    // 2) Filter to only the “frames” keys
    const toDelete = (listResp.Contents ?? [])
      .filter((o) => o.Key?.includes("/frames/"))
      .map((o) => ({ Key: o.Key! }));
    if (toDelete.length > 0) {
      // 3) Delete them
      const delResp = await s3.send(
        new DeleteObjectsCommand({
          Bucket: BUCKET,
          Delete: { Objects: toDelete },
        })
      );
      const deleted = delResp.Deleted ?? [];
      // 4) Group by prefix "platform/shortcode"
      const counts: Record<string, number> = {};
      for (const entry of deleted) {
        const key = entry.Key!;
        const prefix = key.split("/frames/")[0]; // yields "platform/shortcode"
        counts[prefix] = (counts[prefix] || 0) + 1;
      }
      // 5) Log per‐prefix deletions
      for (const [prefix, n] of Object.entries(counts)) {
        console.log(`→ Deleted ${n} frames from ${prefix}`);
      }
      if (delResp.Errors && delResp.Errors.length) {
        console.warn("⚠️ Some deletions failed:", delResp.Errors);
      }
    }
    ContinuationToken = listResp.IsTruncated
      ? listResp.NextContinuationToken
      : undefined;
  } while (ContinuationToken);
}

/** Ask for y/N confirmation before proceeding. */
function confirmAndRun() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  rl.question(
    `⚠️  Are you sure you want to DELETE **ALL** '/frames/' objects from S3 bucket "${BUCKET}"? This cannot be undone. (y/N) `,
    (answer) => {
      rl.close();
      const resp = answer.trim().toLowerCase();
      if (resp === "y" || resp === "yes") {
        deleteAllFrames()
          .then(() => console.log("✅ All frames removed"))
          .catch((err) => {
            console.error("❌ Failed to remove frames:", err);
            process.exit(1);
          });
      } else {
        console.log("Aborted. No changes made.");
        process.exit(0);
      }
    }
  );
}

confirmAndRun();
