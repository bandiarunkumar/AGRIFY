"""
AGRIFY Authentication Routes - Cookie + JWT with hardening
"""
import os
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Blueprint, request, jsonify, make_response

from models.database import db, User, TokenBlacklist

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

JWT_SECRET = os.getenv('JWT_SECRET_KEY') or os.getenv('JWT_SECRET') or 'agrify-dev-secret-change-in-production'
JWT_EXPIRY_HOURS = 24
JWT_ISSUER = os.getenv('JWT_ISSUER', 'agrify')
JWT_AUDIENCE = os.getenv('JWT_AUDIENCE', 'agrify-users')
COOKIE_NAME = 'agrify_token'

# Production check
if os.getenv('FLASK_ENV') == 'production' or os.getenv('ENV') == 'production':
    if not os.getenv('JWT_SECRET_KEY') or JWT_SECRET == 'agrify-dev-secret-change-in-production':
        raise RuntimeError('JWT_SECRET_KEY must be set securely in production')


def get_token_from_request():
    # Prefer cookie, fallback to Authorization header for compatibility
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.replace('Bearer ', '')
    return ''


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        if not token:
            return jsonify({'error': 'Token required'}), 401
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'], issuer=JWT_ISSUER, audience=JWT_AUDIENCE)
            jti = data.get('jti')
            if jti and TokenBlacklist.query.filter_by(jti=jti).first():
                return jsonify({'error': 'Token revoked'}), 401
            user_id = data.get('user_id')
            if not user_id:
                return jsonify({'error': 'Invalid token'}), 401
            current_user = User.query.get(user_id)
            if not current_user or not current_user.is_active:
                return jsonify({'error': 'Invalid token'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except Exception:
            return jsonify({'error': 'Invalid token'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


def _set_auth_cookie(response, token):
    secure = request.is_secure or os.getenv('COOKIE_SECURE', 'false').lower() == 'true'
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=secure,
        samesite='Lax',
        max_age=JWT_EXPIRY_HOURS * 3600,
        path='/'
    )
    return response


def _clear_auth_cookie(response):
    secure = request.is_secure or os.getenv('COOKIE_SECURE', 'false').lower() == 'true'
    response.set_cookie(COOKIE_NAME, '', httponly=True, secure=secure, samesite='Lax', max_age=0, path='/')
    return response


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    full_name = str(data.get('full_name', '')).strip()
    email = str(data.get('email', '')).strip().lower() or None
    phone = str(data.get('phone', '')).strip() or None
    password = str(data.get('password', ''))
    
    if not full_name:
        return jsonify({'error': 'Full name required'}), 400
    if not email and not phone:
        return jsonify({'error': 'Email or phone required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if email and '@' not in email:
        return jsonify({'error': 'Invalid email'}), 400
    
    if email and User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409
    if phone and User.query.filter_by(phone=phone).first():
        return jsonify({'error': 'Phone already registered'}), 409
    
    user = User(full_name=full_name, email=email, phone=phone)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    jti = str(uuid.uuid4())
    token = jwt.encode({
        'user_id': user.id,
        'jti': jti,
        'iss': JWT_ISSUER,
        'aud': JWT_AUDIENCE,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    }, JWT_SECRET, algorithm='HS256')
    
    resp = make_response(jsonify({'message': 'Registration successful', 'user': user.to_dict()}))
    _set_auth_cookie(resp, token)
    return resp, 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get('email', '')).strip().lower() or None
    phone = str(data.get('phone', '')).strip() or None
    password = str(data.get('password', ''))
    
    if not password:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    user = None
    if email:
        user = User.query.filter_by(email=email).first()
    elif phone:
        user = User.query.filter_by(phone=phone).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    if not user.is_active:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    jti = str(uuid.uuid4())
    token = jwt.encode({
        'user_id': user.id,
        'jti': jti,
        'iss': JWT_ISSUER,
        'aud': JWT_AUDIENCE,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    }, JWT_SECRET, algorithm='HS256')
    
    resp = make_response(jsonify({'message': 'Login successful', 'user': user.to_dict()}))
    _set_auth_cookie(resp, token)
    return resp, 200


@auth_bp.route('/me', methods=['GET'])
@token_required
def me(current_user):
    return jsonify({'user': current_user.to_dict()}), 200


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    token = get_token_from_request()
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'], options={'verify_exp': False})
        jti = data.get('jti')
        exp = datetime.fromtimestamp(data.get('exp'), tz=timezone.utc) if data.get('exp') else datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
        if jti and not TokenBlacklist.query.filter_by(jti=jti).first():
            db.session.add(TokenBlacklist(jti=jti, exp=exp))
            db.session.commit()
    except Exception:
        pass
    resp = make_response(jsonify({'message': 'Logged out successfully'}))
    _clear_auth_cookie(resp)
    return resp, 200
