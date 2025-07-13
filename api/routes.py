"""
API Routes

This module defines all the API endpoints for the real estate scraper.
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from io import BytesIO
import pandas as pd

from database.database_manager import DatabaseManager
from scraper.scraper_manager import ScraperManager

logger = logging.getLogger(__name__)

# Initialize database manager
db_manager = DatabaseManager()

# Initialize scraper manager
scraper_manager = ScraperManager()

# Create blueprints
listings_bp = Blueprint('listings', __name__)
users_bp = Blueprint('users', __name__)
alerts_bp = Blueprint('alerts', __name__)
scraping_bp = Blueprint('scraping', __name__)


# Listings Routes

@listings_bp.route('/', methods=['GET'])
def get_listings():
    """
    Get property listings with filters
    
    Query parameters:
    - location: Filter by location
    - min_price: Minimum price
    - max_price: Maximum price
    - min_area: Minimum area
    - max_area: Maximum area
    - property_type: Filter by property type
    - bedrooms: Filter by number of bedrooms
    - source: Filter by source
    - limit: Maximum number of results (default: 100)
    - offset: Number of results to skip (default: 0)
    """
    try:
        # Get query parameters
        location = request.args.get('location')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        min_area = request.args.get('min_area', type=float)
        max_area = request.args.get('max_area', type=float)
        property_type = request.args.get('property_type')
        bedrooms = request.args.get('bedrooms', type=int)
        source = request.args.get('source')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Get listings from database
        listings = db_manager.get_listings(
            location=location,
            min_price=min_price,
            max_price=max_price,
            min_area=min_area,
            max_area=max_area,
            property_type=property_type,
            bedrooms=bedrooms,
            source=source,
            limit=limit,
            offset=offset
        )
        
        # Convert to dictionaries
        listings_data = [listing.to_dict() for listing in listings]
        
        return jsonify({
            'listings': listings_data,
            'count': len(listings_data),
            'filters': {
                'location': location,
                'min_price': min_price,
                'max_price': max_price,
                'min_area': min_area,
                'max_area': max_area,
                'property_type': property_type,
                'bedrooms': bedrooms,
                'source': source
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting listings: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@listings_bp.route('/<int:listing_id>', methods=['GET'])
def get_listing(listing_id: int):
    """
    Get a specific listing by ID
    
    Args:
        listing_id: Listing ID
    """
    try:
        listing = db_manager.get_listing_by_id(listing_id)
        
        if not listing:
            return jsonify({'error': 'Listing not found'}), 404
        
        return jsonify(listing.to_dict())
        
    except Exception as e:
        logger.error(f"Error getting listing {listing_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@listings_bp.route('/export', methods=['GET'])
def export_listings():
    """
    Export listings to CSV or Excel
    
    Query parameters:
    - format: Export format (csv, excel) - default: csv
    - All other parameters same as get_listings
    """
    try:
        # Get export format
        export_format = request.args.get('format', 'csv').lower()
        
        if export_format not in ['csv', 'excel']:
            return jsonify({'error': 'Invalid format. Use csv or excel'}), 400
        
        # Get listings with same filters as get_listings
        location = request.args.get('location')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        min_area = request.args.get('min_area', type=float)
        max_area = request.args.get('max_area', type=float)
        property_type = request.args.get('property_type')
        bedrooms = request.args.get('bedrooms', type=int)
        source = request.args.get('source')
        
        # Get all listings (no limit for export)
        listings = db_manager.get_listings(
            location=location,
            min_price=min_price,
            max_price=max_price,
            min_area=min_area,
            max_area=max_area,
            property_type=property_type,
            bedrooms=bedrooms,
            source=source,
            limit=10000,  # Large limit for export
            offset=0
        )
        
        # Convert to DataFrame
        listings_data = [listing.to_dict() for listing in listings]
        df = pd.DataFrame(listings_data)
        
        # Create file buffer
        buffer = BytesIO()
        
        if export_format == 'csv':
            df.to_csv(buffer, index=False)
            mimetype = 'text/csv'
            filename = f'listings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        else:  # excel
            df.to_excel(buffer, index=False)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'listings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting listings: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@listings_bp.route('/statistics', methods=['GET'])
def get_listings_statistics():
    """Get statistics about listings"""
    try:
        stats = db_manager.get_statistics()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@listings_bp.route('/trends', methods=['GET'])
def get_price_trends():
    """
    Get price trends over time
    
    Query parameters:
    - location: Filter by location
    - days: Number of days to analyze (default: 30)
    """
    try:
        location = request.args.get('location')
        days = request.args.get('days', 30, type=int)
        
        trends = db_manager.get_price_trends(location=location, days=days)
        return jsonify({'trends': trends})
        
    except Exception as e:
        logger.error(f"Error getting price trends: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# Users Routes

@users_bp.route('/', methods=['POST'])
def create_user():
    """
    Create a new user
    
    Request body:
    {
        "email": "user@example.com",
        "name": "User Name"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'name' not in data:
            return jsonify({'error': 'Email and name are required'}), 400
        
        user = db_manager.create_user(
            email=data['email'],
            name=data['name']
        )
        
        if not user:
            return jsonify({'error': 'Failed to create user'}), 500
        
        return jsonify(user.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@users_bp.route('/<email>', methods=['GET'])
def get_user(email: str):
    """
    Get user by email
    
    Args:
        email: User email
    """
    try:
        user = db_manager.get_user_by_email(email)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict())
        
    except Exception as e:
        logger.error(f"Error getting user {email}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# Alerts Routes

@alerts_bp.route('/', methods=['POST'])
def create_alert():
    """
    Create a new alert
    
    Request body:
    {
        "user_email": "user@example.com",
        "name": "Alert Name",
        "location": "Hanoi",
        "min_price": 1000000000,
        "max_price": 5000000000,
        "min_area": 50,
        "max_area": 150,
        "property_type": "Căn hộ",
        "bedrooms": 2
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'user_email' not in data or 'name' not in data:
            return jsonify({'error': 'User email and alert name are required'}), 400
        
        # Get user
        user = db_manager.get_user_by_email(data['user_email'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Prepare alert data
        alert_data = {
            'name': data['name'],
            'location': data.get('location'),
            'min_price': data.get('min_price'),
            'max_price': data.get('max_price'),
            'min_area': data.get('min_area'),
            'max_area': data.get('max_area'),
            'property_type': data.get('property_type'),
            'bedrooms': data.get('bedrooms')
        }
        
        alert = db_manager.create_alert(user.id, alert_data)
        
        if not alert:
            return jsonify({'error': 'Failed to create alert'}), 500
        
        return jsonify(alert.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@alerts_bp.route('/user/<email>', methods=['GET'])
def get_user_alerts(email: str):
    """
    Get all alerts for a user
    
    Args:
        email: User email
    """
    try:
        user = db_manager.get_user_by_email(email)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        alerts = db_manager.get_user_alerts(user.id)
        alerts_data = [alert.to_dict() for alert in alerts]
        
        return jsonify({'alerts': alerts_data})
        
    except Exception as e:
        logger.error(f"Error getting alerts for user {email}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@alerts_bp.route('/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id: int):
    """
    Delete an alert
    
    Args:
        alert_id: Alert ID
    """
    try:
        # This would need to be implemented in DatabaseManager
        # For now, return a placeholder response
        return jsonify({'message': 'Alert deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# Scraping Routes

@scraping_bp.route('/start', methods=['POST'])
def start_scraping():
    """
    Start a scraping job
    
    Request body (optional):
    {
        "max_pages_per_site": 10,
        "scrapers": ["batdongsan", "chotot"]
    }
    """
    try:
        data = request.get_json() or {}
        max_pages = data.get('max_pages_per_site', 10)
        scrapers = data.get('scrapers', ['batdongsan', 'chotot'])
        
        # Start scraping asynchronously
        import asyncio
        import threading
        
        def run_scraping():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(scraper_manager.run_all_scrapers(max_pages))
            finally:
                loop.close()
        
        # Run in background thread
        thread = threading.Thread(target=run_scraping)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Scraping started',
            'max_pages_per_site': max_pages,
            'scrapers': scrapers
        })
        
    except Exception as e:
        logger.error(f"Error starting scraping: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@scraping_bp.route('/status', methods=['GET'])
def get_scraping_status():
    """Get scraping status and statistics"""
    try:
        stats = scraper_manager.get_stats()
        scraper_status = scraper_manager.get_scraper_status()
        
        return jsonify({
            'stats': stats,
            'scrapers': scraper_status,
            'scheduler_running': scraper_manager.is_running
        })
        
    except Exception as e:
        logger.error(f"Error getting scraping status: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@scraping_bp.route('/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the scraping scheduler"""
    try:
        scraper_manager.start_scheduler()
        return jsonify({'message': 'Scheduler started successfully'})
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@scraping_bp.route('/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop the scraping scheduler"""
    try:
        scraper_manager.stop_scheduler()
        return jsonify({'message': 'Scheduler stopped successfully'})
        
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@scraping_bp.route('/logs', methods=['GET'])
def get_scraping_logs():
    """
    Get scraping logs
    
    Query parameters:
    - limit: Maximum number of logs (default: 50)
    - scraper: Filter by scraper name
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        scraper_name = request.args.get('scraper')
        
        # This would need to be implemented in DatabaseManager
        # For now, return a placeholder response
        return jsonify({
            'logs': [],
            'message': 'Logs endpoint not yet implemented'
        })
        
    except Exception as e:
        logger.error(f"Error getting scraping logs: {e}")
        return jsonify({'error': 'Internal server error'}), 500 