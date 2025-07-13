"""
Base Scraper Class

This module provides the base class for all real estate scrapers,
defining the common interface and functionality.
"""

import asyncio
import logging
import time
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import requests
from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)


@dataclass
class PropertyListing:
    """Data class for property listing information"""
    title: str
    location: str
    price: float
    area: float
    price_per_m2: float
    image_url: Optional[str]
    link: str
    property_type: str
    bedrooms: Optional[int]
    bathrooms: Optional[int]
    timestamp: datetime
    source: str
    raw_data: Dict[str, Any]


class BaseScraper(ABC):
    """
    Base class for all real estate scrapers
    
    This class provides common functionality and defines the interface
    that all scrapers must implement.
    """
    
    def __init__(self, name: str, base_url: str, delay_range: tuple = (2, 5)):
        """
        Initialize the base scraper
        
        Args:
            name: Name of the scraper
            base_url: Base URL of the website
            delay_range: Range for random delays between requests (min, max)
        """
        self.name = name
        self.base_url = base_url
        self.delay_range = delay_range
        self.session = requests.Session()
        self.setup_session()
        
    def setup_session(self):
        """Setup the requests session with proper headers"""
        self.session.headers.update({
            'User-Agent': 'RealEstateScraper/1.0 (+https://github.com/real-estate-scraper)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    async def respectful_delay(self):
        """Implement respectful delay between requests"""
        delay = random.uniform(*self.delay_range)
        logger.info(f"Waiting {delay:.2f} seconds before next request")
        await asyncio.sleep(delay)
    
    async def check_robots_txt(self) -> bool:
        """
        Check robots.txt to ensure scraping is allowed
        
        Returns:
            bool: True if scraping is allowed, False otherwise
        """
        try:
            robots_url = f"{self.base_url}/robots.txt"
            response = self.session.get(robots_url, timeout=10)
            
            if response.status_code == 200:
                robots_content = response.text.lower()
                # Check if our user agent is disallowed
                if 'disallow: /' in robots_content:
                    logger.warning(f"Scraping disallowed by robots.txt for {self.name}")
                    return False
                logger.info(f"Robots.txt check passed for {self.name}")
                return True
            else:
                logger.warning(f"Could not fetch robots.txt for {self.name}")
                return True  # Assume allowed if we can't check
                
        except Exception as e:
            logger.error(f"Error checking robots.txt for {self.name}: {e}")
            return True  # Assume allowed if we can't check
    
    @abstractmethod
    async def scrape_listings(self, max_pages: int = 10) -> List[PropertyListing]:
        """
        Scrape property listings from the website
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List[PropertyListing]: List of scraped property listings
        """
        pass
    
    @abstractmethod
    def parse_listing(self, listing_element: Any) -> Optional[PropertyListing]:
        """
        Parse a single listing element into PropertyListing object
        
        Args:
            listing_element: Raw listing element from the page
            
        Returns:
            Optional[PropertyListing]: Parsed listing or None if parsing fails
        """
        pass
    
    def clean_price(self, price_text: str) -> float:
        """
        Clean and convert price text to float
        
        Args:
            price_text: Raw price text from the page
            
        Returns:
            float: Cleaned price value
        """
        if not price_text:
            return 0.0
            
        # Remove common price prefixes and suffixes
        price_text = price_text.lower().strip()
        price_text = price_text.replace('tỷ', '000000000')  # Billion
        price_text = price_text.replace('triệu', '000000')  # Million
        price_text = price_text.replace('vnđ', '').replace('vnd', '')
        price_text = price_text.replace('đồng', '')
        price_text = price_text.replace(',', '').replace('.', '')
        
        # Extract numeric values
        import re
        numbers = re.findall(r'\d+', price_text)
        if numbers:
            return float(''.join(numbers))
        return 0.0
    
    def clean_area(self, area_text: str) -> float:
        """
        Clean and convert area text to float (square meters)
        
        Args:
            area_text: Raw area text from the page
            
        Returns:
            float: Area in square meters
        """
        if not area_text:
            return 0.0
            
        area_text = area_text.lower().strip()
        area_text = area_text.replace('m²', '').replace('m2', '').replace('sqm', '')
        area_text = area_text.replace(',', '').replace('.', '')
        
        import re
        numbers = re.findall(r'\d+', area_text)
        if numbers:
            return float(''.join(numbers))
        return 0.0
    
    def calculate_price_per_m2(self, price: float, area: float) -> float:
        """
        Calculate price per square meter
        
        Args:
            price: Property price
            area: Property area in square meters
            
        Returns:
            float: Price per square meter
        """
        if area > 0:
            return price / area
        return 0.0
    
    async def run_scraper(self, max_pages: int = 10) -> List[PropertyListing]:
        """
        Main method to run the scraper with proper error handling
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List[PropertyListing]: List of scraped listings
        """
        logger.info(f"Starting scraper: {self.name}")
        
        # Check robots.txt first
        if not await self.check_robots_txt():
            logger.warning(f"Skipping {self.name} due to robots.txt restrictions")
            return []
        
        try:
            listings = await self.scrape_listings(max_pages)
            logger.info(f"Successfully scraped {len(listings)} listings from {self.name}")
            return listings
            
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {e}")
            return []
        
        finally:
            self.session.close() 