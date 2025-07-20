
# Deployment Guide

author = "agent"
task = "shell.exec"

This guide covers deploying LLM-Lens on various platforms.

## 🚀 Local Deployment

### Quick Local Deploy

1. **Clone the Project**
   - git clone https://github.com/your-username/llm-lens.git
   - cd llm-lens

2. **Install Dependencies**
   - pip install fastapi uvicorn sqlalchemy httpx jinja2 python-multipart

3. **Run the Application**
   - python main.py
   - Access the dashboard at http://localhost:5000

### Environment Variables

Set environment variables in a `.env` file:

```env
DEFAULT_LLM_URL=http://your-llm-server:port/v1/chat/completions
DATABASE_URL=sqlite:///./llm_lens.db
```

### Database on Replit


### Custom Domain


## 🖥️ Local Development

### Development Server

For local development with hot reload:

```bash
# Clone the repository
git clone https://github.com/your-username/llm-lens.git
cd llm-lens

# Install dependencies
pip install fastapi uvicorn sqlalchemy httpx jinja2 python-multipart

# Run with auto-reload
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

### Development Environment

Set up environment variables:
```bash
export DEFAULT_LLM_URL=http://localhost:1234/v1/chat/completions
export DATABASE_URL=sqlite:///./llm_lens.db
export DEBUG=true
```

## 🐳 Docker Deployment

### Dockerfile

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml .
RUN pip install fastapi uvicorn sqlalchemy httpx jinja2 python-multipart

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 llmlens && chown -R llmlens:llmlens /app
USER llmlens

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  llm-lens:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DEFAULT_LLM_URL=http://host.docker.internal:1234/v1/chat/completions
      - DATABASE_URL=postgresql://llmlens:password@postgres:5432/llmlens
    depends_on:
      - postgres
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: llmlens
      POSTGRES_USER: llmlens
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

### Deploy with Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f llm-lens

# Stop
docker-compose down
```

## ☁️ Cloud Deployment

### Railway

1. **Connect Repository**
   - Go to Railway.app
   - Click "Deploy from GitHub repo"
   - Select your LLM-Lens fork

2. **Configure Environment**
   ```bash
   DEFAULT_LLM_URL=http://your-llm-server/v1/chat/completions
   DATABASE_URL=postgresql://postgres:password@railway-postgres:5432/railway
   ```

3. **Deploy**
   - Railway automatically detects Python and installs dependencies
   - App deploys on the provided domain

### Heroku

1. **Prepare for Heroku**
   Create `Procfile`:
   ```
   web: uvicorn main:app --host=0.0.0.0 --port=${PORT:-5000}
   ```

   Create `requirements.txt`:
   ```
   fastapi==0.116.1
   uvicorn==0.35.0
   sqlalchemy==2.0.41
   httpx==0.28.1
   jinja2==3.1.6
   python-multipart==0.0.20
   psycopg2-binary==2.9.10
   ```

2. **Deploy to Heroku**
   ```bash
   # Install Heroku CLI and login
   heroku login
   
   # Create app
   heroku create your-llm-lens-app
   
   # Add PostgreSQL
   heroku addons:create heroku-postgresql:hobby-dev
   
   # Set environment variables
   heroku config:set DEFAULT_LLM_URL=http://your-llm-server/v1/chat/completions
   
   # Deploy
   git push heroku main
   ```

### DigitalOcean App Platform

1. **Connect Repository**
   - Go to DigitalOcean App Platform
   - Create new app from GitHub

2. **Configure App**
   ```yaml
   name: llm-lens
   services:
   - name: web
     source_dir: /
     github:
       repo: your-username/llm-lens
       branch: main
     run_command: uvicorn main:app --host 0.0.0.0 --port 8080
     environment_slug: python
     instance_count: 1
     instance_size_slug: basic-xxs
     routes:
     - path: /
   databases:
   - name: llm-lens-db
     engine: PG
     version: "15"
   ```

### AWS EC2

1. **Launch EC2 Instance**
   - Choose Ubuntu 22.04 LTS
   - t3.micro for testing, t3.small+ for production
   - Configure security group for port 5000

2. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx
   pip3 install fastapi uvicorn sqlalchemy httpx jinja2 python-multipart
   ```

3. **Clone and Setup**
   ```bash
   git clone https://github.com/your-username/llm-lens.git
   cd llm-lens
   ```

4. **Create Service**
   Create `/etc/systemd/system/llm-lens.service`:
   ```ini
   [Unit]
   Description=LLM-Lens Server
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/llm-lens
   ExecStart=/home/ubuntu/.local/bin/uvicorn main:app --host 0.0.0.0 --port 5000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

