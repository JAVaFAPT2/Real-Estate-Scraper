/**
 * Real Estate Scraper - Frontend JavaScript
 * Handles all UI interactions and API calls
 */

// Global variables
let currentPage = 1;
let totalPages = 1;
let map = null;
let currentFilters = {};

// API base URL
const API_BASE = '/api';

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    loadStatistics();
    loadSampleData();
});

/**
 * Load and display statistics
 */
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE}/listings/statistics`);
        const stats = await response.json();
        
        // Update statistics cards
        document.getElementById('total-listings').textContent = formatNumber(stats.total_listings || 0);
        document.getElementById('avg-price').textContent = formatPrice(stats.average_price || 0);
        document.getElementById('recent-listings').textContent = formatNumber(stats.recent_listings_24h || 0);
        document.getElementById('total-users').textContent = formatNumber(stats.total_users || 0);
        
    } catch (error) {
        console.error('Error loading statistics:', error);
        // Load sample statistics for demo
        loadSampleStatistics();
    }
}

/**
 * Load sample statistics for demo purposes
 */
function loadSampleStatistics() {
    document.getElementById('total-listings').textContent = '1,247';
    document.getElementById('avg-price').textContent = '2.8B VND';
    document.getElementById('recent-listings').textContent = '23';
    document.getElementById('total-users').textContent = '156';
}

/**
 * Load sample data for demonstration
 */
function loadSampleData() {
    const sampleListings = [
        {
            id: 1,
            title: 'Căn hộ cao cấp tại Quận 1, TP.HCM',
            location: 'Quận 1, TP.HCM',
            price: 3200000000,
            area: 85,
            price_per_m2: 37647058,
            property_type: 'Căn hộ',
            bedrooms: 3,
            bathrooms: 2,
            image_url: 'https://via.placeholder.com/300x200/3498db/ffffff?text=Apartment',
            link: '#',
            source: 'BatDongSan',
            timestamp: '2024-01-15T10:30:00'
        },
        {
            id: 2,
            title: 'Nhà phố thương mại tại Quận 7, TP.HCM',
            location: 'Quận 7, TP.HCM',
            price: 12000000000,
            area: 200,
            price_per_m2: 60000000,
            property_type: 'Nhà phố',
            bedrooms: 5,
            bathrooms: 4,
            image_url: 'https://via.placeholder.com/300x200/e74c3c/ffffff?text=Townhouse',
            link: '#',
            source: 'Chotot',
            timestamp: '2024-01-15T09:15:00'
        },
        {
            id: 3,
            title: 'Căn hộ 2 phòng ngủ tại Quận 2, TP.HCM',
            location: 'Quận 2, TP.HCM',
            price: 2800000000,
            area: 75,
            price_per_m2: 37333333,
            property_type: 'Căn hộ',
            bedrooms: 2,
            bathrooms: 2,
            image_url: 'https://via.placeholder.com/300x200/27ae60/ffffff?text=Apartment',
            link: '#',
            source: 'BatDongSan',
            timestamp: '2024-01-15T08:45:00'
        }
    ];
    
    displayListings(sampleListings);
}

/**
 * Search properties based on current filters
 */
async function searchProperties() {
    // Show loading
    showLoading(true);
    
    // Build query parameters
    const params = new URLSearchParams();
    
    const filters = {
        location: document.getElementById('location').value,
        property_type: document.getElementById('property-type').value,
        bedrooms: document.getElementById('bedrooms').value,
        min_price: document.getElementById('min-price').value,
        max_price: document.getElementById('max-price').value,
        min_area: document.getElementById('min-area').value,
        max_area: document.getElementById('max-area').value,
        source: document.getElementById('source').value,
        limit: 20,
        offset: (currentPage - 1) * 20
    };
    
    // Add non-empty filters to query
    Object.entries(filters).forEach(([key, value]) => {
        if (value) {
            params.append(key, value);
        }
    });
    
    try {
        const response = await fetch(`${API_BASE}/listings?${params.toString()}`);
        const data = await response.json();
        
        if (data.listings) {
            displayListings(data.listings);
            currentFilters = filters;
        } else {
            // Fallback to sample data
            loadSampleData();
        }
        
    } catch (error) {
        console.error('Error searching properties:', error);
        // Show sample data on error
        loadSampleData();
    } finally {
        showLoading(false);
    }
}

/**
 * Display listings in the results container
 */
function displayListings(listings) {
    const resultsContainer = document.getElementById('results');
    
    if (!listings || listings.length === 0) {
        resultsContainer.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h4>No properties found</h4>
                <p class="text-muted">Try adjusting your search criteria</p>
            </div>
        `;
        return;
    }
    
    const listingsHTML = listings.map(listing => createListingCard(listing)).join('');
    
    resultsContainer.innerHTML = `
        <div class="row">
            ${listingsHTML}
        </div>
    `;
}

