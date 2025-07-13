"""
Real Estate Scraper Package

This package contains modules for scraping real estate data from Vietnamese websites
in an ethical and respectful manner.
"""

__version__ = "1.0.0"
__author__ = "Real Estate Scraper Team"
__email__ = "contact@realestate-scraper.com"

from .base_scraper import BaseScraper
from .batdongsan_scraper import BatDongSanScraper
from .chotot_scraper import ChototScraper
from .scraper_manager import ScraperManager

__all__ = [
    'BaseScraper',
    'BatDongSanScraper', 
    'ChototScraper',
    'ScraperManager'
] 