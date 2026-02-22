from functools import wraps
from flask import request, jsonify
from app.core.config import settings


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        x_api_key = request.headers.get("X-Api-Key")
        if not x_api_key or x_api_key != settings.API_KEY:
            return jsonify({"detail": "Invalid API key"}), 401
        return f(*args, **kwargs)
    return decorated_function
