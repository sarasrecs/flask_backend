import React, { useState } from 'react';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:5000/api/products/recommendations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      console.log(query)

      if (!response.ok) {
        throw new Error('Failed to fetch recommendations');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Skincare Product Recommendations</h1>
      </header>

      <main className="App-main">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your skincare query (e.g., moisturizer for dry skin)"
            className="search-input"
          />
          <button type="submit" className="search-button" disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>

        {error && (
          <div className="error-message">
            Error: {error}
          </div>
        )}

        {results && (
          <div className="results-container">
            <h2>Results for: {results.query}</h2>
            <p className="results-meta">
              Found {results.metadata.total_matches} matches across {results.metadata.filtered_products} products
            </p>
            
            <div className="products-grid">
              {results.products.map((product, index) => (
                <div key={index} className="product-card">
                  <h3>{product.name}</h3>
                  <img 
                    src={(() => {
                      const urlObj = new URL(product.url);
                      const skuId = urlObj.searchParams.get("skuId");
                      return skuId ? `https://sephora.com/productimages/sku/s${skuId}-main-zoom.jpg?imwidth=315` : product.url; 
                    })()}
                    alt={product.name} 
                    className="product-image" 
                  />
                  <div className="product-stats">
                    <span>Confidence: {product.confidence_score}</span>
                    <span>Reviews: {product.review_count}</span>
                  </div>
                  <a href={product.url} target="_blank" rel="noopener noreferrer" className="product-link">
                    View Product
                  </a>
                  <div className="reviews-section">
                    <h4>Sample Reviews:</h4>
                    {product.sample_reviews.map((review, reviewIndex) => (
                      <div key={reviewIndex} className="review-card">
                        <p>{review.text}</p>
                        <span className="review-score">
                          Match Score: {review.similarity_score}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
