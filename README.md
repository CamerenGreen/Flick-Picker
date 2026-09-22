# Flick Picker

A full stack movie and show recommender with a Chrome extension, a Python API, SQLite history, and a **locally trained recommendation model**. The model is implemented in this repository. It learns a weighted TF-IDF vocabulary from the catalog and ranks unseen titles against a profile built from a user's watched titles and optional 1–5 ratings. It retrains when new titles enter the catalog. No hosted model or recommender API is used.

The bundled 28-title movie and show catalog works without credentials. For a larger searchable catalog, add a [TMDB API key](https://developer.themoviedb.org/docs/getting-started) as `TMDB_API_KEY` on the backend, then use **Sync movies** and **Sync shows** in Settings to add recommendation candidates. The key is never put in the extension. TMDB search results are also imported when a user watches one. IMDb is not used because this implementation uses TMDB's documented API.

## Run locally

Use Python 3.12 or newer:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend\requirements.txt
.venv\Scripts\python -m uvicorn backend.app.main:app --reload --port 8000
```

Open the [browser demo](http://127.0.0.1:8000). Click **Try a ready-made demo** to create a local profile with *The Matrix* watched, then see recommendations immediately. You can also create your own profile, search titles, and mark movies and shows as watched.

To load the Chrome extension, open `chrome://extensions`, enable Developer mode, click **Load unpacked**, and select `frontend/extension`. The extension is plain JavaScript; no Node build step is needed. Keep the backend running at `http://127.0.0.1:8000`. The Settings page allows another backend URL, but additional origins require matching Chrome host permissions in `manifest.json`.

Docker is also supported with `docker compose up --build`. Set `TMDB_API_KEY` in `.env` first if you want live TMDB search.

## API and model

- `GET /catalog?media_type=movie|tv|all` and `GET /search?q=...` list local titles and optionally search TMDB.
- `POST /users`, `POST /users/{id}/history`, `GET /users/{id}/history` save and retrieve a profile. Add history using `media_id`, or `source="tmdb"`, `source_id`, and `media_type` for a TMDB result.
- `GET /users/{id}/recommend` returns ranked unseen titles and short explanations.
- `POST /tmdb/sync_popular?media_type=movie|tv` imports popular titles; `POST /train` explicitly retrains; `GET /model/status` shows the trained catalog size.

The model file and SQLite database live in `backend/storage/`. The starter catalog is intended for demonstration; recommendation quality grows with a larger, richer catalog. Viewing history is entered by the user; the extension does not monitor streaming sites.

Run tests with `.venv\Scripts\python -m pytest backend/tests -q`.