5. **Start Service**
   ```bash
   sudo systemctl enable llm-lens
   sudo systemctl start llm-lens
   ```

6. **Configure Nginx**
   Create `/etc/nginx/sites-available/llm-lens`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   Enable site:
   ```bash
   sudo ln -s /etc/nginx/sites-available/llm-lens /etc/nginx/sites-enabled/
   sudo systemctl reload nginx
   ```

## 🔧 Production Configuration

### Environment Variables

Essential production environment variables:

```bash
# LLM Configuration
DEFAULT_LLM_URL=http://your-production-llm:port/v1/chat/completions

# Database (use PostgreSQL for production)
DATABASE_URL=postgresql://user:password@localhost:5432/llm_lens

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=your-sentry-dsn (optional)
```

### Database Setup

For PostgreSQL in production:

```sql
-- Create database
CREATE DATABASE llm_lens;

-- Create user
CREATE USER llmlens WITH PASSWORD 'secure-password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE llm_lens TO llmlens;
```

### Security Considerations

1. **Environment Variables**
   - Never commit secrets to version control
   - Use a secrets management service

2. **Database Security**
   - Use strong passwords
   - Encrypt connections
   - Regular backups

3. **Network Security**
   - Use HTTPS in production
   - Configure firewall rules
   - Consider VPN for LLM access

4. **Authentication**
   - Consider adding authentication for production
   - Implement rate limiting
   - Monitor for abuse

### Performance Optimization

1. **Application Level**
   ```python
   # In main.py, add these optimizations
   from fastapi import FastAPI
   from fastapi.middleware.gzip import GZipMiddleware
   
   app = FastAPI()
   app.add_middleware(GZipMiddleware, minimum_size=1000)
   ```

2. **Database Optimization**
   - Add indexes for frequently queried columns
   - Regular VACUUM for PostgreSQL
   - Connection pooling

3. **Caching**
   - Implement Redis for caching
   - Cache expensive analytics queries

### Monitoring & Logging

1. **Application Monitoring**
   ```python
   import logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

2. **Health Checks**
   Add health check endpoint:
   ```python
   @app.get("/health")
   async def health_check():
       return {"status": "healthy", "timestamp": datetime.utcnow()}
   ```

3. **Metrics**
   - Monitor response times
   - Track error rates
   - Monitor database performance

### Backup Strategy

1. **Database Backups**
   ```bash
   # Daily backup script
   pg_dump llm_lens > backup_$(date +%Y%m%d).sql
   ```

2. **Configuration Backups**
   - Backup environment variables
   - Document deployment procedures

### Scaling Considerations

1. **Horizontal Scaling**
   - Use load balancer
   - Scale application instances
   - Share database among instances

2. **Vertical Scaling**
   - Monitor CPU/memory usage
   - Upgrade instance sizes as needed

3. **Database Scaling**
   - Read replicas for analytics
   - Connection pooling
   - Consider database sharding for large scales

## 🔍 Deployment Verification

### Health Check Script

Create `health_check.py`:
```python
import requests
import sys

def check_health(base_url):
    try:
        # Check main endpoint
        response = requests.get(f"{base_url}/")
        assert response.status_code == 200
        
        # Check API endpoints
        response = requests.get(f"{base_url}/api/analytics/performance")
        assert response.status_code == 200
        
        print("✅ All health checks passed")
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    success = check_health(url)
    sys.exit(0 if success else 1)
```

### Deployment Checklist

- [ ] Environment variables configured
- [ ] Database initialized and accessible
- [ ] Application starts without errors
- [ ] Health check endpoint responds
- [ ] Dashboard loads correctly
- [ ] API endpoints functional
- [ ] Logs are being written
- [ ] SSL/TLS configured (production)
- [ ] Monitoring set up
- [ ] Backups configured

### Troubleshooting Deployment Issues

**Common Issues:**

1. **Port binding errors**
   ```
   Error: Address already in use
   ```
   Solution: Change port or stop conflicting service

2. **Database connection errors**
   ```
   Error: Connection refused
   ```
   Solution: Check database URL and credentials

3. **Module import errors**
   ```
   ModuleNotFoundError: No module named 'fastapi'
   ```
   Solution: Ensure all dependencies are installed

4. **Permission errors**
   ```
   PermissionError: [Errno 13] Permission denied
   ```
   Solution: Check file permissions and user privileges

For additional help with deployment issues, check the main troubleshooting guide in or create an issue on GitHub.
