from flask import Blueprint, request, jsonify
from services.product_service import ProductService
from http import HTTPStatus

product_bp = Blueprint('products', __name__)
product_service = ProductService()

@product_bp.route('/recommendations', methods=['POST'])
def get_recommendations():
    try:
        data = request.get_json()
        print('data', data)
        if not data or 'query' not in data:
            return jsonify({
                'error': 'Query is required'
            }), HTTPStatus.BAD_REQUEST
            
        query = data['query']
        top_k = data.get('top_k', 20)
        min_reviews = data.get('min_reviews', 1)
        score_threshold = data.get('score_threshold', 0.5)
        
        results = product_service.get_recommendations(
            query=query,
            top_k=top_k,
            min_reviews=min_reviews,
            score_threshold=score_threshold
        )
        
        return jsonify(results), HTTPStatus.OK
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@product_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'product-recommendations'
    }), HTTPStatus.OK 