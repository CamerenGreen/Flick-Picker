"""Optional TMDB search and import. The API key stays on the server."""
import os
import urllib.parse
import urllib.request
import json

BASE = "https://api.themoviedb.org/3"


def enabled():
    return bool(os.environ.get("TMDB_API_KEY"))


def _get(path, params=None):
    key = os.environ.get("TMDB_API_KEY")
    if not key:
        raise RuntimeError("TMDB_API_KEY is not configured")
    query = urllib.parse.urlencode({**(params or {}), "api_key": key})
    request = urllib.request.Request(BASE + path + "?" + query,
                                     headers={"User-Agent": "FlickPicker/1.0"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def search(query, media_type="all"):
    types = ["movie", "tv"] if media_type == "all" else [media_type]
    output = []
    for kind in types:
        for item in _get(f"/search/{kind}", {"query": query}).get("results", [])[:8]:
            output.append({"source": "tmdb", "source_id": str(item["id"]),
                           "media_type": kind, "title": item.get("title") or item.get("name"),
                           "year": (item.get("release_date") or item.get("first_air_date") or "")[:4],
                           "overview": item.get("overview") or "",
                           "poster_path": item.get("poster_path")})
    return output


def popular(media_type, page=1):
    return [str(item["id"]) for item in _get(f"/{media_type}/popular", {"page": page}).get("results", [])]


def details(source_id, media_type):
    item = _get(f"/{media_type}/{source_id}", {"append_to_response": "keywords"})
    keyword_data = item.get("keywords", {})
    tags = keyword_data.get("keywords", keyword_data.get("results", []))
    return {"source": "tmdb", "source_id": str(item["id"]), "media_type": media_type,
            "title": item.get("title") or item.get("name"), "overview": item.get("overview") or "",
            "genres": [g["name"] for g in item.get("genres", [])],
            "tags": [tag["name"] for tag in tags[:12]],
            "year": int((item.get("release_date") or item.get("first_air_date") or "0")[:4]),
            "poster_path": item.get("poster_path")}
