import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';

// Mock fetch
global.fetch = jest.fn();

describe('App Component', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('renders search input and button', () => {
    render(<App />);
    
    expect(screen.getByPlaceholderText(/enter your skincare query/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
  });

  it('handles successful search', async () => {
    const mockResponse = {
      query: 'test query',
      products: [
        {
          name: 'Test Product',
          confidence_score: 0.95,
          review_count: 3,
          url: 'http://example.com',
          sample_reviews: [
            { text: 'Great product', similarity_score: 0.9 }
          ]
        }
      ],
      metadata: {
        total_matches: 1,
        filtered_products: 1
      }
    };

    fetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })
    );

    render(<App />);
    
    const input = screen.getByPlaceholderText(/enter your skincare query/i);
    const button = screen.getByRole('button', { name: /search/i });

    fireEvent.change(input, { target: { value: 'test query' } });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
      expect(screen.getByText('Great product')).toBeInTheDocument();
    });
  });

  it('handles error response', async () => {
    fetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: false,
        status: 500
      })
    );

    render(<App />);
    
    const input = screen.getByPlaceholderText(/enter your skincare query/i);
    const button = screen.getByRole('button', { name: /search/i });

    fireEvent.change(input, { target: { value: 'test query' } });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/failed to fetch recommendations/i)).toBeInTheDocument();
    });
  });
});
