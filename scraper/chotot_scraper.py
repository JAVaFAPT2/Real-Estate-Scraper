"""
Chotot Scraper

This module implements scraping functionality for chotot.com using their API
"""

import asyncio
import logging
import requests
import json
from typing import List, Optional, Any, Dict
from datetime import datetime
from urllib.parse import urljoin

from .base_scraper import BaseScraper, PropertyListing

logger = logging.getLogger(__name__)


class ChototScraper(BaseScraper):
    """
    Scraper for chotot.com using their API
    
    This scraper uses the internal API endpoint to fetch property listings
    instead of browser automation for better performance and reliability.
    """
    
    def __init__(self):
        super().__init__(
            name="Chotot",
            base_url="https://chotot.com",
            delay_range=(1, 2)  # Faster requests since we're using API
        )
        
        # API endpoint and parameters
        self.api_url = "https://gateway.chotot.com/v1/public/ad-listing"
        self.headers = {
            'User-Agent': 'RealEstateScraper/1.0 (+https://github.com/real-estate-scraper)',
            'Accept': 'application/json',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Referer': 'https://chotot.com/',
            'Origin': 'https://chotot.com'
        }
        
        # Default API parameters
        self.default_params = {
            'cg': 1000,  # Real estate category
            'limit': 20,  # Items per page
            'page': 1
        }
    
    async def scrape_listings(self, max_pages: int = 10) -> List[PropertyListing]:
        """
        Scrape property listings from Chotot API
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List[PropertyListing]: List of scraped property listings
        """
        listings = []
        
        try:
            page_num = 1
            while page_num <= max_pages:
                logger.info(f"Scraping page {page_num} from Chotot API")
                
                # Prepare API parameters
                params = self.default_params.copy()
                params['page'] = page_num
                
                # Make API request
                response = await self._make_api_request(params)
                
                if not response or 'ads' not in response:
                    logger.warning(f"No valid response from API on page {page_num}")
                    break
                
                ads = response.get('ads', [])
                if not ads:
                    logger.info(f"No more listings found on page {page_num}")
                    break
                
                # Parse each listing
                for ad in ads:
                    try:
                        listing = self._parse_api_listing(ad)
                        if listing:
                            listings.append(listing)
                    except Exception as e:
                        logger.error(f"Error parsing listing: {e}")
                        continue
                
                # Check if we should continue to next page
                total = response.get('total', 0)
                current_count = page_num * params['limit']
                
                if current_count >= total or page_num >= max_pages:
                    break
                
                page_num += 1
                await self.respectful_delay()
                
        except Exception as e:
            logger.error(f"Error during Chotot API scraping: {e}")
        
        return listings
    
    async def _make_api_request(self, params: Dict[str, Any]) -> Optional[Dict]:
        """
        Make API request to Chotot
        
        Args:
            params: Query parameters for the API
            
        Returns:
            Optional[Dict]: API response or None if failed
        """
        try:
            # Use asyncio to run the synchronous requests in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.get(
                    self.api_url, 
                    params=params, 
                    headers=self.headers, 
                    timeout=30
                )
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API request failed with status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error making API request: {e}")
            return None
    
    def _parse_api_listing(self, ad: Dict[str, Any]) -> Optional[PropertyListing]:
        """
        Parse a listing from the API response
        
        Args:
            ad: Raw ad data from API
            
        Returns:
            Optional[PropertyListing]: Parsed listing or None
        """
        try:
            # Extract basic information
            title = ad.get('subject', 'No title')
            price = ad.get('price', 0)
            area = ad.get('size', 0)  # size field contains area in m²
            location = self._extract_location(ad)
            image_url = ad.get('image')
            property_type = ad.get('category_name', 'Unknown')
            
            # Extract bedrooms and bathrooms
            bedrooms = ad.get('rooms')
            bathrooms = ad.get('toilets')
            
            # Create listing URL
            ad_id = ad.get('ad_id')
            link = f"{self.base_url}/mua-ban-nha-dat/{ad_id}" if ad_id else ""
            
            # Calculate price per m²
            price_per_m2 = self.calculate_price_per_m2(price, area)
            
            # Create PropertyListing object
            listing = PropertyListing(
                title=title.strip(),
                location=location.strip(),
                price=price,
                area=area,
                price_per_m2=price_per_m2,
                image_url=image_url,
                link=link,
                property_type=property_type.strip(),
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                timestamp=datetime.now(),
                source=self.name,
                raw_data={
                    'ad_id': ad_id,
                    'category': ad.get('category'),
                    'region_v2': ad.get('region_v2'),
                    'area_v2': ad.get('area_v2'),
                    'price_string': ad.get('price_string'),
                    'date': ad.get('date'),
                    'account_name': ad.get('account_name'),
                    'full_name': ad.get('full_name'),
                    'street_name': ad.get('street_name'),
                    'ward_name': ad.get('ward_name'),
                    'area_name': ad.get('area_name'),
                    'region_name': ad.get('region_name'),
                    'latitude': ad.get('latitude'),
                    'longitude': ad.get('longitude'),
                    'property_legal_document': ad.get('property_legal_document'),
                    'furnishing_sell': ad.get('furnishing_sell'),
                    'furnishing_rent': ad.get('furnishing_rent'),
                    'house_type': ad.get('house_type'),
                    'apartment_type': ad.get('apartment_type'),
                    'floors': ad.get('floors'),
                    'width': ad.get('width'),
                    'length': ad.get('length'),
                    'living_size': ad.get('living_size'),
                    'deposit': ad.get('deposit'),
                    'price_million_per_m2': ad.get('price_million_per_m2'),
                    'has_video': ad.get('has_video'),
                    'number_of_images': ad.get('number_of_images'),
                    'images': ad.get('images', []),
                    'videos': ad.get('videos', []),
                    'seller_info': ad.get('seller_info', {}),
                }
            )
            
            return listing
            
        except Exception as e:
            logger.error(f"Error parsing Chotot API listing: {e}")
            return None
    
    def _extract_location(self, ad: Dict[str, Any]) -> str:
        """
        Extract location information from ad data
        
        Args:
            ad: Raw ad data from API
            
        Returns:
            str: Formatted location string
        """
        location_parts = []
        
        # Add street name if available
        street_name = ad.get('street_name')
        if street_name:
            location_parts.append(street_name)
        
        # Add ward name if available
        ward_name = ad.get('ward_name')
        if ward_name:
            location_parts.append(ward_name)
        
        # Add area name if available
        area_name = ad.get('area_name')
        if area_name:
            location_parts.append(area_name)
        
        # Add region name if available
        region_name = ad.get('region_name')
        if region_name:
            location_parts.append(region_name)
        
        if location_parts:
            return ', '.join(location_parts)
        else:
            return "Unknown"
    
    def parse_listing(self, listing_element: Any) -> Optional[PropertyListing]:
        """
        Parse a single listing element (kept for compatibility)
        
        Args:
            listing_element: Raw listing element (not used in API version)
            
        Returns:
            Optional[PropertyListing]: Parsed listing or None if parsing fails
        """
        logger.warning("parse_listing method is deprecated - use API methods instead")
        return None


