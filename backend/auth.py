"""
backend/auth.py
Authentication & Role-Based Access Control using JWT and Werkzeug security.
Provides token generation, verification, and role protection decorators.
"""
import os
from functools import wraps
from datetime import datetime, timedelta
from jose import jwt, JWTError
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, jsonify
from backend.models_db import User

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'roomee-jwt-secret-key-prod-2026')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 7


def hash_password(password: str) -> str:
    """Hashes a plaintext password."""
    return generate_password_hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verifies a plaintext password against the stored hash."""
    return check_password_hash(hashed, password)


def generate_jwt_token(user: User) -> str:
    """Generates a signed JWT token containing user identity and role."""
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    payload = {
        'user_id': user.id,
        'email': user.email,
        'name': user.name,
        'role': user.role,
        'exp': expire
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str):
    """Decodes and validates a JWT token."""
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        return None


def token_required(f):
    """
    Decorator requiring a valid Bearer JWT token in Authorization header or cookie.
    Passes current_user as first argument to the endpoint.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1].strip()
        elif request.cookies.get('roomee_token'):
            token = request.cookies.get('roomee_token')

        if not token:
            return jsonify({
                "success": False,
                "error": "Authentication required. Please log in to proceed."
            }), 401

        payload = decode_jwt_token(token)
        if not payload:
            return jsonify({
                "success": False,
                "error": "Session expired or invalid token. Please log in again."
            }), 401

        user = User.query.get(payload.get('user_id'))
        if not user:
            return jsonify({
                "success": False,
                "error": "User account not found."
            }), 401

        return f(user, *args, **kwargs)
    return decorated


def roles_accepted(*allowed_roles):
    """
    Role-based access control decorator.
    Must be used along with or after token_required.
    """
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            if current_user.role not in allowed_roles:
                return jsonify({
                    "success": False,
                    "error": f"Access denied. Requires one of roles: {', '.join(allowed_roles)}"
                }), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator
