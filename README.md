# Flick-Picker — Movie Recommender

This project provides a simple movie/show recommender system that uses TMDB (The Movie Database) as the data source and a lightweight machine learning pipeline to recommend items based on a user's viewing history.

Features
- FastAPI backend (Python)
- SQLite database (simple, file-based for quick shipping)
- TMDB client to fetch movie metadata (requires TMDB_API_KEY)
- Simple item-item recommender using TruncatedSVD and cosine similarity
- Minimal frontend (single-page HTML) for demo usage
- Dockerfile and docker-compose for containerized shipping

Quick start (local, using Docker)

1. Copy `.env.example` to `.env` and add your TMDB API key.
2. Build and run with Docker Compose:

```powershell
docker compose up --build
```

3. Open http://localhost:8000 in your browser.

Notes
- The TMDB API key is required and must be set in environment variable `TMDB_API_KEY`.
- This is a starter implementation intended to be extended (auth, improved model, background jobs, better frontend).

Files of interest
- `backend/app/main.py` — FastAPI app entry
- `backend/app/tmdb_client.py` — TMDB wrapper
- `backend/app/recommender.py` — model training and recommendation logic
- `backend/app/models.py` — database models
- `frontend/index.html` — minimal UI
 - `frontend/extension/` — Chrome extension source, TypeScript Preact popup and options page, build pipeline

Extension build & install
1. Open a terminal and install dependencies for the extension:

```cmd
cd frontend\extension
npm install
```

2. Build extension bundles (uses esbuild):

```cmd
npm run build
```

3. Load the extension in Chrome (Developer mode) by selecting `frontend/extension` as the unpacked extension folder. If you don't build, a fallback plain JS popup exists but the Preact features will not be active.


License: MIT
# Flick-Picker
Recommends movies and shows based on a user's viewing history, powered with the TMBD database
