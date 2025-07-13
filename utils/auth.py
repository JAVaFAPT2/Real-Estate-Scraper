"""
Authentication Module

This module provides JWT-based authentication for the real estate scraper.
"""

import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, 
    get_jwt_identity, verify_jwt_in_request
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session
from database.models import User, PropertyListing, Base
from database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

# Initialize JWT manager
jwt = JWTManager()

# Tier limits
TIER_LIMITS = {
    'free': {
        'listings_per_request': 10,
        'alerts_limit': 3,
        'export_limit': 100,
        'api_calls_per_day': 100
    },
    'pro': {
        'listings_per_request': 100,
        'alerts_limit': 10,
        'export_limit': 1000,
        'api_calls_per_day': 1000
    },
    'enterprise': {
        'listings_per_request': 10000,
        'alerts_limit': 50,
        'export_limit': 10000,
        'api_calls_per_day': 10000
    }
}


class AuthManager:
    """Manages user authentication and authorization"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def register_user(self, username: str, email: str, password: str, tier: str = 'free'):
        """
        Register a new user
        
        Args:
            username: Username
            email: Email address
            password: Plain text password
            tier: Subscription tier (free, pro, enterprise)
            
        Returns:
            User object or None if failed
        """
        try:
            # Check if user already exists
            existing_user = self.db_manager.get_user_by_email(email)
            if existing_user:
                logger.warning(f"User registration failed: email {email} already exists")
                return None
            
            # Hash password
            hashed_password = generate_password_hash(password)
            
            # Create user
            user_data = {
                'username': username,
                'email': email,
                'password': hashed_password,
                'subscription_tier': tier,
                'is_active': True
            }
            
            user = self.db_manager.create_user(user_data)
            
            if user:
                logger.info(f"User registered successfully: {email}")
                return user
            else:
                logger.error(f"Failed to create user: {email}")
                return None
                
        except Exception as e:
            logger.error(f"Error in register_user: {e}")
            return None
    
    def login_user(self, email: str, password: str):
        """
        Authenticate user and return JWT token
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            dict with token and user info, or None if failed
        """
        try:
            # Get user by email
            user = self.db_manager.get_user_by_email(email)
            
            if not user:
                logger.warning(f"Login failed: user not found: {email}")
                return None
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Login failed: user inactive: {email}")
                return None
            
            # Verify password
            if not check_password_hash(user.password, password):
                logger.warning(f"Login failed: invalid password for: {email}")
                return None
            
            # Check subscription expiration
            if user.subscription_expires and user.subscription_expires < datetime.utcnow():
                logger.warning(f"Login failed: subscription expired for: {email}")
                return None
            
            # Create access token
            token = create_access_token(
                identity=user.id,
                expires_delta=timedelta(hours=24)
            )
            
            logger.info(f"User logged in successfully: {email}")
            
            return {
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'tier': user.subscription_tier,
                    'subscription_expires': user.subscription_expires.isoformat() if user.subscription_expires else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error in login_user: {e}")
            return None
    
    def get_current_user(self):
        """Get current authenticated user"""
        try:
            user_id = get_jwt_identity()
            if user_id:
                return self.db_manager.get_user_by_id(user_id)
            return None
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
    
    def check_tier_limit(self, user, limit_type: str, current_usage: int = 0):
        """
        Check if user has exceeded tier limits
        
        Args:
            user: User object
            limit_type: Type of limit to check
            current_usage: Current usage count
            
        Returns:
            bool: True if within limits, False if exceeded
        """
        try:
            tier = user.subscription_tier
            if tier not in TIER_LIMITS:
                tier = 'free'  # Default to free tier
            
            limit = TIER_LIMITS[tier].get(limit_type, 0)
            return current_usage < limit
            
        except Exception as e:
            logger.error(f"Error checking tier limit: {e}")
            return False
    
    def get_user_limits(self, user):
        """Get user's tier limits"""
        try:
            tier = user.subscription_tier
            if tier not in TIER_LIMITS:
                tier = 'free'
            
            return TIER_LIMITS[tier].copy()
            
        except Exception as e:
            logger.error(f"Error getting user limits: {e}")
            return TIER_LIMITS['free'].copy()


