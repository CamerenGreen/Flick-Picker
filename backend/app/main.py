"""Flick Picker API and static extension demo."""
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import catalog, db, recommender, tmdb_client


@asynccontextmanager
async def lifespan(_app):
    db.init_db()
    catalog.seed_catalog()
    with db.connect() as connection:
        recommender.load_or_train(connection)
    yield


app = FastAPI(title="Flick Picker", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)


class ViewingCreate(BaseModel):
    media_id: int | None = None
    source: Literal["tmdb"] | None = None
    source_id: str | None = None
    media_type: Literal["movie", "tv"] | None = None
    rating: float | None = Field(default=None, ge=1, le=5)


def serialize(row):
    item = dict(row)
    item["genres"] = json.loads(item["genres"])
    item["tags"] = json.loads(item["tags"])
    item["poster_url"] = ("https://image.tmdb.org/t/p/w342" + item["poster_path"]
                          if item["poster_path"] else None)
    return item


def require_user(connection, user_id):
    if not connection.execute("SELECT 1 FROM users WHERE id=?", (user_id,)).fetchone():
        raise HTTPException(404, "User not found")


@app.get("/health")
def health():
    return {"status": "ok", "tmdb_enabled": tmdb_client.enabled()}


@app.get("/catalog")
def list_catalog(media_type: Literal["all", "movie", "tv"] = "all", limit: int = Query(60, ge=1, le=200)):
    with db.connect() as connection:
        if media_type == "all":
            rows = connection.execute("SELECT * FROM media ORDER BY title LIMIT ?", (limit,)).fetchall()
        else:
            rows = connection.execute("SELECT * FROM media WHERE media_type=? ORDER BY title LIMIT ?",
                                      (media_type, limit)).fetchall()
        return [serialize(row) for row in rows]


@app.get("/search")
def search(q: str = Query(min_length=1), media_type: Literal["all", "movie", "tv"] = "all"):
    with db.connect() as connection:
        pattern = "%" + q.strip().replace("%", "\\%").replace("_", "\\_") + "%"
        if media_type == "all":
            rows = connection.execute("SELECT * FROM media WHERE title LIKE ? ESCAPE '\\' ORDER BY title LIMIT 20", (pattern,)).fetchall()
        else:
            rows = connection.execute("SELECT * FROM media WHERE media_type=? AND title LIKE ? ESCAPE '\\' ORDER BY title LIMIT 20",
                                      (media_type, pattern)).fetchall()
        local = [serialize(row) for row in rows]
    remote = []
    if tmdb_client.enabled() and len(local) < 5:
        try:
            remote = tmdb_client.search(q, media_type)
        except Exception:
            pass  # local catalog remains searchable if TMDB is unavailable
    existing = {(item["source"], item["source_id"], item["media_type"]) for item in local}
    return local + [item for item in remote if (item["source"], item["source_id"], item["media_type"]) not in existing]


@app.post("/users", status_code=201)
def create_user(body: UserCreate):
    if not body.name.strip():
        raise HTTPException(422, "Name cannot be blank")
    with db.connect() as connection:
        cursor = connection.execute("INSERT INTO users(name) VALUES (?)", (body.name.strip(),))
        return {"id": cursor.lastrowid, "name": body.name.strip()}


@app.get("/users/{user_id}")
def get_user(user_id: int):
    with db.connect() as connection:
        row = connection.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        return dict(row)


@app.get("/users/{user_id}/history")
def get_history(user_id: int):
    with db.connect() as connection:
        require_user(connection, user_id)
        rows = connection.execute("""SELECT media.*, viewing_history.rating, viewing_history.watched_at
            FROM viewing_history JOIN media ON media.id=viewing_history.media_id
            WHERE user_id=? ORDER BY watched_at DESC, media.id DESC""", (user_id,)).fetchall()
        return [serialize(row) for row in rows]


@app.post("/users/{user_id}/history", status_code=201)
def add_history(user_id: int, body: ViewingCreate):
    with db.connect() as connection:
        require_user(connection, user_id)
        media_id = body.media_id
        if media_id is None:
            if body.source != "tmdb" or not body.source_id or not body.media_type:
                raise HTTPException(422, "Provide media_id or TMDB source_id and media_type")
            if not body.source_id.isdecimal():
                raise HTTPException(422, "TMDB source_id must be numeric")
            row = connection.execute("SELECT id FROM media WHERE source='tmdb' AND source_id=? AND media_type=?",
                                     (body.source_id, body.media_type)).fetchone()
            if row:
                media_id = row["id"]
            else:
                try:
                    item = tmdb_client.details(body.source_id, body.media_type)
                except Exception as exc:
                    raise HTTPException(502, f"TMDB import failed: {exc}") from exc
                cursor = connection.execute("""INSERT INTO media
                    (source, source_id, media_type, title, overview, genres, tags, year, poster_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (item["source"], item["source_id"], item["media_type"], item["title"],
                     item["overview"], json.dumps(item["genres"]), json.dumps(item["tags"]),
                     item["year"], item["poster_path"]))
                media_id = cursor.lastrowid
        row = connection.execute("SELECT * FROM media WHERE id=?", (media_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Title not found")
        connection.execute("""INSERT INTO viewing_history(user_id, media_id, rating)
            VALUES (?, ?, ?) ON CONFLICT(user_id, media_id)
            DO UPDATE SET rating=excluded.rating, watched_at=CURRENT_TIMESTAMP""",
            (user_id, media_id, body.rating))
        return {"ok": True, "media": serialize(row)}


@app.get("/users/{user_id}/recommend")
def recommend(user_id: int, top_k: int = Query(8, ge=1, le=50)):
    with db.connect() as connection:
        require_user(connection, user_id)
        result = recommender.recommend_for_user(connection, user_id, top_k)
        return [{**serialize(item["media"]), "score": item["score"], "reason": item["reason"]}
                for item in result]


@app.post("/train")
def train():
    with db.connect() as connection:
        model = recommender.train_model(connection)
        return {"algorithm": model["algorithm"], "item_count": model["item_count"],
                "trained_at": model["trained_at"]}


@app.post("/tmdb/sync_popular")
def sync_popular(media_type: Literal["movie", "tv"] = "movie", page: int = Query(1, ge=1, le=50)):
    if not tmdb_client.enabled():
        raise HTTPException(400, "Configure TMDB_API_KEY on the backend first")
    try:
        ids = tmdb_client.popular(media_type, page)
    except Exception as exc:
        raise HTTPException(502, f"TMDB sync failed: {exc}") from exc
    added = 0
    failed = 0
    with db.connect() as connection:
        for source_id in ids:
            if connection.execute("SELECT 1 FROM media WHERE source='tmdb' AND source_id=? AND media_type=?",
                                  (source_id, media_type)).fetchone():
                continue
            try:
                item = tmdb_client.details(source_id, media_type)
                connection.execute("""INSERT INTO media
                    (source, source_id, media_type, title, overview, genres, tags, year, poster_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (item["source"], item["source_id"], item["media_type"], item["title"],
                     item["overview"], json.dumps(item["genres"]), json.dumps(item["tags"]),
                     item["year"], item["poster_path"]))
                added += 1
            except Exception:
                failed += 1
        model = recommender.load_or_train(connection)
    return {"added": added, "failed": failed, "item_count": model["item_count"]}


@app.get("/model/status")
def model_status():
    with db.connect() as connection:
        model = recommender.load_or_train(connection)
        return {"algorithm": model["algorithm"], "item_count": model["item_count"],
                "trained_at": model["trained_at"], "local": True}


FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
