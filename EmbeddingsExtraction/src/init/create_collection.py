from qdrant_client import QdrantClient, models

DIM = 512
COLL = "video_frames"

client = QdrantClient(host="localhost", port=6333, prefer_grpc=True)

if not client.collection_exists(COLL):
    client.create_collection(
        collection_name=COLL,
        vectors_config=models.VectorParams(size=DIM,
                                           distance=models.Distance.COSINE),
    )
    # indices for fast payload-filtering
    for field in ("id", "platform", "video"):
        client.create_payload_index(COLL, field_name=field,
                                    field_schema=models.PayloadSchemaType.KEYWORD)
