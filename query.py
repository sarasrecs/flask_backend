import os
import json
from dotenv import load_dotenv
from pinecone import Pinecone
from google import genai
import time
from typing import List, Dict, Tuple, Any

# Load API keys from environment variables
load_dotenv()
pinecone_key = os.getenv("PINECONE_KEY")
gemini_key = os.getenv("GEMINI_KEY")

# Initialize Gemini and Pinecone clients
client = genai.Client(api_key=gemini_key)
pc = Pinecone(api_key=pinecone_key)

# Connect to the Pinecone index
index_name = "skincare-products"
index = pc.Index(index_name)

def get_embedding(text: str, max_retries: int = 3, initial_delay: float = 1) -> List[float]:
    """
    Get embedding for text with retry logic for rate limits
    """
    delay = initial_delay
    attempt = 0
    
    while attempt < max_retries:
        try:
            response = client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            return response.embeddings[0].values
            
        except Exception as e:
            attempt += 1
            error_msg = str(e).lower()
            
            if "rate limit" in error_msg or "quota" in error_msg or "429" in error_msg:
                wait_time = delay * (2 ** attempt)
                print(f"Rate limit hit. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Error: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
                
            if attempt == max_retries:
                raise Exception(f"Failed to get embedding after {max_retries} attempts")
    
    return None

class ProductRecommender:
    def __init__(self, index):
        self.index = index
    
    def search_reviews(self, query: str, top_k: int = 10, score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Search for relevant reviews and return detailed results
        """
        try:
            query_embedding = get_embedding(query)
            if not query_embedding:
                raise Exception("Failed to generate query embedding")

            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )

            # Filter results by similarity score threshold
            filtered_matches = [
                match for match in results["matches"]
                if match["score"] >= score_threshold
            ]

            return filtered_matches
        except Exception as e:
            print(f"Error during search: {e}")
            return []

    def get_product_recommendations(
        self,
        query: str,
        top_k: int = 20,
        min_reviews: int = 1,
        score_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Get product recommendations with detailed analysis
        """
        matches = self.search_reviews(query, top_k=top_k * 2, score_threshold=score_threshold)
        
        # Aggregate results by product
        product_data: Dict[str, Dict[str, Any]] = {}
        for match in matches:
            product_name = match["metadata"]["product_name"]
            if product_name not in product_data:
                product_data[product_name] = {
                    "url": match["metadata"]["url"],
                    "review_count": 0,
                    "avg_score": 0.0,
                    "relevant_reviews": [],
                    "total_score": 0.0
                }
            
            data = product_data[product_name]
            data["review_count"] += 1
            data["total_score"] += match["score"]
            data["relevant_reviews"].append({
                "text": match["metadata"]["review"],
                "similarity_score": match["score"]
            })

        # Calculate averages and filter products
        filtered_products = {}
        for product_name, data in product_data.items():
            if data["review_count"] >= min_reviews:
                data["avg_score"] = data["total_score"] / data["review_count"]
                filtered_products[product_name] = data

        # Sort products by average score
        sorted_products = sorted(
            filtered_products.items(),
            key=lambda x: (x[1]["avg_score"], x[1]["review_count"]),
            reverse=True
        )

        return {
            "query": query,
            "products": sorted_products[:top_k],
            "total_matches": len(matches),
            "filtered_products": len(filtered_products)
        }

def format_recommendations(results: Dict[str, Any]) -> str:
    """
    Format recommendations into a readable string
    """
    output = [
        f"Search Query: {results['query']}\n",
        f"Found {results['total_matches']} relevant reviews across {results['filtered_products']} products.\n",
        "\nTop Recommended Products:\n"
    ]

    for i, (product_name, data) in enumerate(results["products"], 1):
        output.extend([
            f"\n{i}. {product_name}",
            f"   Confidence Score: {data['avg_score']:.2f}",
            f"   Based on {data['review_count']} relevant reviews",
            f"   Product URL: {data['url']}",
            "\n   Sample Review:",
            f"   \"{data['relevant_reviews'][0]['text'][:200]}...\"\n"
        ])

    return "\n".join(output)

def main():
    # Initialize recommender
    recommender = ProductRecommender(index)
    
    while True:
        try:
            # Get user query
            print("\nEnter your skincare query (or 'quit' to exit):")
            query = input().strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
                
            if not query:
                print("Please enter a valid query.")
                continue
            
            # Get and format recommendations
            results = recommender.get_product_recommendations(
                query,
                top_k=20,
                min_reviews=2,
                score_threshold=0.5
            )
            
            # Print formatted results
            print("\n" + format_recommendations(results))
            
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please try again with a different query.")

if __name__ == "__main__":
    main()