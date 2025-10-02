#!/usr/bin/env python3
"""
Encodes an image using the project's centralized embedding model
and queries the Qdrant 'watched_frames' collection.

Usage:
    python test/search/search_image.py --image test/samples/images/your_image.png
"""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image
from qdrant_client import QdrantClient

# --- Fix Python's Import Path ---
# Add the project's root directory to the system path to find modules
# like 'src' and 'config'.
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
# --------------------------------

# Use the centralized function for encoding images from your pipeline's source
from src.infer_embeds import encode_image_batch


def main():
    parser = argparse.ArgumentParser(description="Search watched_frames by a query image.")
    parser.add_argument(
        "--image",
        type=Path,
        required=True,
        help="Path to the image file (e.g., 'test/samples/images/dog.png').",
    )
    parser.add_argument("--limit", type=int, default=5, help="Number of results to return.")
    parser.add_argument(
        "--collection", default="watched_frames", help="Name of the Qdrant collection to search."
    )
    args = parser.parse_args()

    if not args.image.is_file():
        sys.exit(f"❌ Error: Image file not found at '{args.image}'")

    # Load environment variables from the project root .env file
    load_dotenv(project_root / ".env")
    url = os.getenv("QDRANT_URL")
    key = os.getenv("QDRANT_KEY")
    if not url or not key:
        sys.exit("❌ QDRANT_URL and QDRANT_KEY must be set in your .env file.")

    print(f"Connecting to Qdrant at {url}...")
    client = QdrantClient(url=url, api_key=key)

    # Load the image and encode it using the centralized function
    print(f"Embedding image: '{args.image.name}'...")
    try:
        img = Image.open(args.image)
        # encode_image_batch expects a list of items to encode
        vector = encode_image_batch([img])[0]
    except Exception as e:
        sys.exit(f"❌ Failed to load or embed the image. Error: {e}")

    # Perform search on the correct collection
    print(f"Searching collection '{args.collection}'...")
    hits = client.search(
        collection_name=args.collection,
        query_vector=vector,
        limit=args.limit,
        with_payload=True,
        with_vectors=False,
    )

    # Display results cleanly
    print(f"\n✅ Found {len(hits)} results for '{args.image.name}':")
    for i, hit in enumerate(hits):
        print(f"\n--- Result {i+1} ---")
        print(f"  ID             : {hit.id}")
        print(f"  Smiliarity     : {hit.score:.4f}")
        # Pretty print the payload dictionary
        payload = hit.payload or {}
        for key, value in payload.items():
            print(f"  {key:<15}: {value}")


if __name__ == "__main__":
    main()
