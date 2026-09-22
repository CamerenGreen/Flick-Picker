"""Locally trained weighted TF-IDF model and cosine user profile."""
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone

from . import db as database

MODEL_PATH = database.DATA_DIR / "content_model.json"
TOKEN = re.compile(r"[a-z0-9]{2,}")


def _features(row):
    words = list(TOKEN.findall(row["overview"].lower()))
    for value in json.loads(row["genres"]) + json.loads(row["tags"]):
        words.extend(TOKEN.findall(value.lower()) * 4)
    words.append("type_" + row["media_type"])
    return Counter(words)


def train_model(connection):
    rows = connection.execute("SELECT * FROM media ORDER BY id").fetchall()
    if len(rows) < 2:
        raise ValueError("At least two catalog titles are required to train")
    documents = [_features(row) for row in rows]
    document_frequency = Counter(token for doc in documents for token in doc)
    count = len(documents)
    idf = {token: math.log((1 + count) / (1 + frequency)) + 1
           for token, frequency in document_frequency.items()}
    vectors = {}
    for row, doc in zip(rows, documents):
        vector = {token: (1 + math.log(frequency)) * idf[token]
                  for token, frequency in doc.items()}
        norm = math.sqrt(sum(value * value for value in vector.values())) or 1
        vectors[str(row["id"])] = {token: value / norm for token, value in vector.items()}
    model = {"algorithm": "weighted TF-IDF + cosine user profile", "item_count": count,
             "catalog_ids": [row["id"] for row in rows], "idf": idf, "vectors": vectors,
             "trained_at": datetime.now(timezone.utc).isoformat()}
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps(model), encoding="utf-8")
    return model


def load_or_train(connection):
    ids = [row[0] for row in connection.execute("SELECT id FROM media ORDER BY id")]
    if MODEL_PATH.exists():
        try:
            model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
            if model.get("catalog_ids") == ids:
                return model
        except (ValueError, OSError):
            pass
    return train_model(connection)


def recommend_for_user(connection, user_id, top_k=10):
    model = load_or_train(connection)
    watched = connection.execute("""
        SELECT media_id, rating, watched_at FROM viewing_history
        WHERE user_id = ? ORDER BY watched_at DESC, media_id DESC
    """, (user_id,)).fetchall()
    if not watched:
        return []
    profile = Counter()
    watched_ids = set()
    for position, item in enumerate(watched):
        media_id = item["media_id"]
        watched_ids.add(media_id)
        weight = (item["rating"] or 3) / 3 * (0.92 ** position)
        for token, value in model["vectors"].get(str(media_id), {}).items():
            profile[token] += weight * value
    norm = math.sqrt(sum(value * value for value in profile.values())) or 1
    for token in profile:
        profile[token] /= norm
    scored = []
    for row in connection.execute("SELECT * FROM media"):
        if row["id"] in watched_ids:
            continue
        vector = model["vectors"].get(str(row["id"]), {})
        score = sum(profile.get(token, 0) * value for token, value in vector.items())
        shared = [tag for tag in json.loads(row["genres"]) + json.loads(row["tags"])
                  if any(token in profile for token in TOKEN.findall(tag.lower()))]
        scored.append({"media": dict(row), "score": round(score, 4),
                       "reason": "Matches your interest in " + ", ".join(shared[:2])
                       if shared else "Similar to titles in your watch history"})
    scored.sort(key=lambda item: (-item["score"], item["media"]["title"]))
    return scored[:top_k]
