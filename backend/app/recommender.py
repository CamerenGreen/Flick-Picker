import os
from typing import List, Dict
import joblib
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
import crud

# Simple file paths
STORAGE_DIR = os.environ.get('STORAGE_DIR') or './storage'
MODEL_PATH = os.environ.get('MODEL_PATH') or os.path.join(STORAGE_DIR, 'model.joblib')
ITEM_IDX_PATH = os.environ.get('ITEM_IDX_PATH') or os.path.join(STORAGE_DIR, 'item_index.joblib')


def train_model(db: Session, n_components: int = 50):
    """Train item embeddings using viewing history.

    Build a user-item interaction matrix (binary: watched=1) and compute item
    embeddings using TruncatedSVD.
    """
    movies = crud.list_all_movies(db)
    movie_id_to_idx = {m.id: i for i, m in enumerate(movies)}
    users = db.query(crud.models.User).all()
    user_id_to_idx = {u.id: i for i, u in enumerate(users)}

    if len(movies) == 0 or len(users) == 0:
        raise RuntimeError('Not enough data to train')

    mat = np.zeros((len(users), len(movies)), dtype=float)
    for vh in db.query(crud.models.ViewingHistory).all():
        ui = user_id_to_idx.get(vh.user_id)
        mi = movie_id_to_idx.get(vh.movie_id)
        if ui is not None and mi is not None:
            mat[ui, mi] = 1.0

    # Use truncated SVD to get item latent features
    k = min(n_components, min(mat.shape)-1)
    svd = TruncatedSVD(n_components=max(2, k))
    svd.fit(mat)
    # item embeddings are columns of V^T -> components_.T
    item_embeddings = svd.components_.T  # shape (n_items, k)

    os.makedirs(STORAGE_DIR, exist_ok=True)
    joblib.dump({'svd': svd, 'item_embeddings': item_embeddings}, MODEL_PATH)
    joblib.dump({'movie_ids': [m.id for m in movies], 'tmdb_ids': [m.tmdb_id for m in movies]}, ITEM_IDX_PATH)
    return True


def load_model():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(ITEM_IDX_PATH):
        return None
    m = joblib.load(MODEL_PATH)
    idx = joblib.load(ITEM_IDX_PATH)
    return m['item_embeddings'], idx


def recommend_for_user(db: Session, user_id: int, top_k: int = 10) -> List[Dict]:
    model = load_model()
    if model is None:
        # train on the fly
        train_model(db, n_components=30)
        model = load_model()
    item_embeddings, idx = model
    movie_ids = idx['movie_ids']
    # build movie id -> index
    movie_to_index = {mid: i for i, mid in enumerate(movie_ids)}

    # get user's watched movie indices
    watched = [vh.movie_id for vh in crud.get_user_history(db, user_id)]
    watched_idx = [movie_to_index[m] for m in watched if m in movie_to_index]
    if not watched_idx:
        return []

    # compute similarity between watched items and all items
    watched_emb = item_embeddings[watched_idx]  # (w, k)
    sims = cosine_similarity(watched_emb, item_embeddings)  # (w, n_items)
    # aggregate scores
    scores = sims.mean(axis=0)

    # zero out watched
    for wi in watched_idx:
        scores[wi] = -1.0

    top_indices = list(np.argsort(scores)[::-1][:top_k])
    # return movie ids and scores
    return [{'movie_db_id': movie_ids[i], 'score': float(scores[i])} for i in top_indices]


def recommend_for_movie(db: Session, tmdb_id: int, top_k: int = 10) -> List[Dict]:
    """Recommend movies similar to the given TMDB movie id.

    Returns items as dicts with 'movie_db_id' and 'score'.
    """
    model = load_model()
    if model is None:
        # try to train quickly if possible
        train_model(db, n_components=30)
        model = load_model()
    if model is None:
        raise RuntimeError('Model not available')

    item_embeddings, idx = model
    movie_ids = idx['movie_ids']
    tmdb_ids = idx.get('tmdb_ids')
    if tmdb_ids is None:
        raise RuntimeError('Index missing tmdb_ids')

    # find index for given tmdb_id
    try:
        target_idx = tmdb_ids.index(tmdb_id)
    except ValueError:
        # movie not in index
        return []

    from sklearn.metrics.pairwise import cosine_similarity
    target_emb = item_embeddings[target_idx].reshape(1, -1)
    sims = cosine_similarity(target_emb, item_embeddings).flatten()
    sims[target_idx] = -1.0
    top_indices = list(np.argsort(sims)[::-1][:top_k])
    return [{'movie_db_id': movie_ids[i], 'score': float(sims[i])} for i in top_indices]