/**
 * Create HTML for a single listing card
 */
function createListingCard(listing) {
    const priceFormatted = formatPrice(listing.price);
    const pricePerM2Formatted = formatPrice(listing.price_per_m2);
    const dateFormatted = new Date(listing.timestamp).toLocaleDateString('vi-VN');
    
    return `
        <div class="col-lg-6 col-xl-4 mb-4">
            <div class="listing-card">
                <div class="listing-image" style="background-image: url('${listing.image_url}')">
                    <div class="alert-badge position-absolute top-0 end-0 m-2">
                        ${listing.source}
                    </div>
                </div>
                <div class="p-3">
                    <h5 class="listing-title mb-2">${listing.title}</h5>
                    <div class="listing-price mb-2">${priceFormatted}</div>
                    <div class="listing-location mb-2">
                        <i class="fas fa-map-marker-alt"></i> ${listing.location}
                    </div>
                    <div class="mb-2">
                        <span class="badge bg-primary me-2">${listing.property_type}</span>
                        <span class="badge bg-secondary me-2">${listing.area}m²</span>
                        ${listing.bedrooms ? `<span class="badge bg-info me-2">${listing.bedrooms} phòng ngủ</span>` : ''}
                        ${listing.bathrooms ? `<span class="badge bg-warning">${listing.bathrooms} phòng tắm</span>` : ''}
                    </div>
                    <div class="text-muted small mb-3">
                        <i class="fas fa-chart-line"></i> ${pricePerM2Formatted}/m²
                        <br>
                        <i class="fas fa-calendar"></i> ${dateFormatted}
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <a href="${listing.link}" target="_blank" class="btn btn-primary btn-sm">
                            <i class="fas fa-external-link-alt"></i> View Details
                        </a>
                        <button class="btn btn-outline-secondary btn-sm" onclick="saveToFavorites(${listing.id})">
                            <i class="fas fa-heart"></i> Save
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Export data in specified format
 */
async function exportData(format) {
    const params = new URLSearchParams();
    
    // Add current filters
    Object.entries(currentFilters).forEach(([key, value]) => {
        if (value) {
            params.append(key, value);
        }
    });
    
    params.append('format', format);
    
    try {
        const response = await fetch(`${API_BASE}/listings/export?${params.toString()}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `listings_${new Date().toISOString().split('T')[0]}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            alert('Export failed. Please try again.');
        }
    } catch (error) {
        console.error('Export error:', error);
        alert('Export failed. Please try again.');
    }
}

/**
 * Show map view
 */
function showMapView() {
    const mapView = document.getElementById('map-view');
    const searchView = document.getElementById('search');
    
    if (mapView.style.display === 'none') {
        searchView.style.display = 'none';
        mapView.style.display = 'block';
        initializeMap();
    } else {
        mapView.style.display = 'none';
        searchView.style.display = 'block';
    }
}

/**
 * Initialize Leaflet map
 */
function initializeMap() {
    if (map) {
        map.remove();
    }
    
    map = L.map('map').setView([10.8231, 106.6297], 10); // Ho Chi Minh City coordinates
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Add sample markers
    const sampleLocations = [
        { lat: 10.8231, lng: 106.6297, title: 'Quận 1, TP.HCM', price: '3.2B VND' },
        { lat: 10.7329, lng: 106.7295, title: 'Quận 7, TP.HCM', price: '12B VND' },
        { lat: 10.7873, lng: 106.7498, title: 'Quận 2, TP.HCM', price: '2.8B VND' }
    ];
    
    sampleLocations.forEach(location => {
        L.marker([location.lat, location.lng])
            .addTo(map)
            .bindPopup(`
                <strong>${location.title}</strong><br>
                Price: ${location.price}
            `);
    });
}

/**
 * Show alerts modal
 */
function showAlertsModal() {
    const modal = new bootstrap.Modal(document.getElementById('alertsModal'));
    modal.show();
}

/**
 * Create property alert
 */
async function createAlert() {
    const alertData = {
        user_email: document.getElementById('alert-email').value,
        name: document.getElementById('alert-name').value,
        location: document.getElementById('alert-location').value,
        property_type: document.getElementById('alert-property-type').value,
        bedrooms: document.getElementById('alert-bedrooms').value,
        min_price: document.getElementById('alert-min-price').value,
        max_price: document.getElementById('alert-max-price').value
    };
    
    try {
        const response = await fetch(`${API_BASE}/alerts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(alertData)
        });
        
        if (response.ok) {
            alert('Alert created successfully! You will receive email notifications for matching properties.');
            bootstrap.Modal.getInstance(document.getElementById('alertsModal')).hide();
        } else {
            alert('Failed to create alert. Please try again.');
        }
    } catch (error) {
        console.error('Error creating alert:', error);
        alert('Failed to create alert. Please try again.');
    }
}

