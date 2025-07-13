# Deployment Guide

This guide covers deploying the Real Estate Scraper application to various platforms.

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd real-estate-scraper
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

5. **Setup environment**
   ```bash
   cp config.env.example .env
   # Edit .env with your configuration
   ```

6. **Run database migrations**
   ```bash
   python app.py --migrate
   ```

7. **Start the application**
   ```bash
   python app.py --debug
   ```

8. **Access the application**
   - Web UI: http://localhost:5000
   - API: http://localhost:5000/api
   - Health check: http://localhost:5000/health

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf libxss1 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["python", "app.py", "--host", "0.0.0.0", "--port", "5000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  real-estate-scraper:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=sqlite:///realestate.db
      - SECRET_KEY=your-secret-key-here
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    
  # Optional: Add PostgreSQL for production
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: realestate
      POSTGRES_USER: scraper
      POSTGRES_PASSWORD: your-password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Build and Run with Docker

```bash
# Build the image
docker build -t real-estate-scraper .

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f real-estate-scraper
```

## ☁️ Cloud Deployment

### Heroku

1. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```

2. **Add buildpacks**
   ```bash
   heroku buildpacks:add heroku/python
   heroku buildpacks:add https://github.com/heroku/heroku-buildpack-google-chrome
   ```

3. **Set environment variables**
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set DATABASE_URL=postgresql://...
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

### AWS (EC2 + RDS)

1. **Launch EC2 instance**
   ```bash
   # Use Ubuntu 22.04 LTS
   # Instance type: t3.medium or larger
   # Security group: Allow ports 22, 80, 443, 5000
   ```

2. **Install dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx
   ```

3. **Setup application**
   ```bash
   git clone <repository-url>
   cd real-estate-scraper
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

4. **Setup systemd service**
   ```bash
   sudo nano /etc/systemd/system/real-estate-scraper.service
   ```

   ```ini
   [Unit]
   Description=Real Estate Scraper
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/real-estate-scraper
   Environment=PATH=/home/ubuntu/real-estate-scraper/venv/bin
   ExecStart=/home/ubuntu/real-estate-scraper/venv/bin/python app.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

5. **Start service**
   ```bash
   sudo systemctl enable real-estate-scraper
   sudo systemctl start real-estate-scraper
   ```

6. **Setup Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/real-estate-scraper
   ```

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

   ```bash
   sudo ln -s /etc/nginx/sites-available/real-estate-scraper /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### Google Cloud Platform (GCP)

1. **Create Compute Engine instance**
   ```bash
   gcloud compute instances create real-estate-scraper \
     --zone=us-central1-a \
     --machine-type=e2-medium \
     --image-family=ubuntu-2204-lts \
     --image-project=ubuntu-os-cloud
   ```

2. **Setup application (similar to AWS)**
   ```bash
   # SSH into instance and follow AWS setup steps
   gcloud compute ssh real-estate-scraper --zone=us-central1-a
   ```

3. **Setup load balancer (optional)**
   ```bash
   # Create load balancer for high availability
   gcloud compute http-health-checks create real-estate-scraper-health \
     --port=5000 \
     --request-path=/health
   ```

### Azure

1. **Create Azure VM**
   ```bash
   az vm create \
     --resource-group myResourceGroup \
     --name real-estate-scraper \
     --image Ubuntu2204 \
     --size Standard_B2s \
     --admin-username azureuser
   ```

2. **Setup application (similar to AWS/GCP)**
   ```bash
   # SSH into VM and follow setup steps
   az vm open-port --resource-group myResourceGroup --name real-estate-scraper --port 5000
   ```

## 🔧 Production Configuration

### Environment Variables

```bash
# Required
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key
DATABASE_URL=postgresql://user:password@host:port/database

# Optional
API_RATE_LIMIT=100
API_RATE_LIMIT_WINDOW=3600
SCRAPING_DELAY=3
MAX_PAGES_PER_SITE=10

# Email (for alerts)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_FROM=alerts@yourdomain.com
```

### Database Setup

#### PostgreSQL (Recommended for Production)

1. **Install PostgreSQL**
   ```bash
   sudo apt install postgresql postgresql-contrib
   ```

2. **Create database and user**
   ```sql
   CREATE DATABASE realestate;
   CREATE USER scraper WITH PASSWORD 'your-password';
   GRANT ALL PRIVILEGES ON DATABASE realestate TO scraper;
   ```

3. **Update DATABASE_URL**
   ```bash
   DATABASE_URL=postgresql://scraper:your-password@localhost:5432/realestate
   ```

#### SQLite (Development/Testing)

```bash
DATABASE_URL=sqlite:///realestate.db
```

### SSL/HTTPS Setup

#### Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Nginx SSL Configuration

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## 📊 Monitoring and Logging

### Application Monitoring

1. **Setup logging**
   ```python
   # Already configured in app.py
   # Logs are written to logs/app.log
   ```

2. **Monitor application health**
   ```bash
   # Check health endpoint
   curl http://your-domain.com/health
   
   # Check service status
   sudo systemctl status real-estate-scraper
   ```

3. **Setup monitoring with Prometheus/Grafana**
   ```yaml
   # prometheus.yml
   global:
     scrape_interval: 15s
   
   scrape_configs:
     - job_name: 'real-estate-scraper'
       static_configs:
         - targets: ['localhost:5000']
   ```

### Database Monitoring

```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('realestate'));

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      - name: Run tests
        run: |
          pytest tests/ -v

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.KEY }}
          script: |
            cd /path/to/real-estate-scraper
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            python app.py --migrate
            sudo systemctl restart real-estate-scraper
```

## 🚨 Troubleshooting

### Common Issues

1. **Playwright browser not found**
   ```bash
   playwright install chromium
   ```

2. **Database connection issues**
   ```bash
   # Check database URL
   echo $DATABASE_URL
   
   # Test connection
   python -c "from database.database_manager import DatabaseManager; db = DatabaseManager(); print('Connected')"
   ```

3. **Permission denied errors**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER /path/to/real-estate-scraper
   chmod +x app.py
   ```

4. **Port already in use**
   ```bash
   # Find process using port 5000
   sudo lsof -i :5000
   
   # Kill process
   sudo kill -9 <PID>
   ```

### Performance Optimization

1. **Database indexing**
   ```sql
   -- Already included in migrations
   CREATE INDEX idx_listings_location ON property_listings(location);
   CREATE INDEX idx_listings_price ON property_listings(price);
   CREATE INDEX idx_listings_timestamp ON property_listings(timestamp);
   ```

2. **Caching with Redis**
   ```python
   # Add to requirements.txt
   redis==4.5.4
   
   # Setup Redis caching in app.py
   import redis
   cache = redis.Redis(host='localhost', port=6379, db=0)
   ```

3. **Load balancing**
   ```nginx
   upstream real_estate_scraper {
       server 127.0.0.1:5000;
       server 127.0.0.1:5001;
       server 127.0.0.1:5002;
   }
   ```

## 📈 Scaling

### Horizontal Scaling

1. **Multiple instances behind load balancer**
2. **Database read replicas**
3. **Redis for session storage**
4. **CDN for static assets**

### Vertical Scaling

1. **Increase server resources**
2. **Database optimization**
3. **Application profiling**

## 🔒 Security

### Security Checklist

- [ ] Use HTTPS in production
- [ ] Set secure SECRET_KEY
- [ ] Configure firewall rules
- [ ] Regular security updates
- [ ] Database backups
- [ ] Rate limiting enabled
- [ ] Input validation
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CSRF protection

### Security Headers

```python
# Add to Flask app
from flask_talisman import Talisman

Talisman(app, 
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'",
    }
)
```

## 📞 Support

For deployment issues:

1. Check the logs: `tail -f logs/app.log`
2. Verify environment variables
3. Test database connectivity
4. Check service status
5. Review error messages

Contact: support@realestate-scraper.com 