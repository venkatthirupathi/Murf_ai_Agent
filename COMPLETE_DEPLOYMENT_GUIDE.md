# Complete AI Voice Agent Deployment Guide

## Prerequisites
- Python 3.11+
- Docker (for container deployment)
- API Keys:
  - Murf.ai API Key
  - AssemblyAI API Key
  - Google Gemini API Key

## Step 1: Environment Setup

### Create Environment File
Create a `.env` file in the project root:

```bash
MURF_API_KEY=your_murf_api_key_here
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optional Configuration
PORT=8000
LOG_LEVEL=INFO
WORKERS=4
```

### Install Python Dependencies
```bash
pip install -r requirements.txt
```

## Step 2: Local Development Deployment

### Option A: Development Mode
```bash
python run_prod.py
```

### Option B: Production Mode with Gunicorn
```bash
pip install gunicorn
gunicorn app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --log-level info
```

## Step 3: Docker Deployment

### Build Docker Image
```bash
docker build -t murf-ai-app .
```

### Run Docker Container
```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name murf-ai-app \
  murf-ai-app
```

### Docker Compose (Recommended)
Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  murf-ai:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run with:
```bash
docker-compose up -d
```

## Step 4: Cloud Deployment Options

### Option A: AWS Elastic Beanstalk
1. Install EB CLI: `pip install awsebcli`
2. Initialize EB: `eb init`
3. Create environment: `eb create murf-ai-env`
4. Deploy: `eb deploy`

### Option B: Google Cloud Run
```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/your-project/murf-ai-app

# Deploy to Cloud Run
gcloud run deploy murf-ai-app \
  --image gcr.io/your-project/murf-ai-app \
  --platform managed \
  --region us-central1 \
  --set-env-vars MURF_API_KEY=$MURF_API_KEY \
  --set-env-vars ASSEMBLYAI_API_KEY=$ASSEMBLYAI_API_KEY \
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY \
  --allow-unauthenticated
```

### Option C: Heroku
```bash
# Create Heroku app
heroku create your-murf-ai-app

# Set environment variables
heroku config:set MURF_API_KEY=your_key
heroku config:set ASSEMBLYAI_API_KEY=your_key
heroku config:set GEMINI_API_KEY=your_key

# Deploy
git push heroku main
```

## Step 5: Production Configuration

### Nginx Configuration (for self-hosted)
Create `/etc/nginx/sites-available/murf-ai`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### Systemd Service (for self-hosted)
Create `/etc/systemd/system/murf-ai.service`:
```ini
[Unit]
Description=Murf AI Voice Agent
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/app
EnvironmentFile=/path/to/your/.env
ExecStart=/usr/local/bin/gunicorn app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --log-level info
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Step 6: SSL/HTTPS Configuration

### Let's Encrypt with Certbot
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal setup
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Step 7: Monitoring and Logging

### Health Checks
```bash
curl http://localhost:8000/health
curl http://localhost:8000/test-transcription
```

### Log Monitoring
```bash
# View logs
tail -f app.log

# Docker logs
docker logs murf-ai-app

# Systemd logs
journalctl -u murf-ai.service -f
```

## Step 8: Performance Optimization

### Database Setup (Optional)
For production, consider adding:
- Redis for session storage
- PostgreSQL for persistent data
- Message queue for background processing

### Scaling Configuration
```bash
# Increase workers based on CPU cores
WORKERS=$(nproc)
gunicorn app:app --workers $WORKERS --worker-class uvicorn.workers.UvicornWorker
```

## Step 9: Security Considerations

1. **API Key Security**: Never commit `.env` to version control
2. **HTTPS**: Always use HTTPS in production
3. **CORS**: Configure proper CORS for your domain
4. **Rate Limiting**: Implement rate limiting for API endpoints
5. **Authentication**: Add user authentication for production use

## Step 10: Backup and Recovery

### Regular Backups
```bash
# Backup environment variables
cp .env .env.backup.$(date +%Y%m%d)

# Backup uploads directory
tar -czf uploads-backup-$(date +%Y%m%d).tar.gz uploads/
```

### Disaster Recovery
1. Keep multiple copies of `.env` file
2. Regularly backup API keys
3. Monitor disk space for uploads directory
4. Implement logging and alerting

## Troubleshooting

### Common Issues
1. **API Key Errors**: Check all three API keys in `.env`
2. **WebSocket Issues**: Verify platform supports WebSockets
3. **Audio Playback**: Check browser console for CORS errors
4. **Memory Issues**: Monitor uploads directory size

### Health Check Endpoints
- `/health` - Application health
- `/test-transcription` - Service configuration check
- `/conversation/{session_id}` - Session history
- `/recorded-audio/{session_id}` - Audio files

## Deployment Verification

After deployment, test:
1. Open web interface: `http://your-domain.com:8000`
2. Test audio recording functionality
3. Verify WebSocket connections work
4. Check all three AI services are responding
5. Test the joke endpoint: `http://your-domain.com:8000/joke`

## Quick Start Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run development server
python run_prod.py
```

### Production Deployment
```bash
# Docker deployment
docker build -t murf-ai-app .
docker run -d -p 8000:8000 --env-file .env --name murf-ai-app murf-ai-app

# Or with Docker Compose
docker-compose up -d
```

## Support and Maintenance

- Monitor `app.log` for errors
- Regularly check API key quotas
- Clean up old audio files from uploads directory
- Keep dependencies updated with `pip install -U -r requirements.txt`

Your AI Voice Agent is now ready for production use!
