import numpy as np

def search_by_image(img_path, top_k=20, filters=None):
    vec = model.encode_image(Image.open(img_path).convert("RGB"))[0]
    return client.search(
        collection_name=COLL,
        query_vector=vec.tolist(),
        limit=top_k,
        query_filter=filters,
    )

def search_by_text(prompt, top_k=20, filters=None):
    vec = model.encode_text([prompt])[0]
    return client.search(COLL, query_vector=vec.tolist(), limit=top_k, query_filter=filters)

def parse_key(key: str):
    """
    Returns (platform, video_code, id_, frame_n, sec) or None if pattern unknown.
    • Public:   platform/video-code/ n _ sec .png
    • Oriane:   oriane/<user_uuid>/<video_uuid>/ n _ sec .png
                video_code = "<user_uuid>.<video_uuid>"
                id_        = <video_uuid>
    """
    if not key.endswith(".png"):
        return None
    parts = key.split("/")
    if parts[0] == "oriane" and len(parts) == 4:
        _, user_uuid, video_uuid, filename = parts
        n, sec = filename[:-4].split("_")          # strip ".png"
        return ("oriane",
                f"{user_uuid}.{video_uuid}",       # video_code
                video_uuid,                        # id
                int(n), float(sec))
    elif len(parts) == 3:
        platform, video_code, filename = parts
        n, sec = filename[:-4].split("_")
        return (platform,
                video_code,
                video_code,                        # use video_code as id
                int(n), float(sec))
    else:
        return None
