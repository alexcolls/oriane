#!/usr/bin/env python3
"""
A generic, configuration-driven script to create a Qdrant collection.

This script reads all necessary parameters from a JSON configuration file,
making it reusable for any collection. It is idempotent and safe to run
multiple times.

Usage:
    python create_collection.py path/to/your_collection_config.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

load_dotenv("../../core/py/pipeline/.env")

# --- Helper Mappings from String to Qdrant Enum ---

DISTANCE_MAP = {
    "COSINE": models.Distance.COSINE,
    "EUCLID": models.Distance.EUCLID,
    "DOT": models.Distance.DOT,
}

SCHEMA_TYPE_MAP = {
    "KEYWORD": models.PayloadSchemaType.KEYWORD,
    "INTEGER": models.PayloadSchemaType.INTEGER,
    "FLOAT": models.PayloadSchemaType.FLOAT,
    "GEO": models.PayloadSchemaType.GEO,
    "TEXT": models.PayloadSchemaType.TEXT,
    "BOOL": models.PayloadSchemaType.BOOL,
    "DATETIME": models.PayloadSchemaType.DATETIME,
}


def create_collection_from_config(config_path: Path):
    """
    Connects to Qdrant and creates a collection based on a JSON config file.
    """
    # --- 1. Load Configuration ---
    print(f"📄 Loading configuration from: {config_path}")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        collection_name = config["collection_name"]
        vector_params = config["vector_params"]
        payload_indexes = config.get("payload_indexes", [])
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        sys.exit(f"❌  Error loading or parsing config file: {e}")

    # --- 2. Connect to Qdrant ---
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_key = os.getenv("QDRANT_KEY")

    if not qdrant_url or not qdrant_key:
        sys.exit("❌  QDRANT_URL and QDRANT_KEY must be set in your .env file")

    print(f"Connecting to Qdrant at {qdrant_url}...")
    try:
        client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
        client.get_collections()
        print("✅  Connection successful.")
    except Exception as e:
        sys.exit(f"❌  Could not connect to Qdrant. Error: {e}")

    # --- 3. Create Collection (if it doesn't exist) ---
    try:
        existing_collections = [c.name for c in client.get_collections().collections]
        if collection_name in existing_collections:
            print(f"✅  Collection '{collection_name}' already exists.")
        else:
            print(f"➕  Creating collection '{collection_name}'...")
            distance_enum = DISTANCE_MAP.get(vector_params["distance"].upper())
            if not distance_enum:
                sys.exit(f"❌ Invalid distance metric: {vector_params['distance']}")

            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_params["size"],
                    distance=distance_enum,
                ),
            )
            print("    Collection created successfully.")

    except Exception as e:
        sys.exit(f"❌  An error occurred during collection creation: {e}")

    # --- 4. Create Payload Indexes (if they don't exist) ---
    try:
        info = client.get_collection(collection_name=collection_name)
        existing_indexes = info.payload_schema.keys()

        for index_config in payload_indexes:
            field_name = index_config["field_name"]
            if field_name in existing_indexes:
                print(f"✅  Payload index for '{field_name}' already exists.")
                continue

            print(f"➕  Creating payload index for '{field_name}'...")
            schema_type_enum = SCHEMA_TYPE_MAP.get(index_config["field_schema"].upper())
            if not schema_type_enum:
                print(
                    f"⚠️  Warning: Invalid schema type '{index_config['field_schema']}' for field '{field_name}'. Skipping."
                )
                continue

            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=schema_type_enum,
                wait=True,
            )
            print(f"    Index for '{field_name}' created.")
    except Exception as e:
        sys.exit(f"❌  An error occurred during payload index creation: {e}")

    # --- 5. Final Summary ---
    print("\n─ Final Collection Summary ─")
    final_info = client.get_collection(collection_name=collection_name)
    print(f"  Name          : {collection_name}")
    print(f"  Vector size   : {final_info.config.params.vectors.size}")
    print(f"  Distance      : {final_info.config.params.vectors.distance}")
    print(f"  Points count  : {final_info.points_count}")
    print(f"  Payload indexes : {list(final_info.payload_schema.keys())}")
    print("\n🎉  Process complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a Qdrant collection from a JSON config file."
    )
    parser.add_argument(
        "config_file",
        type=Path,
        help="Path to the JSON file defining the collection.",
    )
    args = parser.parse_args()

    if not args.config_file.is_file():
        sys.exit(f"❌  Configuration file not found at: {args.config_file}")

    create_collection_from_config(args.config_file)
