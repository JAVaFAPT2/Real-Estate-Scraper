"""
BatDongSan Scraper

This module implements scraping functionality for batdongsan.com.vn
"""

import asyncio
import logging
from typing import List, Optional, Any
from datetime import datetime
from urllib.parse import urljoin
from playwright.async_api import async_playwright, Page

from .base_scraper import BaseScraper, PropertyListing

logger = logging.getLogger(__name__)


class BatDongSanScraper(BaseScraper):
    """
    Scraper for batdongsan.com.vn
    
    This scraper handles the specific structure and selectors
    used by the BatDongSan website.
    """
    
    def __init__(self):
        super().__init__(
            name="BatDongSan",
            base_url="https://batdongsan.com.vn",
            delay_range=(3, 6)  # Slightly longer delays for this site
        )
        
        # CSS selectors for BatDongSan
        self.selectors = {
            'listing_container': '.vip-item, .normal-item',
            'title': '.vip-item-title a, .normal-item-title a',
            'price': '.vip-item-price, .normal-item-price',
            'area': '.vip-item-area, .normal-item-area',
            'location': '.vip-item-location, .normal-item-location',
            'image': '.vip-item-image img, .normal-item-image img',
            'property_type': '.vip-item-type, .normal-item-type',
            'bedrooms': '.vip-item-bedroom, .normal-item-bedroom',
            'bathrooms': '.vip-item-bathroom, .normal-item-bathroom',
            'next_page': '.pagination .next a',
        }
    
    async def scrape_listings(self, max_pages: int = 10) -> List[PropertyListing]:
        """
        Scrape property listings from BatDongSan
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List[PropertyListing]: List of scraped property listings
        """
        listings = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set user agent
            await page.set_extra_http_headers({
                'User-Agent': 'RealEstateScraper/1.0 (+https://github.com/real-estate-scraper)'
            })
            
            try:
                # Start with the main listing page
                start_url = f"{self.base_url}/ban-nha-dat"
                await page.goto(start_url, wait_until='networkidle')
                await self.respectful_delay()
                
                page_num = 1
                while page_num <= max_pages:
                    logger.info(f"Scraping page {page_num} from BatDongSan")
                    
                    # Wait for listings to load
                    await page.wait_for_selector(self.selectors['listing_container'], timeout=10000)
                    
                    # Get all listing elements
                    listing_elements = await page.query_selector_all(self.selectors['listing_container'])
                    
                    # Parse each listing
                    for element in listing_elements:
                        try:
                            listing = await self.parse_listing_async(page, element)
                            if listing:
                                listings.append(listing)
                        except Exception as e:
                            logger.error(f"Error parsing listing: {e}")
                            continue
                    
                    # Check if there's a next page
                    next_button = await page.query_selector(self.selectors['next_page'])
                    if not next_button or page_num >= max_pages:
                        break
                    
                    # Go to next page
                    await next_button.click()
                    await page.wait_for_load_state('networkidle')
                    await self.respectful_delay()
                    page_num += 1
                    
            except Exception as e:
                logger.error(f"Error during BatDongSan scraping: {e}")
                
            finally:
                await browser.close()
        
        return listings
    
    async def parse_listing_async(self, page: Page, element: Any) -> Optional[PropertyListing]:
        """
        Parse a listing element asynchronously
        
        Args:
            page: Playwright page object
            element: Listing element
            
        Returns:
            Optional[PropertyListing]: Parsed listing or None
        """
        try:
            # Extract title and link
            title_element = await element.query_selector(self.selectors['title'])
            title = await title_element.text_content() if title_element else "No title"
            link = await title_element.get_attribute('href') if title_element else ""
            if link and not link.startswith('http'):
                link = urljoin(self.base_url, link)
            
            # Extract price
            price_element = await element.query_selector(self.selectors['price'])
            price_text = await price_element.text_content() if price_element else "0"
            price = self.clean_price(price_text)
            
            # Extract area
            area_element = await element.query_selector(self.selectors['area'])
            area_text = await area_element.text_content() if area_element else "0"
            area = self.clean_area(area_text)
            
            # Extract location
            location_element = await element.query_selector(self.selectors['location'])
            location = await location_element.text_content() if location_element else "Unknown"
            
            # Extract image
            image_element = await element.query_selector(self.selectors['image'])
            image_url = await image_element.get_attribute('src') if image_element else None
            if image_url and not image_url.startswith('http'):
                image_url = urljoin(self.base_url, image_url)
            
            # Extract property type
            type_element = await element.query_selector(self.selectors['property_type'])
            property_type = await type_element.text_content() if type_element else "Unknown"
            
            # Extract bedrooms (if available)
            bedroom_element = await element.query_selector(self.selectors['bedrooms'])
            bedrooms = None
            if bedroom_element:
                bedroom_text = await bedroom_element.text_content()
                if bedroom_text:
                    import re
                    numbers = re.findall(r'\d+', bedroom_text)
                    if numbers:
                        bedrooms = int(numbers[0])
            
            # Extract bathrooms (if available)
            bathroom_element = await element.query_selector(self.selectors['bathrooms'])
            bathrooms = None
            if bathroom_element:
                bathroom_text = await bathroom_element.text_content()
                if bathroom_text:
                    import re
                    numbers = re.findall(r'\d+', bathroom_text)
                    if numbers:
                        bathrooms = int(numbers[0])
            
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
                    'price_text': price_text,
                    'area_text': area_text,
                    'property_type': property_type,
                }
            )
            
            return listing
            
        except Exception as e:
            logger.error(f"Error parsing BatDongSan listing: {e}")
            return None
    
    def parse_listing(self, listing_element: Any) -> Optional[PropertyListing]:
        """
        Parse a single listing element (synchronous version for compatibility)
        
        Args:
            listing_element: Raw listing element from the page
            
        Returns:
            Optional[PropertyListing]: Parsed listing or None if parsing fails
        """
        # This method is kept for compatibility but the async version is preferred
        logger.warning("Using synchronous parse_listing - use parse_listing_async instead")
        return None


# Sample data for testing and development
SAMPLE_BATDONGSAN_DATA = [
    {
        "title": "Căn hộ 2 phòng ngủ tại Quận 1, TP.HCM",
        "location": "Quận 1, TP.HCM",
        "price": 2500000000,  # 2.5 billion VND
        "area": 65.0,  # 65 m²
        "price_per_m2": 38461538.46,
        "image_url": "https://example.com/image1.jpg",
        "link": "https://batdongsan.com.vn/ban-can-ho/can-ho-2-phong-ngu-quan-1",
        "property_type": "Căn hộ",
        "bedrooms": 2,
        "bathrooms": 2,
        "timestamp": datetime.now(),
        "source": "BatDongSan",
        "raw_data": {
            "price_text": "2.5 tỷ",
            "area_text": "65m²",
            "property_type": "Căn hộ"
        }
    },
    {
        "title": "Nhà riêng 3 tầng tại Quận 3, TP.HCM",
        "location": "Quận 3, TP.HCM", 
        "price": 8500000000,  # 8.5 billion VND
        "area": 120.0,  # 120 m²
        "price_per_m2": 70833333.33,
        "image_url": "https://example.com/image2.jpg",
        "link": "https://batdongsan.com.vn/ban-nha-rieng/nha-rieng-3-tang-quan-3",
        "property_type": "Nhà riêng",
        "bedrooms": 4,
        "bathrooms": 3,
        "timestamp": datetime.now(),
        "source": "BatDongSan",
        "raw_data": {
            "price_text": "8.5 tỷ",
            "area_text": "120m²",
            "property_type": "Nhà riêng"
        }
    }
] 