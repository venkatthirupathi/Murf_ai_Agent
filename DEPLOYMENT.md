# Deployment Guide - AI Voice Agent

## Production Deployment Options

### Option 1: Local Production Server
```bash
# Install dependencies
pip install -r requirements.txt

# Run production server
python run_prod.py
```

### Option 2: Docker Deployment
```bash
# Build Docker image
docker build -t murf-ai-app .

# Run container with environment variables
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name murf-ai-app \
  murf-ai-app
```

### Option 3: Gunicorn + Uvicorn (Recommended for Production)
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --log-level info
```

## Environment Variables

Create a `.env` file with:
```bash
MURF_API_KEY=your_murf_api_key_here
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here  
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
PORT=8000
LOG_LEVEL=INFO
WORKERS=4
```

## Performance Optimization

### WebSocket Considerations
- For WebSocket support, ensure your deployment platform supports WebSockets
- Consider using Redis for session storage in production
- Use a WebSocket-aware load balancer if scaling horizontally

### Memory Management
- Monitor memory usage, especially with audio file storage
- Consider implementing automatic cleanup of old audio files
- Use external storage for uploaded files in production

### Scaling
- Use multiple workers for CPU-bound operations
- Consider using a message queue for background processing
- Implement rate limiting for API endpoints

## Monitoring & Logging

The application includes:
- File logging to `app.log`
- Structured logging with timestamps
- Health check endpoint at `/health`
- Error handling with fallback mechanisms

## Troubleshooting

### Common Issues
1. **API Key Errors**: Check all three API keys are set correctly
2. **WebSocket Connection Issues**: Verify your deployment platform supports WebSockets
3. **Audio Playback Issues**: Check browser console for CORS or network errors
4. **Memory Issues**: Monitor uploads directory size and implement cleanup

### Health Check
```bash
curl http://localhost:8000/health
curl http://localhost:8000/test-transcription
```

## Security Considerations

- Keep API keys secure and never commit them to version control
- Use HTTPS in production for secure WebSocket connections
- Implement proper CORS configuration for your domain
- Consider adding authentication for production use
- Regularly rotate API keys

## Backup & Recovery

- Backup your `.env` file with API keys
- Consider database backup if using persistent storage
- Implement logging and monitoring for quick issue detection
