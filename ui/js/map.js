/**
 * Map Integration for Real Estate Scraper
 * Uses Leaflet.js for interactive property mapping
 */

class PropertyMap {
    constructor(containerId = 'map') {
        this.containerId = containerId;
        this.map = null;
        this.markers = [];
        this.currentPopup = null;
        
        // Default center (Ho Chi Minh City)
        this.defaultCenter = [10.8231, 106.6297];
        this.defaultZoom = 10;
        
        // Location coordinates (hardcoded for MVP)
        this.locationCoords = {
            'Ho Chi Minh City': [10.8231, 106.6297],
            'Hanoi': [21.0285, 105.8542],
            'Da Nang': [16.0544, 108.2022],
            'Hai Phong': [20.8449, 106.6881],
            'Can Tho': [10.0452, 105.7469],
            'Bien Hoa': [10.9574, 106.8426],
            'Vung Tau': [10.3459, 107.0843],
            'Nha Trang': [12.2388, 109.1967],
            'Hue': [16.4637, 107.5909],
            'Buon Ma Thuot': [12.6667, 108.0500]
        };
        
        this.init();
    }
    
    init() {
        // Create map container if it doesn't exist
        this.createMapContainer();
        
        // Initialize Leaflet map
        this.map = L.map(this.containerId).setView(this.defaultCenter, this.defaultZoom);
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(this.map);
        
        // Add custom controls
        this.addControls();
        
        console.log('Property map initialized');
    }
    
    createMapContainer() {
        // Check if container exists
        let container = document.getElementById(this.containerId);
        if (!container) {
            container = document.createElement('div');
            container.id = this.containerId;
            container.style.height = '500px';
            container.style.width = '100%';
            container.style.borderRadius = '8px';
            container.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
            
            // Find a good place to insert the map
            const listingsContainer = document.querySelector('.listings-container') || 
                                    document.querySelector('#listings') ||
                                    document.body;
            listingsContainer.appendChild(container);
        }
    }
    
    addControls() {
        // Add fullscreen control
        L.control.fullscreen({
            position: 'topleft',
            title: {
                'false': 'View Fullscreen',
                'true': 'Exit Fullscreen'
            }
        }).addTo(this.map);
        
        // Add layer control for different property types
        this.addLayerControl();
    }
    
    addLayerControl() {
        this.propertyLayers = {
            'All Properties': L.layerGroup(),
            'Apartments': L.layerGroup(),
            'Houses': L.layerGroup(),
            'Villas': L.layerGroup(),
            'Land': L.layerGroup(),
            'Deals': L.layerGroup()
        };
        
        // Add layers to map
        Object.values(this.propertyLayers).forEach(layer => {
            layer.addTo(this.map);
        });
        
        // Add layer control
        L.control.layers(null, this.propertyLayers, {
            position: 'topright',
            collapsed: false
        }).addTo(this.map);
    }
    
    async loadListings(filters = {}) {
        try {
            // Build API URL with filters
            const params = new URLSearchParams();
            if (filters.location) params.append('location', filters.location);
            if (filters.min_price) params.append('min_price', filters.min_price);
            if (filters.max_price) params.append('max_price', filters.max_price);
            if (filters.property_type) params.append('property_type', filters.property_type);
            
            const response = await fetch(`/api/listings?${params.toString()}`);
            const data = await response.json();
            
            if (data.listings) {
                this.displayListings(data.listings);
            }
            
        } catch (error) {
            console.error('Error loading listings for map:', error);
            this.showError('Failed to load property data');
        }
    }
    
    displayListings(listings) {
        // Clear existing markers
        this.clearMarkers();
        
        if (!listings || listings.length === 0) {
            this.showMessage('No properties found in this area');
            return;
        }
        
        // Group listings by location for clustering
        const locationGroups = {};
        
        listings.forEach(listing => {
            const coords = this.getListingCoordinates(listing);
            if (coords) {
                if (!locationGroups[listing.location]) {
                    locationGroups[listing.location] = [];
                }
                locationGroups[listing.location].push(listing);
            }
        });
        
        // Create markers for each location
        Object.entries(locationGroups).forEach(([location, locationListings]) => {
            this.createLocationMarker(location, locationListings);
        });
        
        // Fit map to show all markers
        if (this.markers.length > 0) {
            const group = L.featureGroup(this.markers);
            this.map.fitBounds(group.getBounds().pad(0.1));
        }
        
        console.log(`Displayed ${listings.length} properties on map`);
    }
    
    getListingCoordinates(listing) {
        // Try to get coordinates from listing data
        if (listing.raw_data && typeof listing.raw_data === 'object') {
            if (listing.raw_data.lat && listing.raw_data.lng) {
                return [parseFloat(listing.raw_data.lat), parseFloat(listing.raw_data.lng)];
            }
        }
        
        // Fallback to hardcoded location coordinates
        const location = listing.location;
        if (this.locationCoords[location]) {
            return this.locationCoords[location];
        }
        
        // Try partial matches
        for (const [key, coords] of Object.entries(this.locationCoords)) {
            if (location.toLowerCase().includes(key.toLowerCase()) || 
                key.toLowerCase().includes(location.toLowerCase())) {
                return coords;
            }
        }
        
        return null;
    }
    