/**
 * Clear all filters
 */
function clearFilters() {
    document.getElementById('location').value = '';
    document.getElementById('property-type').value = '';
    document.getElementById('bedrooms').value = '';
    document.getElementById('min-price').value = '';
    document.getElementById('max-price').value = '';
    document.getElementById('min-area').value = '';
    document.getElementById('max-area').value = '';
    document.getElementById('source').value = '';
    
    currentFilters = {};
    loadSampleData();
}

/**
 * Show/hide loading indicator
 */
function showLoading(show) {
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    
    if (show) {
        loading.style.display = 'block';
        results.style.display = 'none';
    } else {
        loading.style.display = 'none';
        results.style.display = 'block';
    }
}

/**
 * Scroll to search section
 */
function scrollToSearch() {
    document.getElementById('search').scrollIntoView({ behavior: 'smooth' });
}

/**
 * Save listing to favorites (placeholder)
 */
function saveToFavorites(listingId) {
    alert('Feature coming soon! This will save the property to your favorites.');
}

/**
 * Format price in Vietnamese currency
 */
function formatPrice(price) {
    if (!price) return '0 VND';
    
    if (price >= 1000000000) {
        return `${(price / 1000000000).toFixed(1)} tỷ VND`;
    } else if (price >= 1000000) {
        return `${(price / 1000000).toFixed(0)} triệu VND`;
    } else {
        return `${price.toLocaleString()} VND`;
    }
}

/**
 * Format number with commas
 */
function formatNumber(num) {
    return num.toLocaleString();
}

/**
 * Start scraping job
 */
async function startScraping() {
    try {
        const response = await fetch(`${API_BASE}/scraping/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                max_pages_per_site: 5,
                scrapers: ['batdongsan', 'chotot']
            })
        });
        
        if (response.ok) {
            alert('Scraping job started successfully!');
        } else {
            alert('Failed to start scraping job.');
        }
    } catch (error) {
        console.error('Error starting scraping:', error);
        alert('Failed to start scraping job.');
    }
}

/**
 * Get scraping status
 */
async function getScrapingStatus() {
    try {
        const response = await fetch(`${API_BASE}/scraping/status`);
        const status = await response.json();
        console.log('Scraping status:', status);
    } catch (error) {
        console.error('Error getting scraping status:', error);
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('location').focus();
    }
    
    // Enter to search
    if (e.key === 'Enter' && document.activeElement.id === 'location') {
        searchProperties();
    }
});

// Auto-search on filter change (debounced)
let searchTimeout;
function debouncedSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(searchProperties, 500);
}

// Add event listeners for auto-search
['location', 'property-type', 'bedrooms', 'source'].forEach(id => {
    document.getElementById(id).addEventListener('change', debouncedSearch);
});

['min-price', 'max-price', 'min-area', 'max-area'].forEach(id => {
    document.getElementById(id).addEventListener('input', debouncedSearch);
}); 