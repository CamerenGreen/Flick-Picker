import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
import requests
import pathlib
import mimetypes
from sqlalchemy.orm import Session
import db, crud, tmdb_client, recommender, schemas

app = FastAPI(title='Flick-Picker')

# Enable CORS so the Chrome extension (and other origins) can call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # consider restricting in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event('startup')
def startup_event():
    """Try to initialize DB at startup with retries (useful when DB is in a separate container)."""
    import time
    attempts = 0
    max_attempts = 10
    wait_seconds = 2
    while attempts < max_attempts:
        try:
            db.init_db()
            break
        except Exception as e:
            attempts += 1
            print(f"DB init attempt {attempts} failed: {e}")
            time.sleep(wait_seconds)
    else:
        print('WARNING: could not initialize DB after retries')


def get_db():
    db_sess = db.SessionLocal()
    try:
        yield db_sess
    finally:
        db_sess.close()


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.post('/tmdb/sync_popular')
def sync_popular(page: int = 1, db: Session = Depends(get_db)):
    try:
        movies = tmdb_client.fetch_popular_movies(page=page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    added = 0
    for m in movies:
        tmdb_id = m['id']
        title = m.get('title') or m.get('name')
        details = tmdb_client.fetch_movie_details(tmdb_id)
        if crud.get_movie_by_tmdb(db, tmdb_id) is None:
            crud.create_movie(db, tmdb_id, title, details)
            added += 1
    return {'added': added, 'page': page}


@app.post('/users')
def create_user(u: schemas.UserCreate, db: Session = Depends(get_db)):
    user = crud.create_user(db, name=u.name)
    return user


@app.post('/users/{user_id}/history')
def add_history(user_id: int, v: schemas.ViewingCreate, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='user not found')
    # ensure movie is present
    try:
        details = tmdb_client.fetch_movie_details(v.tmdb_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail='TMDB error: ' + str(e))
    movie = crud.ensure_movie(db, v.tmdb_id, details.get('title') or details.get('name', ''), details)
    vh = crud.add_viewing(db, user_id=user_id, movie_db_id=movie.id)
    return {'ok': True, 'viewing_id': vh.id}


@app.get('/users/{user_id}')
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='user not found')
    return user


@app.post('/train')
def train(db: Session = Depends(get_db)):
    try:
        recommender.train_model(db)
        return {'ok': True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/users/{user_id}/recommend')
def recommend(user_id: int, top_k: int = 10, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='user not found')
    recs = recommender.recommend_for_user(db, user_id, top_k=top_k)
    # convert movie_db_id to TMDB ids and titles
    out = []
    for r in recs:
        movie = db.query(crud.models.Movie).filter(crud.models.Movie.id == r['movie_db_id']).first()
        if movie:
            # movie.data is stored as a JSON string; try to extract poster_path if available
            poster = None
            try:
                import json
                md = json.loads(movie.data) if movie.data else {}
                poster = md.get('poster_path') or md.get('poster', {}).get('file_path') if isinstance(md, dict) else None
            except Exception:
                poster = None
            out.append({'tmdb_id': movie.tmdb_id, 'title': movie.title, 'score': r['score'], 'poster_path': poster})
    return out


@app.get('/movies/{tmdb_id}')
def get_movie(tmdb_id: int, db: Session = Depends(get_db)):
    """Return stored movie metadata by TMDB id."""
    movie = crud.get_movie_by_tmdb(db, tmdb_id)
    if not movie:
        raise HTTPException(status_code=404, detail='movie not found')
    try:
        import json
        data = json.loads(movie.data) if movie.data else {}
    except Exception:
        data = {}
    return {'tmdb_id': movie.tmdb_id, 'title': movie.title, 'data': data}


@app.get('/movies/{tmdb_id}/recommend')
def recommend_movie(tmdb_id: int, top_k: int = 8, db: Session = Depends(get_db)):
    """Return movies similar to the given TMDB id."""
    # ensure movie exists
    movie = crud.get_movie_by_tmdb(db, tmdb_id)
    if not movie:
        raise HTTPException(status_code=404, detail='movie not found')
    try:
        recs = recommender.recommend_for_movie(db, tmdb_id, top_k=top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    out = []
    for r in recs:
        m = db.query(crud.models.Movie).filter(crud.models.Movie.id == r['movie_db_id']).first()
        if not m:
            continue
        poster = None
        try:
            import json
            md = json.loads(m.data) if m.data else {}
            poster = md.get('poster_path') or (md.get('poster', {}) or {}).get('file_path')
        except Exception:
            poster = None
        out.append({'tmdb_id': m.tmdb_id, 'title': m.title, 'score': r['score'], 'poster_path': poster})
    return out


@app.get('/images/tmdb/{tmdb_id}/{kind}')
def image_proxy(tmdb_id: int, kind: str, size: str = 'w185', db: Session = Depends(get_db)):
    """Proxy and cache TMDB images server-side.

    kind: 'poster' or 'backdrop'
    size: TMDB size token like w185, w342, w780
    """
    if kind not in ('poster', 'backdrop'):
        raise HTTPException(status_code=400, detail='kind must be poster or backdrop')

    movie = crud.get_movie_by_tmdb(db, tmdb_id)
    if not movie:
        raise HTTPException(status_code=404, detail='movie not found')

    # load stored movie metadata
    try:
        import json
        md = json.loads(movie.data) if movie.data else {}
    except Exception:
        md = {}

    path_key = 'poster_path' if kind == 'poster' else 'backdrop_path'
    image_path = md.get(path_key)
    if not image_path:
        raise HTTPException(status_code=404, detail='image not available')

    # Prepare cache directory
    storage_dir = pathlib.Path(os.environ.get('STORAGE_DIR') or './backend/storage')
    images_dir = storage_dir / 'images'
    images_dir.mkdir(parents=True, exist_ok=True)

    # choose extension based on content-type later; for cache filename include tmdb id, kind and size
    cache_name = f"{tmdb_id}_{kind}_{size}"
    # try to find existing file with any known extension
    for ext in ('.jpg', '.jpeg', '.png', '.webp'):
        f = images_dir / (cache_name + ext)
        if f.exists():
            return FileResponse(str(f), media_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')

    # fetch from TMDB
    tmdb_url = f'https://image.tmdb.org/t/p/{size}{image_path}'
    resp = requests.get(tmdb_url, stream=True, timeout=15)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail='failed to fetch image from TMDB')

    content_type = resp.headers.get('content-type', 'image/jpeg')
    # determine extension
    ext = mimetypes.guess_extension(content_type.split(';')[0].strip()) or '.jpg'
    target = images_dir / (cache_name + ext)
    with open(target, 'wb') as fh:
        for chunk in resp.iter_content(8192):
            if chunk:
                fh.write(chunk)

    return FileResponse(str(target), media_type=content_type)


# Serve frontend static
frontend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend')
frontend_path = os.path.abspath(frontend_path)
if os.path.isdir(frontend_path):
    app.mount('/', StaticFiles(directory=frontend_path, html=True), name='frontend')