def auth_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return jsonify({'error': 'Authentication required'}), 401
    return decorated_function


def tier_required(min_tier: str):
    """Decorator to require minimum subscription tier"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                
                # Get user from database
                db_manager = DatabaseManager()
                user = db_manager.get_user_by_id(user_id)
                
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                
                # Check tier
                tier_order = ['free', 'pro', 'enterprise']
                user_tier_index = tier_order.index(user.subscription_tier) if user.subscription_tier in tier_order else 0
                required_tier_index = tier_order.index(min_tier) if min_tier in tier_order else 0
                
                if user_tier_index < required_tier_index:
                    return jsonify({
                        'error': f'Subscription tier {min_tier} or higher required',
                        'current_tier': user.subscription_tier
                    }), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Tier check failed: {e}")
                return jsonify({'error': 'Authentication required'}), 401
        return decorated_function
    return decorator


def limit_usage(limit_type: str):
    """Decorator to limit usage based on tier"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                
                # Get user from database
                db_manager = DatabaseManager()
                user = db_manager.get_user_by_id(user_id)
                
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                
                # Check limits (simplified - in production, track actual usage)
                auth_manager = AuthManager(db_manager)
                if not auth_manager.check_tier_limit(user, limit_type):
                    limits = auth_manager.get_user_limits(user)
                    return jsonify({
                        'error': f'Usage limit exceeded for {limit_type}',
                        'limit': limits.get(limit_type, 0),
                        'tier': user.subscription_tier
                    }), 429
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Usage limit check failed: {e}")
                return jsonify({'error': 'Authentication required'}), 401
        return decorated_function
    return decorator


# Flask route handlers
def register_handler():
    """Handle user registration"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate email format
        if '@' not in data['email']:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Create auth manager
        db_manager = DatabaseManager()
        auth_manager = AuthManager(db_manager)
        
        # Register user
        user = auth_manager.register_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            tier=data.get('tier', 'free')
        )
        
        if user:
            return jsonify({
                'message': 'User registered successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'tier': user.subscription_tier
                }
            }), 201
        else:
            return jsonify({'error': 'Registration failed'}), 500
            
    except Exception as e:
        logger.error(f"Registration handler error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def login_handler():
    """Handle user login"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400
        
        # Create auth manager
        db_manager = DatabaseManager()
        auth_manager = AuthManager(db_manager)
        
        # Login user
        result = auth_manager.login_user(data['email'], data['password'])
        
        if result:
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        logger.error(f"Login handler error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def profile_handler():
    """Get user profile"""
    try:
        # Create auth manager
        db_manager = DatabaseManager()
        auth_manager = AuthManager(db_manager)
        
        # Get current user
        user = auth_manager.get_current_user()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user limits
        limits = auth_manager.get_user_limits(user)
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'tier': user.subscription_tier,
                'subscription_expires': user.subscription_expires.isoformat() if user.subscription_expires else None,
                'created_at': user.created_at.isoformat() if user.created_at else None
            },
            'limits': limits
        }), 200
        
    except Exception as e:
        logger.error(f"Profile handler error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def upgrade_tier_handler():
    """Handle tier upgrade (placeholder for payment integration)"""
    try:
        data = request.get_json()
        
        if not data or 'tier' not in data:
            return jsonify({'error': 'Tier required'}), 400
        
        tier = data['tier']
        if tier not in ['pro', 'enterprise']:
            return jsonify({'error': 'Invalid tier'}), 400
        
        # Get current user
        db_manager = DatabaseManager()
        auth_manager = AuthManager(db_manager)
        user = auth_manager.get_current_user()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update user tier (in production, this would be done after payment)
        user.subscription_tier = tier
        user.subscription_expires = datetime.utcnow() + timedelta(days=30)  # 30-day trial
        
        db_manager.update_user(user)
        
        return jsonify({
            'message': f'Upgraded to {tier} tier',
            'tier': tier,
            'expires': user.subscription_expires.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Upgrade tier handler error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# Initialize JWT with app
def init_jwt(app):
    """Initialize JWT with Flask app"""
    jwt.init_app(app)
    
    # Configure JWT
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Add error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Missing token'}), 401