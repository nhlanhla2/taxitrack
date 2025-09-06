# 🚖 Taxi Streaming System - Deployment Guide

## 🎯 Remote Update Strategies (Cost Comparison)

| Strategy | Monthly Cost | Complexity | Update Speed | Reliability |
|----------|-------------|------------|--------------|-------------|
| **Git-based** | **$0** | Low | 30s | High |
| **Webhook** | **$0-5** | Medium | 5s | High |
| **Docker Registry** | **$5-20** | Low | 10s | Very High |
| **Cloud CI/CD** | **$10-50** | High | 15s | Very High |

## 🏆 Recommended: Git-Based Updates (FREE)

### ✅ Advantages:
- **Zero cost** - Uses GitHub/GitLab free tier
- **Automatic updates** every 5 minutes
- **Rollback capability** with git history
- **Version control** built-in
- **Works offline** - caches updates

### 🚀 Quick Setup:

```bash
# 1. Clone and deploy
git clone https://github.com/yourusername/taxi-streaming.git
cd taxi-streaming
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 2. Start with auto-updates
docker-compose up -d
```

## 📋 Deployment Options

### Option 1: Local Development
```bash
export DEPLOYMENT_MODE=local
export VEHICLE_REGISTRATION=HDJ864L
export CAMERA_IP=192.168.3.200
./scripts/deploy.sh
```

### Option 2: Raspberry Pi (Edge)
```bash
export DEPLOYMENT_MODE=edge
export UPDATE_STRATEGY=git
./scripts/deploy.sh
```

### Option 3: Cloud Deployment
```bash
export DEPLOYMENT_MODE=cloud
export UPDATE_STRATEGY=registry
./scripts/deploy.sh
```

## 🔄 Update Mechanisms

### 1. Git-Based Updates (Recommended)
- **Cost**: FREE
- **Setup**: Automatic in Docker container
- **How it works**:
  1. Container checks GitHub every 5 minutes
  2. Pulls latest changes if available
  3. Restarts service with zero downtime
  4. Keeps backups of previous versions

### 2. Webhook Updates
- **Cost**: FREE (with ngrok) or $5/month (with domain)
- **Setup**: Requires webhook endpoint
- **How it works**:
  1. Push to GitHub triggers webhook
  2. Webhook calls update endpoint
  3. Immediate update (5-10 seconds)

### 3. Docker Registry Updates
- **Cost**: $5-20/month (Docker Hub Pro)
- **Setup**: Use Watchtower container
- **How it works**:
  1. Push new image to registry
  2. Watchtower detects new image
  3. Pulls and restarts container

## 🛠️ Configuration

### Environment Variables
```bash
# Vehicle Configuration
VEHICLE_REGISTRATION=HDJ864L
CAMERA_IP=192.168.3.200
CAMERA_USERNAME=admin
CAMERA_PASSWORD=Random336#

# Update Configuration
GIT_REPO_URL=https://github.com/yourusername/taxi-streaming.git
UPDATE_INTERVAL=300  # 5 minutes
UPDATE_STRATEGY=git

# Deployment Configuration
DEPLOYMENT_MODE=local  # local, cloud, edge
ENVIRONMENT=production
```

### Docker Compose Override
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  taxi-streaming:
    environment:
      - VEHICLE_REGISTRATION=HDJ864L
      - CAMERA_IP=192.168.3.200
      - UPDATE_INTERVAL=180  # 3 minutes
    volumes:
      - ./custom-config:/app/config
```

## 📊 Monitoring & Logging

### Health Checks
```bash
# Check service health
curl http://localhost:8000/health

# View logs
docker logs taxi-hdj864l-stream -f

# Check update status
docker exec taxi-hdj864l-stream cat /app/logs/update.log
```

### Metrics Dashboard
- **Service Status**: http://localhost:8000/health
- **Stream Viewer**: http://localhost:8000/viewer
- **Mobile API**: http://localhost:8000/mobile/vehicles
- **Update Logs**: `/app/logs/update.log`

## 🔧 Troubleshooting

### Common Issues:

1. **Updates not working**:
   ```bash
   # Check git configuration
   docker exec taxi-hdj864l-stream git status
   
   # Manual update
   docker exec taxi-hdj864l-stream /app/scripts/remote_update.py
   ```

2. **Camera connection issues**:
   ```bash
   # Test camera directly
   curl "http://localhost:8000/mobile/vehicle/HDJ864L/stream/info"
   ```

3. **Container not starting**:
   ```bash
   # Check logs
   docker logs taxi-hdj864l-stream
   
   # Rebuild container
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

## 💰 Cost Optimization

### FREE Tier Setup:
- **Git Repository**: GitHub/GitLab (Free)
- **Container Registry**: Docker Hub (Free - 1 private repo)
- **Monitoring**: Built-in health checks (Free)
- **Updates**: Git-based polling (Free)

### Total Monthly Cost: **$0**

### Paid Upgrades (Optional):
- **Docker Hub Pro**: $5/month (unlimited private repos)
- **Custom Domain**: $10/year (for webhooks)
- **Cloud Hosting**: $10-50/month (AWS/GCP/Azure)

## 🚀 Production Deployment

### Step 1: Prepare Repository
```bash
# Create GitHub repository
gh repo create taxi-streaming --private
git remote add origin https://github.com/yourusername/taxi-streaming.git
git push -u origin main
```

### Step 2: Deploy to Production
```bash
# Set production environment
export ENVIRONMENT=production
export GIT_REPO_URL=https://github.com/yourusername/taxi-streaming.git

# Deploy
./scripts/deploy.sh
```

### Step 3: Verify Deployment
```bash
# Check all services
docker-compose ps

# Test streaming
curl http://localhost:8000/mobile/vehicle/HDJ864L/stream/info

# Monitor updates
tail -f logs/update.log
```

## 🎉 Success!

Your taxi streaming system is now deployed with:
- ✅ **Automatic updates** from GitHub
- ✅ **Zero-downtime deployments**
- ✅ **Health monitoring**
- ✅ **Backup & rollback**
- ✅ **Cost-effective** ($0/month)

**Next Steps**:
1. Push code changes to GitHub
2. Updates deploy automatically within 5 minutes
3. Monitor via dashboard at http://localhost:8000/viewer
4. Scale to multiple vehicles by changing `VEHICLE_REGISTRATION`
