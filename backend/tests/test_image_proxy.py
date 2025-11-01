import os
import os
import time
import glob
import requests

BACKEND = os.environ.get('TEST_BACKEND_URL', 'http://localhost:8000')
STORAGE_DIR = os.environ.get('STORAGE_DIR', os.path.join(os.path.dirname(__file__), '..', 'storage'))
# Use a commonly-known TMDB id; we'll use 550 (Fight Club). If your app uses a different dataset, set TEST_TMDB_ID.
TMDB_ID = int(os.environ.get('TEST_TMDB_ID', '550'))


def wait_for_status(url, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=5)
            return r
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for {url}")


def test_image_proxy_caches_and_serves():
    # 1) create a temporary user so we can ensure the movie is present in DB (POST /users, POST /users/{id}/history)
    create_resp = requests.post(BACKEND.rstrip('/') + '/users', json={'name': 'pytest-integ'})
    assert create_resp.status_code in (200, 201)
    user = create_resp.json()
    user_id = user.get('id')
    assert user_id is not None

    # 2) add watched history which will fetch movie details and store the movie
    hist_resp = requests.post(BACKEND.rstrip('/') + f'/users/{user_id}/history', json={'tmdb_id': TMDB_ID})
    assert hist_resp.status_code in (200, 201)

    # 3) request the proxy image endpoint
    img_url = BACKEND.rstrip('/') + f'/images/tmdb/{TMDB_ID}/poster?size=w185'
    resp = wait_for_status(img_url, timeout=30)
    assert resp.status_code == 200
    assert resp.headers.get('content-type', '').startswith('image/')
    content = resp.content
    assert len(content) > 100  # some bytes returned

    # 4) verify cached file exists on disk under STORAGE_DIR/images
    storage_dir = os.environ.get('STORAGE_DIR', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'storage')))
    images_dir = os.path.join(storage_dir, 'images')
    assert os.path.isdir(images_dir), f"images dir not found: {images_dir}"

    pattern = os.path.join(images_dir, f"{TMDB_ID}_poster_*")
    matches = glob.glob(pattern)
    assert matches, f"No cached image matching {pattern} found; files: {os.listdir(images_dir) if os.path.isdir(images_dir) else 'N/A'}"

    # 5) subsequent request should hit cached file quickly
    t0 = time.time()
    resp2 = requests.get(img_url, timeout=10)
    dt = time.time() - t0
    assert resp2.status_code == 200
    assert dt < 5, f"Second fetch took too long ({dt}s); expected cached file to be served quickly"
