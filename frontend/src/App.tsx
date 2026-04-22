import { useState } from 'react';
import { SearchForm } from './components/SearchForm';
import { RestaurantCard } from './components/RestaurantCard';
import { fetchRecommendations, fetchExplore } from './services/api';
import type { RecommendationRequest, RestaurantResult } from './services/api';

const EXPLORE_CUISINES = [
  { name: 'Indian',        image: '/images/cuisines/indian.png',        emoji: '🍛', color: '#FFF7ED', border: '#FED7AA' },
  { name: 'Italian',       image: '/images/cuisines/italian.png',       emoji: '🍕', color: '#FFF1F2', border: '#FECDD3' },
  { name: 'Chinese',       image: '/images/cuisines/chinese.png',       emoji: '🥢', color: '#FEF9C3', border: '#FDE047' },
  { name: 'Japanese',      image: '/images/cuisines/japanese.png',      emoji: '🍣', color: '#F0FDF4', border: '#BBF7D0' },
  { name: 'Mexican',       image: '/images/cuisines/mexican.png',       emoji: '🌮', color: '#FFF7ED', border: '#FDBA74' },
  { name: 'Mediterranean', image: '/images/cuisines/mediterranean.png', emoji: '🥗', color: '#EFF6FF', border: '#BFDBFE' },
  { name: 'Cafe',          image: '/images/cuisines/cafe.png',          emoji: '☕', color: '#FDF4FF', border: '#E9D5FF' },
  { name: 'Fast Food',     image: '/images/cuisines/fast_food.png',     emoji: '🍔', color: '#F0FDF4', border: '#86EFAC' },
];

function App() {
  const [results, setResults] = useState<RestaurantResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  // Explore section state
  const [activeCuisine, setActiveCuisine] = useState<string | null>(null);
  const [exploreResults, setExploreResults] = useState<RestaurantResult[]>([]);
  const [exploreLoading, setExploreLoading] = useState(false);

  const handleSearch = async (request: RecommendationRequest) => {
    setIsLoading(true);
    setError(null);
    setHasSearched(true);
    setResults([]);

    try {
      const response = await fetchRecommendations(request);
      setResults(response.results);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred while fetching recommendations.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExploreCuisine = async (cuisine: string) => {
    setActiveCuisine(cuisine);
    setExploreLoading(true);
    setExploreResults([]);
    try {
      const res = await fetchExplore(cuisine);
      setExploreResults(res.results);
    } catch (e) {
      console.error(e);
    } finally {
      setExploreLoading(false);
    }
  };

  return (
    <div>
      <nav className="navbar" style={{ padding: '1rem 3rem', justifyContent: 'center' }}>
        <div style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.05em', textAlign: 'center' }}>
          Culinary <span style={{ fontWeight: 300 }}>AI</span>
        </div>
      </nav>

      <div className="app-vertical-layout" style={{ paddingTop: '1rem' }}>
        {/* Hero */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 className="hero-title" style={{ fontSize: '3rem' }}>
            The <span className="epic-font">Epicurean</span> Canvas
          </h1>
          <p style={{ fontSize: '1rem', maxWidth: '600px', margin: '0 auto', opacity: 0.8 }}>
            Refine your gastronomic journey. Our AI curates an editorial-grade dining experience tailored to your palate.
          </p>
        </div>

        {/* Search Bar */}
        <SearchForm onSearch={handleSearch} isLoading={isLoading} />

        {/* Error */}
        {error && (
          <div className="editorial-card" style={{ marginTop: '2rem', borderColor: 'var(--primary-color)' }}>
            <p style={{ color: 'var(--primary-color)' }}>{error}</p>
          </div>
        )}

        {/* Search Results */}
        <div style={{ marginTop: '2.5rem' }}>
          {isLoading && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', padding: '4rem 0' }}>
              <div className="spinner"></div>
              <p>Curating your personalized recommendations...</p>
            </div>
          )}

          {!isLoading && hasSearched && results.length === 0 && !error && (
            <div className="editorial-card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
              <h2>No perfect match found</h2>
              <p>We couldn't find any restaurants matching those exact criteria. Try broadening your budget or area.</p>
            </div>
          )}

          {!isLoading && results.length > 0 && (
            <div className="animate-slide-up">
              <h2 style={{ fontSize: '1.75rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                Your Curated Matches
              </h2>
              <div className="results-grid">
                {results.map((r) => (
                  <RestaurantCard key={r.restaurant_id} restaurant={r} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ── Explore by Cuisine ── */}
        <div style={{ marginTop: '5rem' }}>
          <div style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
            <h2 style={{ fontSize: '1.75rem', marginBottom: '0.4rem' }}>
              Explore by <span className="epic-font">Cuisine</span>
            </h2>
            <p style={{ fontSize: '0.95rem', opacity: 0.7, maxWidth: '520px', margin: '0 auto' }}>
              Discover top-rated restaurants across the city by cuisine style — no location filter needed.
            </p>
          </div>

          {/* Cuisine Category Cards */}
          <div className="cuisine-category-grid">
            {EXPLORE_CUISINES.map(c => (
              <button
                key={c.name}
                id={`explore-${c.name.toLowerCase().replace(' ', '-')}`}
                onClick={() => handleExploreCuisine(c.name)}
                className="cuisine-category-btn"
                style={{
                  background: c.image ? 'transparent' : c.color,
                  border: c.image ? 'none' : `2px solid ${c.border}`
                }}
              >
                {c.image ? (
                  <>
                    <img
                      src={c.image}
                      alt={c.name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block', transition: 'transform 0.3s ease' }}
                    />
                    {/* Dark overlay */}
                    <div style={{
                      position: 'absolute', inset: 0,
                      background: activeCuisine === c.name
                        ? 'rgba(220,38,38,0.45)'
                        : 'linear-gradient(to top, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.1) 100%)',
                      transition: 'background 0.25s ease'
                    }} />
                    <span style={{
                      position: 'absolute', bottom: '1rem', left: 0, right: 0,
                      textAlign: 'center', color: 'white', fontWeight: 700,
                      fontSize: '1.1rem', textShadow: '0 1px 4px rgba(0,0,0,0.8)'
                    }}>{c.name}</span>
                  </>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '0.6rem' }}>
                    <span style={{ fontSize: '2.5rem' }}>{c.emoji}</span>
                    <span style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>{c.name}</span>
                  </div>
                )}
              </button>
            ))}
          </div>

          {/* Explore Results */}
          {exploreLoading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '2rem 0' }}>
              <div className="spinner" style={{ width: '22px', height: '22px' }}></div>
              <p>Finding the best {activeCuisine} spots...</p>
            </div>
          )}

          {!exploreLoading && exploreResults.length > 0 && (
            <div className="animate-slide-up">
              <h3 style={{ fontSize: '1.2rem', marginBottom: '1.25rem', color: 'var(--text-secondary)' }}>
                Top <strong style={{ color: 'var(--text-primary)' }}>{activeCuisine}</strong> restaurants in the city
              </h3>
              <div className="results-grid">
                {exploreResults.map((r) => (
                  <RestaurantCard key={r.restaurant_id} restaurant={r} />
                ))}
              </div>
            </div>
          )}

          {!exploreLoading && activeCuisine && exploreResults.length === 0 && (
            <div className="editorial-card" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
              <p>No {activeCuisine} restaurants found in the dataset.</p>
            </div>
          )}
        </div>
      </div>

      <footer style={{ background: '#F3F4F6', padding: '3rem 2rem', marginTop: '6rem', textAlign: 'center' }}>
        <p style={{ fontSize: '0.875rem' }}>© 2024 The Culinary Editorial. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;
