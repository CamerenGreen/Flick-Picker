import os
import requests
from typing import Dict, Any, List

TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
TMDB_BASE = 'https://api.themoviedb.org/3'

if not TMDB_API_KEY:
    # We won't raise here; endpoints will return an error if called without a key.
    pass


def _get(path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    if params is None:
        params = {}
    if not TMDB_API_KEY:
        raise RuntimeError('TMDB_API_KEY not set')
    params['api_key'] = TMDB_API_KEY
    resp = requests.get(TMDB_BASE + path, params=params)
    resp.raise_for_status()
    return resp.json()


def fetch_popular_movies(page: int = 1) -> List[Dict[str, Any]]:
    data = _get('/movie/popular', params={'page': page})
    return data.get('results', [])


def fetch_movie_details(tmdb_id: int) -> Dict[str, Any]:
    return _get(f'/movie/{tmdb_id}', params={'append_to_response': 'credits'})
