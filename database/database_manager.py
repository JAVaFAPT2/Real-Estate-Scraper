"""
Database Manager

This module provides a high-level interface for database operations.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, and_, or_, desc, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, PropertyListing, User, Alert, ScrapingLog

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages all database operations for the real estate scraper
    
    This class provides methods for:
    - CRUD operations on property listings
    - User management
    - Alert management
    - Scraping logs
    - Data queries and filtering
    """
    
    def __init__(self, database_url: str = "sqlite:///realestate.db"):
        """
        Initialize the database manager
        
        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Database initialized: {database_url}")
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    # Property Listing Operations
    
    def insert_listing(self, listing_data: Dict[str, Any]) -> Optional[PropertyListing]:
        """
        Insert a new property listing
        
        Args:
            listing_data: Dictionary containing listing data
            
        Returns:
            PropertyListing: The inserted listing or None if failed
        """
        try:
            with self.get_session() as session:
                # Check if listing already exists (by link)
                existing = session.query(PropertyListing).filter(
                    PropertyListing.link == listing_data['link']
                ).first()
                
                if existing:
                    logger.debug(f"Listing already exists: {listing_data['link']}")
                    return existing
                
                # Create new listing
                listing = PropertyListing(**listing_data)
                session.add(listing)
                session.commit()
                session.refresh(listing)
                
                logger.info(f"Inserted new listing: {listing.title}")
                return listing
                
        except SQLAlchemyError as e:
            logger.error(f"Error inserting listing: {e}")
            return None
    
    def insert_listings_batch(self, listings: List[Dict[str, Any]]) -> int:
        """
        Insert multiple listings in batch
        
        Args:
            listings: List of listing dictionaries
            
        Returns:
            int: Number of new listings inserted
        """
        inserted_count = 0
        
        try:
            with self.get_session() as session:
                for listing_data in listings:
                    # Check if listing already exists
                    existing = session.query(PropertyListing).filter(
                        PropertyListing.link == listing_data['link']
                    ).first()
                    
                    if not existing:
                        listing = PropertyListing(**listing_data)
                        session.add(listing)
                        inserted_count += 1
                
                session.commit()
                logger.info(f"Inserted {inserted_count} new listings")
                
        except SQLAlchemyError as e:
            logger.error(f"Error in batch insert: {e}")
            return 0
        
        return inserted_count
    
    def get_listings(
        self,
        location: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_area: Optional[float] = None,
        max_area: Optional[float] = None,
        property_type: Optional[str] = None,
        bedrooms: Optional[int] = None,
        source: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PropertyListing]:
        """
        Get property listings with filters
        
        Args:
            location: Filter by location
            min_price: Minimum price
            max_price: Maximum price
            min_area: Minimum area
            max_area: Maximum area
            property_type: Filter by property type
            bedrooms: Filter by number of bedrooms
            source: Filter by source
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[PropertyListing]: Filtered listings
        """
        try:
            with self.get_session() as session:
                query = session.query(PropertyListing)
                
                # Apply filters
                if location:
                    query = query.filter(PropertyListing.location.contains(location))
                
                if min_price is not None:
                    query = query.filter(PropertyListing.price >= min_price)
                
                if max_price is not None:
                    query = query.filter(PropertyListing.price <= max_price)
                
                if min_area is not None:
                    query = query.filter(PropertyListing.area >= min_area)
                
                if max_area is not None:
                    query = query.filter(PropertyListing.area <= max_area)
                
                if property_type:
                    query = query.filter(PropertyListing.property_type == property_type)
                
                if bedrooms is not None:
                    query = query.filter(PropertyListing.bedrooms == bedrooms)
                
                if source:
                    query = query.filter(PropertyListing.source == source)
                
                # Order by timestamp (newest first)
                query = query.order_by(desc(PropertyListing.timestamp))
                
                # Apply pagination
                query = query.offset(offset).limit(limit)
                
                return query.all()
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting listings: {e}")
            return []
    
    def get_new_listings(self, since: datetime) -> List[PropertyListing]:
        """
        Get listings added since a specific time
        
        Args:
            since: Get listings added after this time
            
        Returns:
            List[PropertyListing]: New listings
        """
        try:
            with self.get_session() as session:
                return session.query(PropertyListing).filter(
                    PropertyListing.timestamp >= since
                ).order_by(desc(PropertyListing.timestamp)).all()
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting new listings: {e}")
            return []
    
    def get_listing_by_id(self, listing_id: int) -> Optional[PropertyListing]:
        """
        Get a listing by ID
        
        Args:
            listing_id: Listing ID
            
        Returns:
            PropertyListing: The listing or None if not found
        """
        try:
            with self.get_session() as session:
                return session.query(PropertyListing).filter(
                    PropertyListing.id == listing_id
                ).first()
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting listing by ID: {e}")
            return None
    
    # User Operations
    
    def create_user(self, email: str, name: str) -> Optional[User]:
        """
        Create a new user
        
        Args:
            email: User email
            name: User name
            
        Returns:
            User: The created user or None if failed
        """
        try:
            with self.get_session() as session:
                # Check if user already exists
                existing = session.query(User).filter(User.email == email).first()
                if existing:
                    logger.warning(f"User already exists: {email}")
                    return existing
                
                user = User(email=email, name=name)
                session.add(user)
                session.commit()
                session.refresh(user)
                
                logger.info(f"Created new user: {email}")
                return user
                
        except SQLAlchemyError as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email
        
        Args:
            email: User email
            
        Returns:
            User: The user or None if not found
        """
        try:
            with self.get_session() as session:
                return session.query(User).filter(User.email == email).first()
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    # Alert Operations
    
    def create_alert(self, user_id: int, alert_data: Dict[str, Any]) -> Optional[Alert]:
        """
        Create a new alert for a user
        
        Args:
            user_id: User ID
            alert_data: Alert configuration data
            
        Returns:
            Alert: The created alert or None if failed
        """
        try:
            with self.get_session() as session:
                alert = Alert(user_id=user_id, **alert_data)
                session.add(alert)
                session.commit()
                session.refresh(alert)
                
                logger.info(f"Created alert for user {user_id}: {alert.name}")
                return alert
                
        except SQLAlchemyError as e:
            logger.error(f"Error creating alert: {e}")
            return None
    
    def get_user_alerts(self, user_id: int) -> List[Alert]:
        """
        Get all alerts for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List[Alert]: User's alerts
        """
        try:
            with self.get_session() as session:
                return session.query(Alert).filter(
                    Alert.user_id == user_id,
                    Alert.is_active == True
                ).all()
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting user alerts: {e}")
            return []
    
    def check_alerts(self, listing: PropertyListing) -> List[Alert]:
        """
        Check if a listing matches any active alerts
        
        Args:
            listing: Property listing to check
            
        Returns:
            List[Alert]: Matching alerts
        """
        try:
            with self.get_session() as session:
                query = session.query(Alert).filter(Alert.is_active == True)
                
                # Apply alert filters
                if listing.location:
                    query = query.filter(
                        or_(
                            Alert.location.is_(None),
                            Alert.location.contains(listing.location)
                        )
                    )
                
                if listing.price:
                    if listing.price > 0:
                        query = query.filter(
                            or_(
                                Alert.min_price.is_(None),
                                Alert.min_price <= listing.price
                            )
                        )
                        query = query.filter(
                            or_(
                                Alert.max_price.is_(None),
                                Alert.max_price >= listing.price
                            )
                        )
                
                if listing.area:
                    if listing.area > 0:
                        query = query.filter(
                            or_(
                                Alert.min_area.is_(None),
                                Alert.min_area <= listing.area
                            )
                        )
                        query = query.filter(
                            or_(
                                Alert.max_area.is_(None),
                                Alert.max_area >= listing.area
                            )
                        )
                
                if listing.property_type:
                    query = query.filter(
                        or_(
                            Alert.property_type.is_(None),
                            Alert.property_type == listing.property_type
                        )
                    )
                
                if listing.bedrooms:
                    query = query.filter(
                        or_(
                            Alert.bedrooms.is_(None),
                            Alert.bedrooms == listing.bedrooms
                        )
                    )
                
                return query.all()
                
        except SQLAlchemyError as e:
            logger.error(f"Error checking alerts: {e}")
            return []
    
    # Scraping Log Operations
    
    def log_scraping_start(self, scraper_name: str) -> Optional[ScrapingLog]:
        """
        Log the start of a scraping job
        
        Args:
            scraper_name: Name of the scraper
            
        Returns:
            ScrapingLog: The created log entry
        """
        try:
            with self.get_session() as session:
                log = ScrapingLog(scraper_name=scraper_name)
                session.add(log)
                session.commit()
                session.refresh(log)
                return log
                
        except SQLAlchemyError as e:
            logger.error(f"Error logging scraping start: {e}")
            return None
    
    def log_scraping_complete(
        self,
        log_id: int,
        listings_found: int,
        listings_new: int,
        status: str = 'completed',
        error_message: Optional[str] = None
    ) -> bool:
        """
        Log the completion of a scraping job
        
        Args:
            log_id: Log entry ID
            listings_found: Number of listings found
            listings_new: Number of new listings
            status: Job status
            error_message: Error message if failed
            
        Returns:
            bool: True if successful
        """
        try:
            with self.get_session() as session:
                log = session.query(ScrapingLog).filter(ScrapingLog.id == log_id).first()
                if log:
                    log.end_time = datetime.utcnow()
                    log.listings_found = listings_found
                    log.listings_new = listings_new
                    log.status = status
                    log.error_message = error_message
                    session.commit()
                    return True
                return False
                
        except SQLAlchemyError as e:
            logger.error(f"Error logging scraping complete: {e}")
            return False
    
    # Statistics and Analytics
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dict[str, Any]: Statistics
        """
        try:
            with self.get_session() as session:
                total_listings = session.query(func.count(PropertyListing.id)).scalar()
                total_users = session.query(func.count(User.id)).scalar()
                total_alerts = session.query(func.count(Alert.id)).scalar()
                
                # Recent listings (last 24 hours)
                yesterday = datetime.utcnow() - timedelta(days=1)
                recent_listings = session.query(func.count(PropertyListing.id)).filter(
                    PropertyListing.timestamp >= yesterday
                ).scalar()
                
                # Average price
                avg_price = session.query(func.avg(PropertyListing.price)).scalar()
                
                return {
                    'total_listings': total_listings or 0,
                    'total_users': total_users or 0,
                    'total_alerts': total_alerts or 0,
                    'recent_listings_24h': recent_listings or 0,
                    'average_price': float(avg_price) if avg_price else 0.0
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def get_price_trends(self, location: Optional[str] = None, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get price trends over time
        
        Args:
            location: Filter by location
            days: Number of days to analyze
            
        Returns:
            List[Dict[str, Any]]: Price trend data
        """
        try:
            with self.get_session() as session:
                since = datetime.utcnow() - timedelta(days=days)
                query = session.query(
                    func.date(PropertyListing.timestamp).label('date'),
                    func.avg(PropertyListing.price).label('avg_price'),
                    func.avg(PropertyListing.price_per_m2).label('avg_price_per_m2'),
                    func.count(PropertyListing.id).label('count')
                ).filter(PropertyListing.timestamp >= since)
                
                if location:
                    query = query.filter(PropertyListing.location.contains(location))
                
                results = query.group_by(func.date(PropertyListing.timestamp)).all()
                
                return [
                    {
                        'date': str(result.date),
                        'avg_price': float(result.avg_price) if result.avg_price else 0.0,
                        'avg_price_per_m2': float(result.avg_price_per_m2) if result.avg_price_per_m2 else 0.0,
                        'count': result.count
                    }
                    for result in results
                ]
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting price trends: {e}")
            return [] 