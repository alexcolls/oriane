#!/usr/bin/env python3
import itertools
import json
import os
import re
from datetime import datetime, timezone

import boto3

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_VIDEOS_BUCKET = os.getenv("S3_VIDEOS_BUCKET", "oriane-contents")
PLATFORMS = {"instagram", "tiktok"}

s3 = boto3.client("s3", region_name=AWS_REGION)

items = []
paginator = s3.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket=S3_VIDEOS_BUCKET):
    for obj in page.get("Contents", []):
        key = obj["Key"]
        m = re.match(r"(?P<plat>[^/]+)/(?P<code>[^/]+)/video\.mp4$", key)
        if not m:  # skip everything that isn’t /<plat>/<code>/video.mp4
            continue
        if m["plat"] not in PLATFORMS:
            continue
        items.append({"platform": m["plat"], "code": m["code"], "ts": obj["LastModified"]})

# pick the 10 000 most-recent
items = sorted(items, key=lambda x: x["ts"], reverse=True)[:10_000]
job_input = [{"platform": it["platform"], "code": it["code"]} for it in items]
print(json.dumps(job_input))
