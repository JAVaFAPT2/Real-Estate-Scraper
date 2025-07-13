"""
API Package

This package contains the Flask API endpoints for the real estate scraper.
"""

from .app import create_app
from .routes import listings_bp, users_bp, alerts_bp, scraping_bp

__all__ = [
    'create_app',
    'listings_bp',
    'users_bp', 
    'alerts_bp',
    'scraping_bp'
] 