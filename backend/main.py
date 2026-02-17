from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import os
from rapidfuzz import fuzz
import requests
import jellyfish


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TMDB_API_KEY = "da98e8856e0fbfd301778ba6b5026589"
BASE_URL = "https://api.themoviedb.org/3"

WATCHLIST_FILE = "watchlist.json"

# ---------- WATCHLIST STORAGE ----------
def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "w") as f:
            json.dump({"watchlist": []}, f)

    with open(WATCHLIST_FILE, "r") as f:
        return json.load(f)

def save_watchlist(data):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f)

# ---------- DISCOVER ----------
@app.get("/trending")
def trending(language: str = "en"):
    url = f"{BASE_URL}/discover/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "with_original_language": language,
        "sort_by": "popularity.desc"
    }
    return requests.get(url, params=params).json()

# ---------- SEARCH ----------
POPULAR_CACHE = []

def load_popular():
    global POPULAR_CACHE
    if not POPULAR_CACHE:
        url = f"{BASE_URL}/discover/movie"
        for page in range(1, 4):  # Fetch 3 pages
            params = {
                "api_key": TMDB_API_KEY,
                "sort_by": "popularity.desc",
                "page": page
            }
            res = requests.get(url, params=params).json()
            POPULAR_CACHE.extend(res.get("results", []))
    return POPULAR_CACHE

@app.get("/search")
def search(query: str):

    def tmdb_search(q):
        url = f"{BASE_URL}/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": q
        }
        return requests.get(url, params=params).json().get("results", [])

    query_lower = query.lower().strip()

    # Step 1: TMDB search
    results = tmdb_search(query)

    # Step 2: Load popular cache
    popular_movies = load_popular()

    # Combine unique movies
    combined = {m["id"]: m for m in (results + popular_movies)}
    movies = list(combined.values())

    scored = []
    best_match_title = None
    best_score = 0

    query_phonetic = jellyfish.soundex(query_lower)

    for movie in movies:
        title = movie.get("title", "")
        title_lower = title.lower()

        # Fuzzy score
        fuzzy_score = fuzz.ratio(query_lower, title_lower)

        # Partial score
        partial_score = fuzz.partial_ratio(query_lower, title_lower)

        # Phonetic score
        title_phonetic = jellyfish.soundex(title_lower)
        phonetic_score = 100 if query_phonetic == title_phonetic else 0

        total_score = max(fuzzy_score, partial_score, phonetic_score)

        if total_score > 45:
            scored.append((total_score, movie))

        # Track best suggestion
        if total_score > best_score:
            best_score = total_score
            best_match_title = title

    scored.sort(reverse=True, key=lambda x: x[0])

    final_results = [movie for score, movie in scored[:15]]

    suggestion = None

    # If strong correction exists but original query differs
    if best_score > 70 and best_match_title.lower() != query_lower:
        suggestion = best_match_title

    return {
        "results": final_results,
        "did_you_mean": suggestion
    }

# ---------- MOVIE DETAILS ----------
@app.get("/movie/{movie_id}")
def movie(movie_id: int):
    url = f"{BASE_URL}/movie/{movie_id}"
    return requests.get(url, params={"api_key": TMDB_API_KEY}).json()

# ---------- RECOMMEND ----------
@app.get("/recommend/{movie_id}")
def recommend(movie_id: int):
    # Step 1: Get movie details
    movie_url = f"{BASE_URL}/movie/{movie_id}"
    movie_data = requests.get(
        movie_url,
        params={"api_key": TMDB_API_KEY}
    ).json()

    if not movie_data or "status_code" in movie_data:
        return {"results": []}

    language = movie_data.get("original_language")
    genres = movie_data.get("genres", [])

    genre_ids = ",".join(str(g["id"]) for g in genres)

    # Step 2: Discover similar movies by language + genre
    discover_url = f"{BASE_URL}/discover/movie"

    params = {
        "api_key": TMDB_API_KEY,
        "with_original_language": language,
        "with_genres": genre_ids,
        "sort_by": "popularity.desc"
    }

    res = requests.get(discover_url, params=params).json()

    return res


# ---------- TRAILER ----------
@app.get("/trailer/{movie_id}")
def trailer(movie_id: int):
    url = f"{BASE_URL}/movie/{movie_id}/videos"
    res = requests.get(url, params={"api_key": TMDB_API_KEY}).json()

    for video in res.get("results", []):
        if video["type"] == "Trailer" and video["site"] == "YouTube":
            return {
                "trailer_url": f"https://www.youtube.com/embed/{video['key']}"
            }

    return {"trailer_url": None}

# ---------- WATCHLIST ----------
@app.get("/watchlist")
def get_watchlist():
    return load_watchlist()

@app.post("/watchlist/add")
def add_watchlist(movie: dict):
    data = load_watchlist()
    if movie["movie_id"] not in data["watchlist"]:
        data["watchlist"].append(movie["movie_id"])
    save_watchlist(data)
    return {"message": "Added"}

@app.delete("/watchlist/remove/{movie_id}")
def remove_watchlist(movie_id: int):
    data = load_watchlist()
    if movie_id in data["watchlist"]:
        data["watchlist"].remove(movie_id)
    save_watchlist(data)
    return {"message": "Removed"}
