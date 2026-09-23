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
            headers = {"Authorization": f"Bearer {user['token']}"}
            response = client.post(f"/users/{user['id']}/history", json={"media_id": media["id"], "rating": 5}, headers=headers)
            assert response.status_code == 201
            recs = client.get(f"/users/{user['id']}/recommend", headers=headers).json()
            assert recs and all(item["id"] != media["id"] for item in recs)
            assert all(item["reason"] for item in recs)
            assert client.get(f"/users/{user['id']}/history", headers=headers).json()[0]["title"] == "The Matrix"
            assert client.get(f"/users/{user['id']}/history").status_code == 401


def test_invalid_user_and_title(monkeypatch):
    with tempfile.TemporaryDirectory() as folder:
        monkeypatch.setattr(db, "DB_PATH", Path(folder) / "test.sqlite3")
        monkeypatch.setattr(recommender, "MODEL_PATH", Path(folder) / "model.json")
        with TestClient(app) as client:
            assert client.get("/users/999/recommend").status_code == 404
            user = client.post("/users", json={"name": "Tester"}).json()
            headers = {"Authorization": f"Bearer {user['token']}"}
            assert client.post(f"/users/{user['id']}/history", json={"media_id": 9999}, headers=headers).status_code == 404
            assert client.post(f"/users/{user['id']}/history", json={"media_id": 1, "rating": 7}, headers=headers).status_code == 422


def test_tmdb_sync_retrains_for_show(monkeypatch):
    with tempfile.TemporaryDirectory() as folder:
        monkeypatch.setattr(db, "DB_PATH", Path(folder) / "test.sqlite3")
        monkeypatch.setattr(recommender, "MODEL_PATH", Path(folder) / "model.json")
        monkeypatch.setenv("ADMIN_TOKEN", "test-admin-token")
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
            response = client.post("/tmdb/sync_popular?media_type=tv",
                                   headers={"X-Admin-Token": "test-admin-token"})
            assert response.status_code == 200
            assert response.json()["item_count"] == before + 1
            assert response.json()["added"] == 1
            assert client.get("/search?q=Sample").json()[0]["media_type"] == "tv"
