#!/usr/bin/env python3
"""
Basic functionality test for the Real Estate Scraper

This script tests the core functionality without requiring external dependencies.
"""

import sys
import os
import logging

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        # Test database imports
        from database.models import PropertyListing, User, Alert, ScrapingLog, Base
        logger.info("✓ Database models imported successfully")
        
        from database.database_manager import DatabaseManager
        logger.info("✓ Database manager imported successfully")
        
        from database.migrations import run_migrations
        logger.info("✓ Database migrations imported successfully")
        
        # Test scraper imports
        from scraper.base_scraper import PropertyListing as ScraperPropertyListing
        logger.info("✓ Base scraper imported successfully")
        
        from scraper.scraper_manager import ScraperManager
        logger.info("✓ Scraper manager imported successfully")
        
        # Test API imports
        from api.app import create_app
        logger.info("✓ API app imported successfully")
        
        # Test utils imports
        from utils.email_service import EmailService
        logger.info("✓ Email service imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False

def test_database_models():
    """Test database model creation"""
    logger.info("Testing database models...")
    
    try:
        from database.models import PropertyListing, User, Alert, ScrapingLog
        
        # Test PropertyListing model
        listing = PropertyListing(
            title="Test Property",
            location="Test Location",
            price=1000000000.0,
            area=100.0,
            price_per_m2=10000000.0,
            image_url="http://example.com/image.jpg",
            link="http://example.com/property",
            property_type="Căn hộ",
            bedrooms=2,
            bathrooms=2,
            timestamp=None,
            source="test",
            raw_data="{}"
        )
        
        # Test to_dict method
        listing_dict = listing.to_dict()
        assert listing_dict['title'] == "Test Property"
        assert listing_dict['price'] == 1000000000.0
        
        logger.info("✓ Database models work correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database model test failed: {e}")
        return False

def test_scraper_manager():
    """Test scraper manager initialization"""
    logger.info("Testing scraper manager...")
    
    try:
        from scraper.scraper_manager import ScraperManager
        
        manager = ScraperManager()
        
        # Check if scrapers are initialized
        assert 'batdongsan' in manager.scrapers
        assert 'chotot' in manager.scrapers
        
        # Check stats
        stats = manager.get_stats()
        assert 'total_runs' in stats
        assert 'successful_runs' in stats
        
        logger.info("✓ Scraper manager works correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Scraper manager test failed: {e}")
        return False

def test_api_app():
    """Test API app creation"""
    logger.info("Testing API app creation...")
    
    try:
        from api.app import create_app
        
        app = create_app()
        
        # Check if app is created
        assert app is not None
        
        # Check if blueprints are registered
        blueprints = list(app.blueprints.keys())
        expected_blueprints = ['listings', 'users', 'alerts', 'scraping', 'auth']
        
        for blueprint in expected_blueprints:
            assert blueprint in blueprints, f"Blueprint {blueprint} not found"
        
        logger.info("✓ API app created successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ API app test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting basic functionality tests...")
    
    tests = [
        test_imports,
        test_database_models,
        test_scraper_manager,
        test_api_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        logger.info("")  # Empty line for readability
    
    logger.info(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The core functionality is working.")
        return 0
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())