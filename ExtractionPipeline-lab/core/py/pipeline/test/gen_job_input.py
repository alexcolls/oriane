#!/usr/bin/env python3
"""
gather_10kvideos.py
────────────────────
Create a JOB_INPUT-style JSON list by querying the `insta_contents` table.

Usage examples
--------------
# Plain stdout (pipe straight into docker run)
python make_job_input_from_db.py > job_input.json

# Custom limit / order column
python make_job_input_from_db.py --limit 5000 --order-col scraped_at \
                                 --outfile job_input.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import DictCursor

# --------------------------------------------------------------------------- #
# env / CLI                                                                   #
# --------------------------------------------------------------------------- #
load_dotenv("../.env")

parser = argparse.ArgumentParser(description="Dump a JOB_INPUT JSON list from insta_contents.")
parser.add_argument("--limit", type=int, default=10_000, help="How many most-recent rows to export")
parser.add_argument(
    "--order-col", default="created_at", help="Timestamp column used for recency sorting"
)
parser.add_argument("--outfile", default="job_input.json", help="Path to write JSON (- for stdout)")
args = parser.parse_args()

try:
    limit = int(args.limit)
    order_col = args.order_col
except ValueError:
    sys.exit("limit must be an integer")

# --------------------------------------------------------------------------- #
# connect                                                                     #
# --------------------------------------------------------------------------- #
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
    sys.exit("DB_HOST, DB_NAME, DB_USER, DB_PASSWORD must be set in .env")

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    cursor_factory=DictCursor,
)

# --------------------------------------------------------------------------- #
# query & build JSON                                                          #
# --------------------------------------------------------------------------- #
with conn, conn.cursor() as cur:
    cur.execute(
        f"""
        SELECT code
        FROM   insta_content
        WHERE  is_downloaded = true
        ORDER  BY {order_col} DESC
        LIMIT  %s
        """,
        [limit],
    )
    rows: List[Dict[str, str]] = cur.fetchall()

job_input = [{"platform": "instagram", "code": r["code"]} for r in rows]

# --------------------------------------------------------------------------- #
# output                                                                      #
# --------------------------------------------------------------------------- #
out_json = json.dumps(job_input, separators=(",", ":"), indent=2)
if args.outfile == "-" or args.outfile == "":
    print(out_json)
else:
    with open(args.outfile, "w", encoding="utf-8") as fh:
        fh.write(out_json)
    print(f"✔ wrote {len(job_input):,} items to {args.outfile}")
