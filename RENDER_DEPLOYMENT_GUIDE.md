# Render Deployment Guide - AI Voice Agent

## Step-by-Step Deployment on Render.com

### Prerequisites
- GitHub account with your AI Voice Agent code
- Render.com account
- API Keys:
  - Murf.ai API Key
  - AssemblyAI API Key
  - Google Gemini API Key

## Step 1: Prepare Your Repository

### 1.1 Ensure Proper File Structure
Your repository should include:
- `app.py` (main FastAPI application)
- `requirements.txt` (Python dependencies)
- `Dockerfile` (for container deployment)
- `.env.example` (template for environment variables)

### 1.2 Create render.yaml (Optional but Recommended)
Create `render.yaml` in your repository root:

```yaml
services:
  - type: web
    name: murf-ai-app
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
    envVars:
      - key: MURF_API_KEY
        fromSecret: MURF_API_KEY
      - key: ASSEMBLYAI_API_KEY
        fromSecret: ASSEMBLYAI_API_KEY
      - key: GEMINI_API_KEY
        fromSecret: GEMINI_API_KEY
      - key: PORT
        value: 8000
```

## Step 2: Deploy on Render.com

### 2.1 Connect Your GitHub Repository
1. Go to [render.com](https://render.com)
2. Sign up or log in to your account
3. Click "New +" → "Web Service"
4. Connect your GitHub account and select your repository

### 2.2 Configure Web Service
- **Name**: `murf-ai-app` (or your preferred name)
- **Environment**: `Python`
- **Region**: Choose closest to your users (e.g., US East)
- **Branch**: `main` (or your deployment branch)
- **Root Directory**: `/` (if your files are in root)

### 2.3 Build & Start Commands
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

### 2.4 Environment Variables
Add these environment variables in Render dashboard:

| Key | Value | Secret |
|-----|-------|--------|
| MURF_API_KEY | Your Murf API Key | ✅ Yes |
| ASSEMBLYAI_API_KEY | Your AssemblyAI API Key | ✅ Yes |
| GEMINI_API_KEY | Your Gemini API Key | ✅ Yes |
| PORT | 8000 | ❌ No |

### 2.5 Advanced Settings
- **Plan**: Free (Starter) or Paid (for better performance)
- **Auto-Deploy**: Enable for automatic deployments on git push
- **Pull Request Previews**: Enable if desired

## Step 3: Alternative Docker Deployment on Render

### 3.1 Using Dockerfile
If you prefer Docker deployment:

1. **Build Command**: Leave empty (Render will use Dockerfile)
2. **Start Command**: Leave empty (Render will use Dockerfile CMD)

### 3.2 Dockerfile Requirements
Ensure your Dockerfile is properly configured:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "app:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

## Step 4: Post-Deployment Configuration

### 4.1 Custom Domain (Optional)
1. Go to your service in Render dashboard
2. Click "Settings" → "Custom Domains"
3. Add your domain and follow DNS instructions

### 4.2 Environment-Specific Config
For production vs staging:
- Create separate services for different environments
- Use different environment variable sets
- Consider using Render's Blueprint for multi-service setup

## Step 5: Verify Deployment

### 5.1 Health Check
```bash
curl https://your-render-url.onrender.com/health
# Should return: {"status":"healthy","message":"AI Voice Agent is running"}
```

### 5.2 Service Test
```bash
curl https://your-render-url.onrender.com/test-transcription
# Should show service configuration status
```

### 5.3 Web Interface
1. Open `https://your-render-url.onrender.com`
2. Test audio recording functionality
3. Verify WebSocket connections work

## Step 6: Monitoring and Maintenance

### 6.1 Logs
- Access logs from Render dashboard
- Monitor for errors in `app.log` (if persisted)
- Set up alerting for critical errors

### 6.2 Performance
- Monitor response times in Render dashboard
- Check API usage and quotas
- Scale up if needed (Render allows easy scaling)

### 6.3 Storage Considerations
- Render has ephemeral storage (uploads may not persist)
- Consider using external storage for audio files
- Implement cleanup of temporary files

## Troubleshooting Common Issues

### Issue: WebSocket Connection Fails
**Solution**: Ensure Render's WebSocket support is enabled (it should work automatically)

### Issue: API Keys Not Working
**Solution**: 
1. Double-check environment variables in Render dashboard
2. Ensure they're marked as "Secret"
3. Verify API keys are valid and have sufficient quota

### Issue: Build Fails
**Solution**:
1. Check `requirements.txt` for compatibility
2. Verify all required files are in repository
3. Check build logs in Render dashboard

### Issue: Application Crashes
**Solution**:
1. Check application logs
2. Verify all environment variables are set
3. Test locally with same configuration

## Cost Optimization

### Free Tier
- 750 free build minutes per month
- 100 free web service hours per month
- Suitable for development and testing

### Paid Plans
- Starts at $7/month for basic web service
- Additional features: custom domains, auto-scaling, more resources

## Best Practices

1. **Use Environment Variables**: Never hardcode API keys
2. **Enable Auto-Deploy**: For continuous deployment
3. **Monitor Logs**: Regularly check for errors
4. **Set Up Alerts**: For service downtime or errors
5. **Regular Backups**: Backup your code and environment configuration

## Migration from Local to Render

### Before Migration
1. Test application locally with production settings
2. Ensure all environment variables are externalized
3. Verify Dockerfile works locally: `docker build -t test .`

### After Migration
1. Test all endpoints on Render
2. Verify WebSocket functionality
3. Check audio recording and playback
4. Monitor performance and error rates

## Support Resources

- Render Documentation: https://render.com/docs
- Render Status: https://status.render.com
- Community Support: Render Discord community

Your AI Voice Agent is now deployed on Render and ready for production use!
