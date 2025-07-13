# Ethical Web Scraping Guidelines

## 🛡️ Core Principles

### 1. Respect robots.txt
- Always check and follow the robots.txt file of each target website
- Example: `https://batdongsan.com.vn/robots.txt`
- If scraping is disallowed, do not proceed

### 2. Rate Limiting
- Implement delays between requests (2-5 seconds minimum)
- Use exponential backoff for failed requests
- Respect server capacity and avoid overwhelming services

### 3. User-Agent Identification
- Use proper user-agent headers to identify your scraper
- Include contact information in user-agent when possible
- Example: `RealEstateScraper/1.0 (+https://github.com/your-repo)`

### 4. Data Privacy
- Only collect publicly available listing data
- Do not scrape personal information (phone numbers, emails, names)
- Respect privacy settings and opt-out mechanisms

### 5. Terms of Service Compliance
- Review and respect each website's terms of service
- Do not bypass authentication or access restrictions
- Use data only for intended purposes

## 📋 Implementation Guidelines

### Request Headers
```python
headers = {
    'User-Agent': 'RealEstateScraper/1.0 (+https://github.com/your-repo)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}
```

### Rate Limiting Implementation
```python
import time
import random

def respectful_request(url, delay_range=(2, 5)):
    """Make a request with random delay to be respectful"""
    time.sleep(random.uniform(*delay_range))
    # Make request here
```

### Error Handling
- Implement proper error handling for 429 (Too Many Requests)
- Use exponential backoff for retries
- Log all scraping activities for transparency

## 🚫 What NOT to Do

1. **Don't** scrape personal contact information
2. **Don't** bypass CAPTCHA or anti-bot measures
3. **Don't** make requests faster than human browsing
4. **Don't** ignore robots.txt directives
5. **Don't** use scraped data for spam or harassment
6. **Don't** violate terms of service agreements

## ✅ Best Practices

1. **Transparency**: Clearly identify your scraper
2. **Efficiency**: Only scrape what you need
3. **Respect**: Treat websites as you'd want yours treated
4. **Monitoring**: Keep logs of all scraping activities
5. **Compliance**: Regularly review and update practices

## 📞 Contact Information

If you receive a request to stop scraping:
- Immediately cease all scraping activities
- Respond professionally and promptly
- Remove any cached data if requested
- Update your practices to prevent future issues

## 🔄 Regular Review

This document should be reviewed monthly to ensure:
- Compliance with current laws and regulations
- Adherence to website policy changes
- Best practice updates
- Ethical considerations remain current 