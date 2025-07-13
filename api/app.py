"""
Flask Application Factory

This module creates and configures the Flask application.
"""

import os
import logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from .routes import listings_bp, users_bp, alerts_bp, scraping_bp

# Load environment variables
load_dotenv()


def create_app(config_name: str = None) -> Flask:
    """
    Create and configure the Flask application
    
    Args:
        config_name: Configuration name (development, production, testing)
        
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(get_config(config_name))
    
    # Setup logging
    setup_logging(app)
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register blueprints
    app.register_blueprint(listings_bp, url_prefix='/api/listings')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(scraping_bp, url_prefix='/api/scraping')
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return {'status': 'healthy', 'service': 'real-estate-scraper-api'}
    
    @app.route('/')
    def index():
        """API root endpoint"""
        return {
            'name': 'Real Estate Scraper API',
            'version': '1.0.0',
            'description': 'API for scraping and managing real estate listings',
            'endpoints': {
                'listings': '/api/listings',
                'users': '/api/users',
                'alerts': '/api/alerts',
                'scraping': '/api/scraping',
                'health': '/health'
            }
        }
    
    return app


def get_config(config_name: str = None) -> object:
    """
    Get configuration object based on environment
    
    Args:
        config_name: Configuration name
        
    Returns:
        object: Configuration object
    """
    class Config:
        """Base configuration"""
        SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
        DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///realestate.db'
        API_RATE_LIMIT = int(os.environ.get('API_RATE_LIMIT', 100))
        API_RATE_LIMIT_WINDOW = int(os.environ.get('API_RATE_LIMIT_WINDOW', 3600))
        
        # Scraping configuration
        SCRAPING_DELAY = int(os.environ.get('SCRAPING_DELAY', 3))
        MAX_PAGES_PER_SITE = int(os.environ.get('MAX_PAGES_PER_SITE', 10))
        
        # Email configuration
        SMTP_SERVER = os.environ.get('SMTP_SERVER')
        SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
        SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
        SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
        ALERT_EMAIL_FROM = os.environ.get('ALERT_EMAIL_FROM')
    
    class DevelopmentConfig(Config):
        """Development configuration"""
        DEBUG = True
        TESTING = False
    
    class ProductionConfig(Config):
        """Production configuration"""
        DEBUG = False
        TESTING = False
    
    class TestingConfig(Config):
        """Testing configuration"""
        DEBUG = True
        TESTING = True
        DATABASE_URL = 'sqlite:///:memory:'
    
    # Determine configuration based on environment
    if config_name:
        config_map = {
            'development': DevelopmentConfig,
            'production': ProductionConfig,
            'testing': TestingConfig
        }
        return config_map.get(config_name, DevelopmentConfig)
    
    # Auto-detect based on environment variables
    if os.environ.get('FLASK_ENV') == 'production':
        return ProductionConfig
    elif os.environ.get('FLASK_ENV') == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig


def setup_logging(app: Flask):
    """
    Setup application logging
    
    Args:
        app: Flask application
    """
    if not app.debug:
        # Production logging
        import logging.handlers
        
        # Create logs directory if it doesn't exist
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # File handler
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'api.log'),
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Real Estate Scraper API startup')
    else:
        # Development logging
        app.logger.setLevel(logging.DEBUG)


def register_error_handlers(app: Flask):
    """
    Register error handlers
    
    Args:
        app: Flask application
    """
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return {
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        app.logger.error(f'Server Error: {error}')
        return {
            'error': 'Internal Server Error',
            'message': 'An internal server error occurred',
            'status_code': 500
        }, 500
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 errors"""
        return {
            'error': 'Bad Request',
            'message': 'The request was malformed or invalid',
            'status_code': 400
        }, 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 errors"""
        return {
            'error': 'Unauthorized',
            'message': 'Authentication required',
            'status_code': 401
        }, 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 errors"""
        return {
            'error': 'Forbidden',
            'message': 'Access denied',
            'status_code': 403
        }, 403


# Create app instance for direct import
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 