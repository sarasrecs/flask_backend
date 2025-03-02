import os
from dotenv import load_dotenv
from pinecone import Pinecone
from google import genai
from typing import Dict, Any

class ProductService:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        pinecone_key = os.getenv("PINECONE_KEY")
        gemini_key = os.getenv("GEMINI_KEY")
        
        if not pinecone_key or not gemini_key:
            raise ValueError("Missing required API keys")
            
        # Initialize clients
        self.gemini_client = genai.Client(api_key=gemini_key)
        self.pc = Pinecone(api_key=pinecone_key)
        
        # Initialize Pinecone index
        self.index_name = "skincare-products"
        self.index = self.pc.Index(self.index_name)
        
        # Initialize recommender
        from query import ProductRecommender
        self.recommender = ProductRecommender(self.index)
    
    def get_recommendations(
        self,
        query: str,
        top_k: int = 20,
        min_reviews: int = 1,
        score_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Get product recommendations based on the query
        """
        results = self.recommender.get_product_recommendations(
            query=query,
            top_k=top_k,
            min_reviews=min_reviews,
            score_threshold=score_threshold
        )
        
        # Transform the results to be more API-friendly
        formatted_products = []
        for product_name, data in results['products']:
            formatted_products.append({
                'name': product_name,
                'url': data['url'],
                'confidence_score': round(data['avg_score'], 2),
                'review_count': data['review_count'],
                'sample_reviews': [
                    {
                        'text': review['text'],
                        'similarity_score': round(review['similarity_score'], 2)
                    }
                    for review in data['relevant_reviews'][:3]  # Limit to top 3 reviews
                ]
            })
            
        return {
            'query': query,
            'products': formatted_products,
            'metadata': {
                'total_matches': results['total_matches'],
                'filtered_products': results['filtered_products']
            }
        } 