# Sample data for testing and development
SAMPLE_CHOTOT_DATA = [
    {
        "title": "Căn hộ cao cấp tại Quận 2, TP.HCM",
        "location": "Quận 2, TP.HCM",
        "price": 3200000000,  # 3.2 billion VND
        "area": 85.0,  # 85 m²
        "price_per_m2": 37647058.82,
        "image_url": "https://example.com/chotot-image1.jpg",
        "link": "https://chotot.com/mua-ban-nha-dat/can-ho-cao-cap-quan-2",
        "property_type": "Căn hộ",
        "bedrooms": 3,
        "bathrooms": 2,
        "timestamp": datetime.now(),
        "source": "Chotot",
        "raw_data": {
            "price_text": "3.2 tỷ",
            "area_text": "85m²",
            "property_type": "Căn hộ"
        }
    },
    {
        "title": "Nhà phố thương mại tại Quận 7, TP.HCM",
        "location": "Quận 7, TP.HCM",
        "price": 12000000000,  # 12 billion VND
        "area": 200.0,  # 200 m²
        "price_per_m2": 60000000.0,
        "image_url": "https://example.com/chotot-image2.jpg",
        "link": "https://chotot.com/mua-ban-nha-dat/nha-pho-thuong-mai-quan-7",
        "property_type": "Nhà phố",
        "bedrooms": 5,
        "bathrooms": 4,
        "timestamp": datetime.now(),
        "source": "Chotot",
        "raw_data": {
            "price_text": "12 tỷ",
            "area_text": "200m²",
            "property_type": "Nhà phố"
        }
    }
] 