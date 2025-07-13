"""
Real Estate Scraper - Main Application

This is the main entry point for the Real Estate Scraper application.
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import application components
from api.app import create_app
from database.migrations import run_migrations
from database.database_manager import DatabaseManager
from scraper.scraper_manager import ScraperManager
from utils.email_service import EmailService


class RealEstateScraperApp:
    """
    Main application class that coordinates all components
    """
    
    def __init__(self):
        """Initialize the application"""
        self.app = None
        self.db_manager = None
        self.scraper_manager = None
        self.email_service = None
        
    def initialize(self):
        """Initialize all application components"""
        logger.info("Initializing Real Estate Scraper application...")
        
        try:
            # Run database migrations
            logger.info("Running database migrations...")
            if not run_migrations():
                logger.error("Database migrations failed")
                return False
            
            # Initialize database manager
            self.db_manager = DatabaseManager()
            logger.info("Database manager initialized")
            
            # Initialize scraper manager
            self.scraper_manager = ScraperManager()
            logger.info("Scraper manager initialized")
            
            # Initialize email service
            self.email_service = EmailService()
            logger.info("Email service initialized")
            
            # Create Flask app
            self.app = create_app()
            logger.info("Flask application created")
            
            logger.info("Application initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Application initialization failed: {e}")
            return False
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """
        Run the application
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        if not self.initialize():
            logger.error("Failed to initialize application")
            return
        
        logger.info(f"Starting Real Estate Scraper on {host}:{port}")
        
        try:
            # Start the scheduler in development mode
            if debug:
                logger.info("Starting scraper scheduler in development mode")
                self.scraper_manager.start_scheduler()
            
            # Run the Flask application
            self.app.run(host=host, port=port, debug=debug)
            
        except KeyboardInterrupt:
            logger.info("Application stopped by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            # Cleanup
            if self.scraper_manager:
                self.scraper_manager.stop_scheduler()
            logger.info("Application shutdown complete")


def run_sample_scraping():
    """Run a sample scraping job for testing"""
    logger.info("Running sample scraping...")
    
    try:
        # Initialize components
        db_manager = DatabaseManager()
        scraper_manager = ScraperManager()
        
        # Run sample scraping
        async def run_scraping():
            listings = await scraper_manager.run_sample_scraping()
            
            # Save to database
            for listing in listings:
                listing_data = {
                    'title': listing.title,
                    'location': listing.location,
                    'price': listing.price,
                    'area': listing.area,
                    'price_per_m2': listing.price_per_m2,
                    'image_url': listing.image_url,
                    'link': listing.link,
                    'property_type': listing.property_type,
                    'bedrooms': listing.bedrooms,
                    'bathrooms': listing.bathrooms,
                    'timestamp': listing.timestamp,
                    'source': listing.source,
                    'raw_data': str(listing.raw_data)
                }
                db_manager.insert_listing(listing_data)
            
            logger.info(f"Sample scraping completed. Saved {len(listings)} listings")
        
        # Run the scraping
        asyncio.run(run_scraping())
        
    except Exception as e:
        logger.error(f"Sample scraping failed: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Real Estate Scraper Application')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--sample-scraping', action='store_true', help='Run sample scraping')
    parser.add_argument('--migrate', action='store_true', help='Run database migrations only')
    
    args = parser.parse_args()
    
    if args.migrate:
        logger.info("Running database migrations...")
        success = run_migrations()
        if success:
            logger.info("Migrations completed successfully")
        else:
            logger.error("Migrations failed")
        return
    
    if args.sample_scraping:
        run_sample_scraping()
        return
    
    # Create and run the application
    app = RealEstateScraperApp()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main() 