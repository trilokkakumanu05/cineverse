import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API = "https://cineverse-1x7t.onrender.com";





function App() {
  const [movies, setMovies] = useState([]);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [trailer, setTrailer] = useState(null);
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [didYouMean, setDidYouMean] = useState(null);
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ================= LOAD TRENDING =================
  useEffect(() => {
    fetchTrending();
  }, [language]);

  const fetchTrending = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API}/trending?language=${language}`);
      setMovies(res?.data?.results || []);
      setError("");
    } catch {
      setError("Failed to load movies.");
    } finally {
      setLoading(false);
    }
  };

  // ================= LIVE SEARCH =================
  useEffect(() => {
    if (query.trim() === "") {
      setSuggestions([]);
      setDidYouMean(null);
      return;
    }

    const controller = new AbortController();

    const fetchSearch = async () => {
      try {
        const res = await axios.get(
          `${API}/search?query=${query}`,
          { signal: controller.signal }
        );

        setSuggestions(res?.data?.results?.slice(0, 8) || []);
        setDidYouMean(res?.data?.did_you_mean || null);
      } catch (err) {
        if (err.name !== "CanceledError") {
          console.error(err);
        }
      }
    };

    const debounce = setTimeout(fetchSearch, 300);

    return () => {
      clearTimeout(debounce);
      controller.abort();
    };
  }, [query]);

  // ================= OPEN MOVIE =================
  const openMovie = async (id) => {
    try {
      setLoading(true);

      const res = await axios.get(`${API}/movie/${id}`);
      if (!res?.data || res.data.status_code) return;

      setSelectedMovie(res.data);
      setQuery("");
      setSuggestions([]);
      setDidYouMean(null);

      const rec = await axios.get(`${API}/recommend/${id}`);
      setRecommendations(rec?.data?.results || []);
    } catch {
      setError("Failed to load movie details.");
    } finally {
      setLoading(false);
    }
  };

  const fetchTrailer = async (id) => {
    const res = await axios.get(`${API}/trailer/${id}`);
    setTrailer(res?.data?.trailer_url || null);
  };

  const goHome = () => {
    setSelectedMovie(null);
    setTrailer(null);
    fetchTrending();
  };

  const heroMovie = movies[0];

  return (
    <div className="app">
      {/* ================= HEADER ================= */}
      <header className="header">
        <h2 className="logo" onClick={goHome}>
          🎬 CineVerse
        </h2>

        <div className="header-right">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            <option value="en">English</option>
            <option value="te">Telugu</option>
            <option value="hi">Hindi</option>
            <option value="ta">Tamil</option>
            <option value="ml">Malayalam</option>
            <option value="kn">Kannada</option>
          </select>

          <div className="search-container">
            <input
              type="text"
              placeholder="Search movies..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />

            {/* DID YOU MEAN */}
            {didYouMean && (
              <div className="did-you-mean">
                Did you mean:{" "}
                <span onClick={() => setQuery(didYouMean)}>
                  {didYouMean}
                </span>
              </div>
            )}

            {/* SEARCH DROPDOWN */}
            {suggestions.length > 0 && (
              <div className="suggestions">
                {suggestions.map((movie) => (
                  <div
                    key={movie.id}
                    className="suggestion-item"
                    onClick={() => openMovie(movie.id)}
                  >
                    {movie.poster_path && (
                      <img
                        src={`https://image.tmdb.org/t/p/w200${movie.poster_path}`}
                        alt={movie.title}
                      />
                    )}
                    <div className="suggestion-text">
                      {movie.title}
                      <div className="suggestion-year">
                        {movie.release_date?.slice(0, 4)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* ================= LOADING ================= */}
      {loading && <div className="spinner"></div>}

      {/* ================= ERROR ================= */}
      {error && <div className="error">{error}</div>}

      {/* ================= HOME PAGE ================= */}
      {!selectedMovie && heroMovie && (
        <>
          <div
            className="hero"
            style={{
              backgroundImage: `url(https://image.tmdb.org/t/p/original${heroMovie.backdrop_path})`,
            }}
          >
            <div className="hero-overlay">
              <h1>{heroMovie.title}</h1>
              <p>{heroMovie.overview?.slice(0, 180)}...</p>
              <button onClick={() => openMovie(heroMovie.id)}>
                ▶ View
              </button>
            </div>
          </div>

          <div className="movie-grid">
            {movies.map(
              (movie) =>
                movie.poster_path && (
                  <div
                    key={movie.id}
                    className="movie-card"
                    onClick={() => openMovie(movie.id)}
                  >
                    <img
                      src={`https://image.tmdb.org/t/p/w500${movie.poster_path}`}
                      alt={movie.title}
                    />
                  </div>
                )
            )}
          </div>
        </>
      )}

      {/* ================= DETAIL PAGE ================= */}
      {selectedMovie && (
        <div className="detail">
          <button className="back-btn" onClick={goHome}>
            ⬅ Back Home
          </button>

          <div className="detail-container">
            <img
              src={`https://image.tmdb.org/t/p/w500${selectedMovie.poster_path}`}
              alt={selectedMovie.title}
            />

            <div>
              <h2>{selectedMovie.title}</h2>
              <p>⭐ {selectedMovie.vote_average}</p>
              <p>{selectedMovie.overview}</p>

              <button onClick={() => fetchTrailer(selectedMovie.id)}>
                ▶ Watch Trailer
              </button>
            </div>
          </div>

          {trailer && (
            <div className="modal">
              <div className="modal-content">
                <button onClick={() => setTrailer(null)}>✖</button>
                <iframe
                  width="100%"
                  height="400"
                  src={trailer}
                  allowFullScreen
                  title="Trailer"
                ></iframe>
              </div>
            </div>
          )}

          <h3>Recommended</h3>
          <div className="movie-grid">
            {recommendations.map(
              (movie) =>
                movie.poster_path && (
                  <div
                    key={movie.id}
                    className="movie-card"
                    onClick={() => openMovie(movie.id)}
                  >
                    <img
                      src={`https://image.tmdb.org/t/p/w500${movie.poster_path}`}
                      alt={movie.title}
                    />
                  </div>
                )
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
