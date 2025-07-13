"""
Tests for Scraper Modules

This module contains tests for all scraper functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from scraper.base_scraper import PropertyListing, BaseScraper
from scraper.batdongsan_scraper import BatDongSanScraper
from scraper.chotot_scraper import ChototScraper
from scraper.scraper_manager import ScraperManager


class TestPropertyListing:
    """Test PropertyListing dataclass"""
    
    def test_property_listing_creation(self):
        """Test creating a PropertyListing instance"""
        listing = PropertyListing(
            title="Test Property",
            location="Hanoi",
            price=1000000000,
            area=100.0,
            price_per_m2=10000000,
            image_url="https://example.com/image.jpg",
            link="https://example.com/property",
            property_type="Căn hộ",
            bedrooms=2,
            bathrooms=2,
            timestamp=datetime.now(),
            source="TestSource",
            raw_data={"test": "data"}
        )
        
        assert listing.title == "Test Property"
        assert listing.location == "Hanoi"
        assert listing.price == 1000000000
        assert listing.area == 100.0
        assert listing.price_per_m2 == 10000000
        assert listing.property_type == "Căn hộ"
        assert listing.bedrooms == 2
        assert listing.bathrooms == 2
        assert listing.source == "TestSource"


class TestBaseScraper:
    """Test BaseScraper functionality"""
    
    def test_base_scraper_initialization(self):
        """Test BaseScraper initialization"""
        scraper = BaseScraper("TestScraper", "https://example.com")
        
        assert scraper.name == "TestScraper"
        assert scraper.base_url == "https://example.com"
        assert scraper.delay_range == (2, 5)
        assert scraper.session is not None
    
    def test_clean_price(self):
        """Test price cleaning functionality"""
        scraper = BaseScraper("TestScraper", "https://example.com")
        
        # Test billion format
        assert scraper.clean_price("2.5 tỷ") == 2500000000
        assert scraper.clean_price("2.5 tỷ VND") == 2500000000
        
        # Test million format
        assert scraper.clean_price("500 triệu") == 500000000
        assert scraper.clean_price("500 triệu đồng") == 500000000
        
        # Test with commas
        assert scraper.clean_price("1,000,000,000") == 1000000000
        
        # Test invalid input
        assert scraper.clean_price("") == 0.0
        assert scraper.clean_price("invalid") == 0.0
    
    def test_clean_area(self):
        """Test area cleaning functionality"""
        scraper = BaseScraper("TestScraper", "https://example.com")
        
        # Test with m²
        assert scraper.clean_area("100m²") == 100.0
        assert scraper.clean_area("100 m²") == 100.0
        
        # Test with m2
        assert scraper.clean_area("150m2") == 150.0
        
        # Test with sqm
        assert scraper.clean_area("200sqm") == 200.0
        
        # Test with commas
        assert scraper.clean_area("1,000") == 1000.0
        
        # Test invalid input
        assert scraper.clean_area("") == 0.0
        assert scraper.clean_area("invalid") == 0.0
    
    def test_calculate_price_per_m2(self):
        """Test price per m² calculation"""
        scraper = BaseScraper("TestScraper", "https://example.com")
        
        # Normal calculation
        assert scraper.calculate_price_per_m2(1000000000, 100) == 10000000
        
        # Zero area
        assert scraper.calculate_price_per_m2(1000000000, 0) == 0.0
        
        # Zero price
        assert scraper.calculate_price_per_m2(0, 100) == 0.0


class TestBatDongSanScraper:
    """Test BatDongSan scraper"""
    
    def test_batdongsan_scraper_initialization(self):
        """Test BatDongSan scraper initialization"""
        scraper = BatDongSanScraper()
        
        assert scraper.name == "BatDongSan"
        assert scraper.base_url == "https://batdongsan.com.vn"
        assert scraper.delay_range == (3, 6)
        assert 'listing_container' in scraper.selectors
        assert 'title' in scraper.selectors
        assert 'price' in scraper.selectors
    
    @pytest.mark.asyncio
    async def test_batdongsan_scrape_listings_mock(self):
        """Test BatDongSan scraping with mocked Playwright"""
        scraper = BatDongSanScraper()
        
        # Mock Playwright
        mock_page = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright = AsyncMock()
        
        # Mock page responses
        mock_page.query_selector_all.return_value = []
        mock_page.query_selector.return_value = None
        mock_page.wait_for_selector.return_value = None
        mock_page.wait_for_load_state.return_value = None
        mock_page.goto.return_value = None
        mock_page.set_extra_http_headers.return_value = None
        
        mock_browser.new_page.return_value = mock_page
        mock_playwright.chromium.launch.return_value = mock_browser
        
        with patch('scraper.batdongsan_scraper.async_playwright') as mock_playwright_context:
            mock_playwright_context.return_value.__aenter__.return_value = mock_playwright
            
            listings = await scraper.scrape_listings(max_pages=1)
            
            assert isinstance(listings, list)
            assert len(listings) == 0  # No listings in mock


class TestChototScraper:
    """Test Chotot scraper"""
    
    def test_chotot_scraper_initialization(self):
        """Test Chotot scraper initialization"""
        scraper = ChototScraper()
        
        assert scraper.name == "Chotot"
        assert scraper.base_url == "https://chotot.com"
        assert scraper.delay_range == (2, 4)
        assert 'listing_container' in scraper.selectors
        assert 'title' in scraper.selectors
        assert 'price' in scraper.selectors
    
    @pytest.mark.asyncio
    async def test_chotot_scrape_listings_mock(self):
        """Test Chotot scraping with mocked Playwright"""
        scraper = ChototScraper()
        
        # Mock Playwright
        mock_page = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright = AsyncMock()
        
        # Mock page responses
        mock_page.query_selector_all.return_value = []
        mock_page.query_selector.return_value = None
        mock_page.wait_for_selector.return_value = None
        mock_page.wait_for_load_state.return_value = None
        mock_page.goto.return_value = None
        mock_page.set_extra_http_headers.return_value = None
        
        mock_browser.new_page.return_value = mock_page
        mock_playwright.chromium.launch.return_value = mock_browser
        
        with patch('scraper.chotot_scraper.async_playwright') as mock_playwright_context:
            mock_playwright_context.return_value.__aenter__.return_value = mock_playwright
            
            listings = await scraper.scrape_listings(max_pages=1)
            
            assert isinstance(listings, list)
            assert len(listings) == 0  # No listings in mock


class TestScraperManager:
    """Test ScraperManager functionality"""
    
    def test_scraper_manager_initialization(self):
        """Test ScraperManager initialization"""
        manager = ScraperManager()
        
        assert 'batdongsan' in manager.scrapers
        assert 'chotot' in manager.scrapers
        assert manager.scrape_interval_hours == 6
        assert not manager.is_running
        assert manager.stats['total_runs'] == 0
    
    @pytest.mark.asyncio
    async def test_run_all_scrapers_mock(self):
        """Test running all scrapers with mocked scrapers"""
        manager = ScraperManager()
        
        # Mock scrapers
        mock_batdongsan = Mock()
        mock_chotot = Mock()
        
        # Create sample listings
        sample_listing = PropertyListing(
            title="Test Property",
            location="Hanoi",
            price=1000000000,
            area=100.0,
            price_per_m2=10000000,
            image_url="https://example.com/image.jpg",
            link="https://example.com/property",
            property_type="Căn hộ",
            bedrooms=2,
            bathrooms=2,
            timestamp=datetime.now(),
            source="TestSource",
            raw_data={"test": "data"}
        )
        
        mock_batdongsan.run_scraper.return_value = [sample_listing]
        mock_chotot.run_scraper.return_value = [sample_listing]
        
        manager.scrapers['batdongsan'] = mock_batdongsan
        manager.scrapers['chotot'] = mock_chotot
        
        listings = await manager.run_all_scrapers(max_pages_per_site=1)
        
        assert len(listings) == 2  # One from each scraper
        assert manager.stats['total_runs'] == 1
        assert manager.stats['successful_runs'] == 2
    
    @pytest.mark.asyncio
    async def test_run_single_scraper(self):
        """Test running a single scraper"""
        manager = ScraperManager()
        
        # Mock scraper
        mock_scraper = Mock()
        sample_listing = PropertyListing(
            title="Test Property",
            location="Hanoi",
            price=1000000000,
            area=100.0,
            price_per_m2=10000000,
            image_url="https://example.com/image.jpg",
            link="https://example.com/property",
            property_type="Căn hộ",
            bedrooms=2,
            bathrooms=2,
            timestamp=datetime.now(),
            source="TestSource",
            raw_data={"test": "data"}
        )
        
        mock_scraper.run_scraper.return_value = [sample_listing]
        manager.scrapers['test'] = mock_scraper
        
        listings = await manager.run_single_scraper('test', max_pages=1)
        
        assert len(listings) == 1
        assert listings[0].title == "Test Property"
    
    def test_get_stats(self):
        """Test getting scraper statistics"""
        manager = ScraperManager()
        
        stats = manager.get_stats()
        
        assert 'total_runs' in stats
        assert 'successful_runs' in stats
        assert 'failed_runs' in stats
        assert 'total_listings' in stats
        assert 'last_run' in stats
        assert 'next_run' in stats
    
    def test_get_scraper_status(self):
        """Test getting scraper status"""
        manager = ScraperManager()
        
        status = manager.get_scraper_status()
        
        assert 'batdongsan' in status
        assert 'chotot' in status
        assert status['batdongsan']['name'] == 'BatDongSan'
        assert status['chotot']['name'] == 'Chotot'
    
    def test_add_remove_scraper(self):
        """Test adding and removing scrapers"""
        manager = ScraperManager()
        
        # Test adding scraper
        mock_scraper = Mock()
        mock_scraper.name = "TestScraper"
        mock_scraper.base_url = "https://test.com"
        mock_scraper.delay_range = (1, 3)
        
        manager.add_scraper('test', mock_scraper)
        assert 'test' in manager.scrapers
        
        # Test removing scraper
        manager.remove_scraper('test')
        assert 'test' not in manager.scrapers
    
    @pytest.mark.asyncio
    async def test_run_sample_scraping(self):
        """Test sample scraping functionality"""
        from scraper.scraper_manager import run_sample_scraping
        
        listings = await run_sample_scraping()
        
        assert isinstance(listings, list)
        assert len(listings) > 0
        
        # Check that listings have required fields
        for listing in listings:
            assert hasattr(listing, 'title')
            assert hasattr(listing, 'location')
            assert hasattr(listing, 'price')
            assert hasattr(listing, 'source')


# Integration tests
class TestScraperIntegration:
    """Integration tests for scraper components"""
    
    @pytest.mark.asyncio
    async def test_full_scraping_workflow(self):
        """Test complete scraping workflow"""
        manager = ScraperManager()
        
        # Mock the scrapers to return sample data
        sample_listing = PropertyListing(
            title="Integration Test Property",
            location="Ho Chi Minh City",
            price=2000000000,
            area=120.0,
            price_per_m2=16666666,
            image_url="https://example.com/integration.jpg",
            link="https://example.com/integration",
            property_type="Căn hộ",
            bedrooms=3,
            bathrooms=2,
            timestamp=datetime.now(),
            source="IntegrationTest",
            raw_data={"integration": "test"}
        )
        
        for scraper_name in manager.scrapers:
            manager.scrapers[scraper_name].run_scraper = AsyncMock(return_value=[sample_listing])
        
        # Run the scraping
        listings = await manager.run_all_scrapers(max_pages_per_site=1)
        
        # Verify results
        assert len(listings) == 2  # One from each scraper
        assert manager.stats['total_runs'] == 1
        assert manager.stats['successful_runs'] == 2
        assert manager.stats['total_listings'] == 2
        
        # Verify listing data
        for listing in listings:
            assert listing.title == "Integration Test Property"
            assert listing.location == "Ho Chi Minh City"
            assert listing.price == 2000000000
            assert listing.area == 120.0
            assert listing.property_type == "Căn hộ"


# Performance tests
class TestScraperPerformance:
    """Performance tests for scraper components"""
    
    @pytest.mark.asyncio
    async def test_scraping_performance(self):
        """Test scraping performance with multiple listings"""
        manager = ScraperManager()
        
        # Create many sample listings
        sample_listings = []
        for i in range(100):
            listing = PropertyListing(
                title=f"Performance Test Property {i}",
                location=f"District {i % 10}",
                price=1000000000 + (i * 10000000),
                area=50.0 + (i * 2),
                price_per_m2=20000000 + (i * 100000),
                image_url=f"https://example.com/performance_{i}.jpg",
                link=f"https://example.com/performance_{i}",
                property_type="Căn hộ",
                bedrooms=1 + (i % 4),
                bathrooms=1 + (i % 3),
                timestamp=datetime.now(),
                source="PerformanceTest",
                raw_data={"performance": "test", "index": i}
            )
            sample_listings.append(listing)
        
        # Mock scrapers to return many listings
        for scraper_name in manager.scrapers:
            manager.scrapers[scraper_name].run_scraper = AsyncMock(return_value=sample_listings)
        
        # Measure performance
        import time
        start_time = time.time()
        
        listings = await manager.run_all_scrapers(max_pages_per_site=1)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify results
        assert len(listings) == 200  # 100 from each scraper
        assert execution_time < 5.0  # Should complete within 5 seconds
        
        # Verify data integrity
        for i, listing in enumerate(listings):
            assert listing.title.startswith("Performance Test Property")
            assert listing.price > 0
            assert listing.area > 0
            assert listing.price_per_m2 > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 