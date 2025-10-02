#!/usr/bin/env python3
"""
Encodes a text prompt using the project's centralized embedding model
and queries the Qdrant 'watched_frames' collection.

Usage: python3 test/search/search_text.py --text "a dog playing on the grass"
"""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient

# --- Fix Python's Import Path ---
# Add the project's root directory (the one containing 'src', 'config', 'models')
# to the system path. This allows us to import modules from anywhere in the project.
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
# --------------------------------

# Use the centralized embedding function from your pipeline's source code
from src.infer_embeds import encode_text_batch


def main():
    parser = argparse.ArgumentParser(description="Search watched_frames by text prompt.")
    parser.add_argument("--text", required=True, help="Text query to embed.")
    parser.add_argument("--limit", type=int, default=5, help="Number of results to return.")
    parser.add_argument(
        "--collection", default="watched_frames", help="Name of the Qdrant collection to search."
    )
    args = parser.parse_args()

    # Load environment variables from the project root .env file
    load_dotenv(project_root / ".env")
    url = os.getenv("QDRANT_URL")
    key = os.getenv("QDRANT_KEY")
    if not url or not key:
        print("❌ QDRANT_URL and QDRANT_KEY must be set in your .env file.")
        sys.exit(1)

    print(f"Connecting to Qdrant at {url}...")
    client = QdrantClient(url=url, api_key=key)

    # Embed the text prompt using the same function as the main pipeline
    print(f"Embedding text: '{args.text}'...")
    # encode_batch expects a list of items to encode
    vector = encode_text_batch([args.text])[0]

    # Perform search on the correct collection
    print(f"Searching collection '{args.collection}'...")
    hits = client.search(
        collection_name=args.collection,
        query_vector=vector,
        limit=args.limit,
        with_payload=True,  # Include the payload data in the results
        with_vectors=False,  # We usually don't need to see the vector itself
    )

    # Display results cleanly
    print(f"\n✅ Found {len(hits)} results:")
    for i, hit in enumerate(hits):
        print(f"\n--- Result {i+1} ---")
        print(f"  ID             : {hit.id}")
        print(f"  Smiliarity     : {hit.score:.4f}")
        # Pretty print the payload dictionary
        for key, value in hit.payload.items():
            print(f"  {key:<15}: {value}")


if __name__ == "__main__":
    main()
