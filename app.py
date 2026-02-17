import streamlit as st
import requests

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Global Movie AI", layout="wide")

TMDB_API_KEY = "da98e8856e0fbfd301778ba6b5026589"

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "selected_movie_id" not in st.session_state:
    st.session_state.selected_movie_id = None

if "page" not in st.session_state:
    st.session_state.page = 1

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

if "show_trailer" not in st.session_state:
    st.session_state.show_trailer = False

# --------------------------------------------------
# STYLING (HOVER ANIMATION)
# --------------------------------------------------
st.markdown("""
<style>
.poster-container {
    position: relative;
    overflow: hidden;
    border-radius: 12px;
}
.poster-container img {
    width: 100%;
    transition: transform 0.4s ease;
    border-radius: 12px;
}
.poster-container:hover img {
    transform: scale(1.08);
}
.overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.4);
    opacity: 0;
    display:flex;
    justify-content:center;
    align-items:center;
    font-size:40px;
    color:white;
    transition: opacity 0.3s ease;
}
.poster-container:hover .overlay {
    opacity: 1;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# TMDB FUNCTIONS
# --------------------------------------------------
def get_trending(page=1):
    url = "https://api.themoviedb.org/3/trending/movie/week"
    params = {"api_key": TMDB_API_KEY, "page": page}
    return requests.get(url, params=params).json()

def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {"api_key": TMDB_API_KEY}
    return requests.get(url, params=params).json()

def get_similar_movies(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/similar"
    params = {"api_key": TMDB_API_KEY}
    return requests.get(url, params=params).json()

def get_trailer(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos"
    params = {"api_key": TMDB_API_KEY}
    data = requests.get(url, params=params).json()

    for video in data.get("results", []):
        if video["type"] == "Trailer" and video["site"] == "YouTube":
            return f"https://www.youtube.com/embed/{video['key']}"
    return None

# --------------------------------------------------
# CLICKABLE POSTER CARD
# --------------------------------------------------
def display_clickable_poster(movie, key_prefix):
    poster = movie.get("poster_path")
    if not poster:
        return False

    poster_url = f"https://image.tmdb.org/t/p/w500{poster}"

    st.markdown(f"""
        <div class="poster-container">
            <img src="{poster_url}">
            <div class="overlay">▶</div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("", key=f"{key_prefix}_{movie['id']}"):
        st.session_state.selected_movie_id = movie["id"]
        st.rerun()

    return True

# --------------------------------------------------
# HEADER
# --------------------------------------------------
col1, col2 = st.columns([4,1])

with col1:
    st.title("🎬 Global Movie AI Recommender")

with col2:
    if st.button("🏠 Home"):
        st.session_state.selected_movie_id = None
        st.session_state.show_trailer = False
        st.rerun()

# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------
if not st.session_state.selected_movie_id:

    st.subheader("🔥 Trending Movies")

    with st.spinner("Loading movies..."):
        results = get_trending(st.session_state.page)
        movies = results.get("results", [])

    cols = st.columns(3)
    displayed = 0

    for movie in movies:
        if displayed >= 9:
            break
        with cols[displayed % 3]:
            if display_clickable_poster(movie, "home"):
                displayed += 1

    if st.button("Load More"):
        st.session_state.page += 1
        st.rerun()

# --------------------------------------------------
# MOVIE DETAIL PAGE
# --------------------------------------------------
if st.session_state.selected_movie_id:

    with st.spinner("Loading movie details..."):
        movie = get_movie_details(st.session_state.selected_movie_id)

    st.markdown("---")

    col1, col2 = st.columns([1,2])

    with col1:
        if movie.get("poster_path"):
            poster_url = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
            st.image(poster_url, use_container_width=True)

    with col2:
        st.header(movie.get("title"))
        st.write(f"⭐ Rating: {movie.get('vote_average')}")
        st.write(movie.get("overview"))

        if st.button("▶ Watch Trailer"):
            st.session_state.show_trailer = True

    # --------------------------------------------------
    # TRAILER MODAL
    # --------------------------------------------------
    if st.session_state.show_trailer:
        trailer_url = get_trailer(st.session_state.selected_movie_id)

        if trailer_url:
            st.markdown("### 🎬 Trailer")
            st.components.v1.iframe(trailer_url, height=450)
        else:
            st.warning("Trailer not available.")

        if st.button("Close Trailer"):
            st.session_state.show_trailer = False
            st.rerun()

    # --------------------------------------------------
    # SIMILAR MOVIES
    # --------------------------------------------------
    st.markdown("### 🎯 Similar Movies")

    similar = get_similar_movies(st.session_state.selected_movie_id)
    similar_movies = similar.get("results", [])

    cols = st.columns(3)
    displayed = 0

    for movie in similar_movies:
        if displayed >= 6:
            break
        with cols[displayed % 3]:
            if display_clickable_poster(movie, "rec"):
                displayed += 1