    createLocationMarker(location, listings) {
        const coords = this.getListingCoordinates(listings[0]);
        if (!coords) return;
        
        // Calculate average price for this location
        const avgPrice = listings.reduce((sum, listing) => sum + listing.price_per_m2, 0) / listings.length;
        const deals = listings.filter(listing => 
            listing.raw_data && listing.raw_data.is_deal
        );
        
        // Create marker with custom icon
        const marker = L.marker(coords, {
            icon: this.createCustomIcon(listings.length, deals.length > 0)
        });
        
        // Create popup content
        const popupContent = this.createPopupContent(location, listings, avgPrice);
        marker.bindPopup(popupContent, {
            maxWidth: 400,
            maxHeight: 300
        });
        
        // Add to appropriate layers
        this.propertyLayers['All Properties'].addLayer(marker);
        
        if (deals.length > 0) {
            this.propertyLayers['Deals'].addLayer(marker);
        }
        
        // Add to property type layers
        const propertyTypes = [...new Set(listings.map(l => l.property_type))];
        propertyTypes.forEach(type => {
            if (this.propertyLayers[type]) {
                this.propertyLayers[type].addLayer(marker);
            }
        });
        
        this.markers.push(marker);
    }
    
    createCustomIcon(count, isDeal) {
        const size = Math.min(30 + count * 2, 50);
        const color = isDeal ? '#ff4444' : '#3388ff';
        
        return L.divIcon({
            className: 'custom-marker',
            html: `<div style="
                background-color: ${color};
                color: white;
                border-radius: 50%;
                width: ${size}px;
                height: ${size}px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 12px;
                border: 2px solid white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            ">${count}</div>`,
            iconSize: [size, size],
            iconAnchor: [size/2, size/2]
        });
    }
    
    createPopupContent(location, listings, avgPrice) {
        const deals = listings.filter(l => l.raw_data && l.raw_data.is_deal);
        
        let content = `
            <div class="map-popup">
                <h4>${location}</h4>
                <p><strong>${listings.length}</strong> properties available</p>
                <p>Average price: <strong>${this.formatPrice(avgPrice)}/m²</strong></p>
        `;
        
        if (deals.length > 0) {
            content += `<p style="color: #ff4444;"><strong>🔥 ${deals.length} deals available!</strong></p>`;
        }
        
        content += `
                <div class="popup-listings">
                    <h5>Recent Listings:</h5>
                    <div class="listing-preview">
        `;
        
        // Show first 3 listings
        listings.slice(0, 3).forEach(listing => {
            const dealBadge = listing.raw_data && listing.raw_data.is_deal ? 
                '<span style="color: #ff4444; font-weight: bold;">DEAL</span> ' : '';
            
            content += `
                <div class="listing-item">
                    ${dealBadge}${listing.title}<br>
                    <small>${this.formatPrice(listing.price)} • ${listing.area}m²</small>
                </div>
            `;
        });
        
        if (listings.length > 3) {
            content += `<p><em>... and ${listings.length - 3} more</em></p>`;
        }
        
        content += `
                    </div>
                    <button onclick="window.location.href='/?location=${encodeURIComponent(location)}'" 
                            style="margin-top: 10px; padding: 5px 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        View All Properties
                    </button>
                </div>
            </div>
        `;
        
        return content;
    }
    
    formatPrice(price) {
        if (price >= 1000000000) {
            return `${(price / 1000000000).toFixed(1)}B VND`;
        } else if (price >= 1000000) {
            return `${(price / 1000000).toFixed(1)}M VND`;
        } else {
            return `${price.toLocaleString()} VND`;
        }
    }
    
    clearMarkers() {
        this.markers.forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.markers = [];
        
        // Clear all layer groups
        Object.values(this.propertyLayers).forEach(layer => {
            layer.clearLayers();
        });
    }
    
    showMessage(message) {
        // Remove existing message
        const existing = document.querySelector('.map-message');
        if (existing) existing.remove();
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'map-message';
        messageDiv.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 20px;
            border-radius: 8px;
            z-index: 1000;
        `;
        messageDiv.textContent = message;
        
        document.getElementById(this.containerId).appendChild(messageDiv);
        
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 3000);
    }
    
    showError(message) {
        this.showMessage(`Error: ${message}`);
    }
    
    // Public methods for external use
    refresh(filters = {}) {
        this.loadListings(filters);
    }
    
    focusOnLocation(location) {
        const coords = this.locationCoords[location];
        if (coords) {
            this.map.setView(coords, 12);
        }
    }
    
    toggleLayer(layerName) {
        if (this.propertyLayers[layerName]) {
            if (this.map.hasLayer(this.propertyLayers[layerName])) {
                this.map.removeLayer(this.propertyLayers[layerName]);
            } else {
                this.map.addLayer(this.propertyLayers[layerName]);
            }
        }
    }
}

// Initialize map when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Load Leaflet CSS if not already loaded
    if (!document.querySelector('link[href*="leaflet"]')) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
        document.head.appendChild(link);
    }
    
    // Load Leaflet JS if not already loaded
    if (typeof L === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
        script.onload = function() {
            // Initialize map after Leaflet is loaded
            window.propertyMap = new PropertyMap();
            window.propertyMap.loadListings();
        };
        document.head.appendChild(script);
    } else {
        // Leaflet already loaded
        window.propertyMap = new PropertyMap();
        window.propertyMap.loadListings();
    }
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PropertyMap;
}