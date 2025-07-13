"""
Scraper Manager

This module manages multiple scrapers and coordinates their execution.
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .base_scraper import PropertyListing
from .batdongsan_scraper import BatDongSanScraper
from .chotot_scraper import ChototScraper

logger = logging.getLogger(__name__)


class ScraperManager:
    """
    Manages multiple scrapers and coordinates their execution
    
    This class handles:
    - Running multiple scrapers concurrently
    - Scheduling regular scraping jobs
    - Error handling and retry logic
    - Data aggregation from multiple sources
    """
    
    def __init__(self, scrape_interval_hours: int = 6):
        """
        Initialize the scraper manager
        
        Args:
            scrape_interval_hours: Hours between scraping runs
        """
        self.scrapers = {
            'batdongsan': BatDongSanScraper(),
            'chotot': ChototScraper(),
        }
        
        self.scrape_interval_hours = scrape_interval_hours
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
        # Statistics
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'total_listings': 0,
            'last_run': None,
            'next_run': None,
        }
    
    async def run_all_scrapers(self, max_pages_per_site: int = 10) -> List[PropertyListing]:
        """
        Run all scrapers concurrently
        
        Args:
            max_pages_per_site: Maximum pages to scrape per site
            
        Returns:
            List[PropertyListing]: Combined results from all scrapers
        """
        logger.info("Starting all scrapers...")
        
        self.stats['total_runs'] += 1
        start_time = datetime.now()
        
        # Create tasks for all scrapers
        tasks = []
        for name, scraper in self.scrapers.items():
            task = asyncio.create_task(
                self._run_single_scraper(name, scraper, max_pages_per_site)
            )
            tasks.append(task)
        
        # Wait for all scrapers to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        all_listings = []
        for i, result in enumerate(results):
            scraper_name = list(self.scrapers.keys())[i]
            
            if isinstance(result, Exception):
                logger.error(f"Scraper {scraper_name} failed: {result}")
                self.stats['failed_runs'] += 1
            else:
                logger.info(f"Scraper {scraper_name} completed with {len(result)} listings")
                all_listings.extend(result)
                self.stats['successful_runs'] += 1
        
        # Update statistics
        self.stats['total_listings'] += len(all_listings)
        self.stats['last_run'] = datetime.now()
        duration = self.stats['last_run'] - start_time
        
        logger.info(f"All scrapers completed. Total listings: {len(all_listings)}")
        logger.info(f"Duration: {duration}")
        
        return all_listings
    
    async def _run_single_scraper(
        self, 
        name: str, 
        scraper: Any, 
        max_pages: int
    ) -> List[PropertyListing]:
        """
        Run a single scraper with error handling
        
        Args:
            name: Name of the scraper
            scraper: Scraper instance
            max_pages: Maximum pages to scrape
            
        Returns:
            List[PropertyListing]: Scraped listings
        """
        try:
            logger.info(f"Starting scraper: {name}")
            listings = await scraper.run_scraper(max_pages)
            logger.info(f"Scraper {name} completed successfully")
            return listings
            
        except Exception as e:
            logger.error(f"Scraper {name} failed: {e}")
            raise
    
    def start_scheduler(self):
        """Start the scheduler for automatic scraping"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Schedule scraping job
        self.scheduler.add_job(
            func=self._scheduled_scrape,
            trigger=IntervalTrigger(hours=self.scrape_interval_hours),
            id='scraping_job',
            name='Real Estate Scraping',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        self.is_running = True
        
        # Calculate next run time
        self.stats['next_run'] = datetime.now() + timedelta(hours=self.scrape_interval_hours)
        
        logger.info(f"Scheduler started. Next run in {self.scrape_interval_hours} hours")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Scheduler stopped")
    
    async def _scheduled_scrape(self):
        """Scheduled scraping job"""
        logger.info("Running scheduled scraping job")
        try:
            await self.run_all_scrapers()
            self.stats['next_run'] = datetime.now() + timedelta(hours=self.scrape_interval_hours)
        except Exception as e:
            logger.error(f"Scheduled scraping failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        return self.stats.copy()
    
    def get_scraper_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all scrapers"""
        status = {}
        for name, scraper in self.scrapers.items():
            status[name] = {
                'name': scraper.name,
                'base_url': scraper.base_url,
                'delay_range': scraper.delay_range,
                'is_active': True,  # Could be enhanced with health checks
            }
        return status
    
    async def run_single_scraper(self, scraper_name: str, max_pages: int = 10) -> List[PropertyListing]:
        """
        Run a single scraper by name
        
        Args:
            scraper_name: Name of the scraper to run
            max_pages: Maximum pages to scrape
            
        Returns:
            List[PropertyListing]: Scraped listings
        """
        if scraper_name not in self.scrapers:
            raise ValueError(f"Unknown scraper: {scraper_name}")
        
        scraper = self.scrapers[scraper_name]
        return await self._run_single_scraper(scraper_name, scraper, max_pages)
    
    def add_scraper(self, name: str, scraper: Any):
        """
        Add a new scraper to the manager
        
        Args:
            name: Name for the scraper
            scraper: Scraper instance
        """
        self.scrapers[name] = scraper
        logger.info(f"Added scraper: {name}")
    
    def remove_scraper(self, name: str):
        """
        Remove a scraper from the manager
        
        Args:
            name: Name of the scraper to remove
        """
        if name in self.scrapers:
            del self.scrapers[name]
            logger.info(f"Removed scraper: {name}")
        else:
            logger.warning(f"Scraper {name} not found")


# Utility functions for testing and development
async def run_sample_scraping():
    """Run sample scraping for testing"""
    manager = ScraperManager()
    
    # Run scrapers with sample data for testing
    logger.info("Running sample scraping...")
    
    # Simulate scraping results
    sample_listings = []
    
    # Add sample data from BatDongSan
    from .batdongsan_scraper import SAMPLE_BATDONGSAN_DATA
    from .base_scraper import PropertyListing
    
    for data in SAMPLE_BATDONGSAN_DATA:
        listing = PropertyListing(**data)
        sample_listings.append(listing)
    
    # Add sample data from Chotot
    from .chotot_scraper import SAMPLE_CHOTOT_DATA
    
    for data in SAMPLE_CHOTOT_DATA:
        listing = PropertyListing(**data)
        sample_listings.append(listing)
    
    logger.info(f"Sample scraping completed. Total listings: {len(sample_listings)}")
    return sample_listings


if __name__ == "__main__":
    # Example usage
    async def main():
        manager = ScraperManager()
        
        # Run all scrapers
        listings = await manager.run_all_scrapers(max_pages_per_site=2)
        
        # Print results
        for listing in listings[:5]:  # Show first 5 listings
            print(f"{listing.source}: {listing.title} - {listing.price:,.0f} VND")
    
    asyncio.run(main()) 