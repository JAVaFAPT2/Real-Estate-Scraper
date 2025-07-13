"""
Database Migrations

This module handles database schema migrations and updates.
"""

import logging
from typing import List, Dict, Any
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

from .models import Base
from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages database migrations
    
    This class handles:
    - Creating initial database schema
    - Running migrations
    - Tracking migration status
    """
    
    def __init__(self, database_manager: DatabaseManager):
        """
        Initialize the migration manager
        
        Args:
            database_manager: Database manager instance
        """
        self.db_manager = database_manager
        self.migrations = [
            {
                'version': 1,
                'name': 'Initial schema',
                'sql': self._get_initial_schema()
            },
            {
                'version': 2,
                'name': 'Add indexes for performance',
                'sql': self._get_index_migrations()
            },
            {
                'version': 3,
                'name': 'Add subscription fields',
                'sql': self._get_subscription_migrations()
            }
        ]
    
    def _get_initial_schema(self) -> List[str]:
        """Get SQL for initial database schema"""
        return [
            """
            CREATE TABLE IF NOT EXISTS property_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(500) NOT NULL,
                location VARCHAR(200) NOT NULL,
                price FLOAT NOT NULL,
                area FLOAT NOT NULL,
                price_per_m2 FLOAT NOT NULL,
                image_url VARCHAR(500),
                link VARCHAR(500) NOT NULL,
                property_type VARCHAR(100) NOT NULL,
                bedrooms INTEGER,
                bathrooms INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                source VARCHAR(50) NOT NULL,
                raw_data TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(200) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                subscription_tier VARCHAR(20) DEFAULT 'free',
                subscription_expires DATETIME
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                location VARCHAR(200),
                min_price FLOAT,
                max_price FLOAT,
                min_area FLOAT,
                max_area FLOAT,
                property_type VARCHAR(100),
                bedrooms INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                last_triggered DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scraping_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scraper_name VARCHAR(50) NOT NULL,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                end_time DATETIME,
                listings_found INTEGER DEFAULT 0,
                listings_new INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'running',
                error_message TEXT
            )
            """
        ]
    
    def _get_index_migrations(self) -> List[str]:
        """Get SQL for performance indexes"""
        return [
            "CREATE INDEX IF NOT EXISTS idx_listings_location ON property_listings(location)",
            "CREATE INDEX IF NOT EXISTS idx_listings_price ON property_listings(price)",
            "CREATE INDEX IF NOT EXISTS idx_listings_timestamp ON property_listings(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_listings_source ON property_listings(source)",
            "CREATE INDEX IF NOT EXISTS idx_listings_link ON property_listings(link)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_logs_scraper ON scraping_logs(scraper_name)",
            "CREATE INDEX IF NOT EXISTS idx_logs_start_time ON scraping_logs(start_time)"
        ]
    
    def _get_subscription_migrations(self) -> List[str]:
        """Get SQL for subscription-related fields"""
        return [
            "ALTER TABLE users ADD COLUMN subscription_tier VARCHAR(20) DEFAULT 'free'",
            "ALTER TABLE users ADD COLUMN subscription_expires DATETIME"
        ]
    
    def get_migration_table_sql(self) -> str:
        """Get SQL to create migration tracking table"""
        return """
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL,
            name VARCHAR(200) NOT NULL,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
        """
    
    def get_applied_migrations(self) -> List[int]:
        """Get list of applied migration versions"""
        try:
            with self.db_manager.get_session() as session:
                # Create migrations table if it doesn't exist
                session.execute(text(self.get_migration_table_sql()))
                session.commit()
                
                # Get applied migrations
                result = session.execute(text("SELECT version FROM migrations ORDER BY version"))
                return [row[0] for row in result.fetchall()]
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting applied migrations: {e}")
            return []
    
    def apply_migration(self, migration: Dict[str, Any]) -> bool:
        """
        Apply a single migration
        
        Args:
            migration: Migration dictionary
            
        Returns:
            bool: True if successful
        """
        try:
            with self.db_manager.get_session() as session:
                # Execute migration SQL
                for sql in migration['sql']:
                    session.execute(text(sql))
                
                # Record migration
                session.execute(
                    text("INSERT INTO migrations (version, name) VALUES (:version, :name)"),
                    {'version': migration['version'], 'name': migration['name']}
                )
                
                session.commit()
                logger.info(f"Applied migration {migration['version']}: {migration['name']}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error applying migration {migration['version']}: {e}")
            return False
    
    def run_migrations(self) -> bool:
        """
        Run all pending migrations
        
        Returns:
            bool: True if all migrations successful
        """
        logger.info("Starting database migrations...")
        
        # Get applied migrations
        applied_versions = self.get_applied_migrations()
        
        # Find pending migrations
        pending_migrations = [
            migration for migration in self.migrations
            if migration['version'] not in applied_versions
        ]
        
        if not pending_migrations:
            logger.info("No pending migrations")
            return True
        
        logger.info(f"Found {len(pending_migrations)} pending migrations")
        
        # Apply migrations in order
        for migration in pending_migrations:
            if not self.apply_migration(migration):
                logger.error(f"Migration {migration['version']} failed")
                return False
        
        logger.info("All migrations completed successfully")
        return True
    
    def create_initial_data(self) -> bool:
        """
        Create initial sample data for testing
        
        Returns:
            bool: True if successful
        """
        try:
            with self.db_manager.get_session() as session:
                # Check if we already have data
                result = session.execute(text("SELECT COUNT(*) FROM property_listings"))
                if result.scalar() > 0:
                    logger.info("Database already contains data, skipping initial data creation")
                    return True
                
                # Create sample user
                session.execute(
                    text("""
                        INSERT INTO users (email, name, subscription_tier)
                        VALUES (:email, :name, :tier)
                    """),
                    {
                        'email': 'demo@example.com',
                        'name': 'Demo User',
                        'tier': 'pro'
                    }
                )
                
                # Create sample alerts
                session.execute(
                    text("""
                        INSERT INTO alerts (user_id, name, location, min_price, max_price, property_type)
                        VALUES (:user_id, :name, :location, :min_price, :max_price, :type)
                    """),
                    {
                        'user_id': 1,
                        'name': 'Hanoi Apartments',
                        'location': 'Hanoi',
                        'min_price': 1000000000,  # 1 billion VND
                        'max_price': 5000000000,  # 5 billion VND
                        'type': 'Căn hộ'
                    }
                )
                
                session.commit()
                logger.info("Created initial sample data")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error creating initial data: {e}")
            return False


def run_migrations(database_url: str = "sqlite:///realestate.db") -> bool:
    """
    Run database migrations
    
    Args:
        database_url: Database URL
        
    Returns:
        bool: True if migrations successful
    """
    try:
        # Create database manager
        db_manager = DatabaseManager(database_url)
        
        # Create migration manager
        migration_manager = MigrationManager(db_manager)
        
        # Run migrations
        success = migration_manager.run_migrations()
        
        if success:
            # Create initial data for development
            migration_manager.create_initial_data()
        
        return success
        
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        return False


def reset_database(database_url: str = "sqlite:///realestate.db") -> bool:
    """
    Reset database (drop all tables and recreate)
    
    Args:
        database_url: Database URL
        
    Returns:
        bool: True if successful
    """
    try:
        logger.warning("Resetting database - this will delete all data!")
        
        # Create database manager
        db_manager = DatabaseManager(database_url)
        
        # Drop all tables
        Base.metadata.drop_all(bind=db_manager.engine)
        logger.info("Dropped all tables")
        
        # Recreate tables and run migrations
        success = run_migrations(database_url)
        
        if success:
            logger.info("Database reset completed successfully")
        
        return success
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        success = reset_database()
    else:
        success = run_migrations()
    
    if success:
        print("Database operations completed successfully")
        sys.exit(0)
    else:
        print("Database operations failed")
        sys.exit(1) 