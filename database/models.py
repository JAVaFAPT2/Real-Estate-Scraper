"""
Database Models

This module defines the SQLAlchemy models for the real estate scraper.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

Base = declarative_base()


class PropertyListing(Base):
    """Database model for property listings"""
    
    __tablename__ = 'property_listings'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    location = Column(String(200), nullable=False)
    price = Column(Float, nullable=False)
    area = Column(Float, nullable=False)
    price_per_m2 = Column(Float, nullable=False)
    image_url = Column(String(500))
    link = Column(String(500), nullable=False)
    property_type = Column(String(100), nullable=False)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    source = Column(String(50), nullable=False)
    raw_data = Column(Text)  # JSON string for additional data
    
    def __repr__(self):
        return f"<PropertyListing(id={self.id}, title='{self.title}', price={self.price})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'location': self.location,
            'price': self.price,
            'area': self.area,
            'price_per_m2': self.price_per_m2,
            'image_url': self.image_url,
            'link': self.link,
            'property_type': self.property_type,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'source': self.source,
            'raw_data': json.loads(self.raw_data) if self.raw_data else {}
        }


class User(Base):
    """Database model for users"""
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(200), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    subscription_tier = Column(String(20), default='free')  # free, pro, enterprise
    subscription_expires = Column(DateTime)
    
    # Relationships
    alerts = relationship("Alert", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', tier='{self.subscription_tier}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'subscription_tier': self.subscription_tier,
            'subscription_expires': self.subscription_expires.isoformat() if self.subscription_expires else None
        }


class Alert(Base):
    """Database model for user alerts"""
    
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    location = Column(String(200))
    min_price = Column(Float)
    max_price = Column(Float)
    min_area = Column(Float)
    max_area = Column(Float)
    property_type = Column(String(100))
    bedrooms = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_triggered = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, name='{self.name}', user_id={self.user_id})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'location': self.location,
            'min_price': self.min_price,
            'max_price': self.max_price,
            'min_area': self.min_area,
            'max_area': self.max_area,
            'property_type': self.property_type,
            'bedrooms': self.bedrooms,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None
        }


class ScrapingLog(Base):
    """Database model for scraping logs"""
    
    __tablename__ = 'scraping_logs'
    
    id = Column(Integer, primary_key=True)
    scraper_name = Column(String(50), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime)
    listings_found = Column(Integer, default=0)
    listings_new = Column(Integer, default=0)
    status = Column(String(20), default='running')  # running, completed, failed
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<ScrapingLog(id={self.id}, scraper='{self.scraper_name}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'scraper_name': self.scraper_name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'listings_found': self.listings_found,
            'listings_new': self.listings_new,
            'status': self.status,
            'error_message': self.error_message
        }


# Export all models
__all__ = ['PropertyListing', 'User', 'Alert', 'ScrapingLog', 'Base'] 