import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import db, recommender
from backend.app import tmdb_client
from backend.app.main import app


def test_demo_recommends_after_one_watch(monkeypatch):
    with tempfile.TemporaryDirectory() as folder:
        monkeypatch.setattr(db, "DB_PATH", Path(folder) / "test.sqlite3")
        monkeypatch.setattr(recommender, "MODEL_PATH", Path(folder) / "model.json")
        with TestClient(app) as client:
            status = client.get("/model/status").json()
            assert status["local"] and status["item_count"] >= 20
            media = client.get("/search", params={"q": "Matrix"}).json()[0]
            user = client.post("/users", json={"name": "Tester"}).json()
            response = client.post(f"/users/{user['id']}/history", json={"media_id": media["id"], "rating": 5})
            assert response.status_code == 201
            recs = client.get(f"/users/{user['id']}/recommend").json()
            assert recs and all(item["id"] != media["id"] for item in recs)
            assert all(item["reason"] for item in recs)
            assert client.get(f"/users/{user['id']}/history").json()[0]["title"] == "The Matrix"


def test_invalid_user_and_title(monkeypatch):
    with tempfile.TemporaryDirectory() as folder:
        monkeypatch.setattr(db, "DB_PATH", Path(folder) / "test.sqlite3")
        monkeypatch.setattr(recommender, "MODEL_PATH", Path(folder) / "model.json")
        with TestClient(app) as client:
            assert client.get("/users/999/recommend").status_code == 404
            user = client.post("/users", json={"name": "Tester"}).json()
            assert client.post(f"/users/{user['id']}/history", json={"media_id": 9999}).status_code == 404
            assert client.post(f"/users/{user['id']}/history", json={"media_id": 1, "rating": 7}).status_code == 422


def test_tmdb_sync_retrains_for_show(monkeypatch):
    with tempfile.TemporaryDirectory() as folder:
        monkeypatch.setattr(db, "DB_PATH", Path(folder) / "test.sqlite3")
        monkeypatch.setattr(recommender, "MODEL_PATH", Path(folder) / "model.json")
        monkeypatch.setattr(tmdb_client, "enabled", lambda: True)
        monkeypatch.setattr(tmdb_client, "popular", lambda media_type, page: ["42"])
        monkeypatch.setattr(tmdb_client, "details", lambda source_id, media_type: {
            "source": "tmdb", "source_id": source_id, "media_type": media_type,
            "title": "Sample Show", "overview": "A science fiction mystery across time.",
            "genres": ["Science Fiction"], "tags": ["time travel"], "year": 2024,
            "poster_path": None,
        })
        with TestClient(app) as client:
            before = client.get("/model/status").json()["item_count"]
            response = client.post("/tmdb/sync_popular?media_type=tv")
            assert response.status_code == 200
            assert response.json()["item_count"] == before + 1
            assert response.json()["added"] == 1
            assert client.get("/search?q=Sample").json()[0]["media_type"] == "tv"
