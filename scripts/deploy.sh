#!/bin/bash

# Taxi Streaming System - Deployment Script
# Supports multiple deployment strategies

set -e

# Configuration
VEHICLE_REG="${VEHICLE_REGISTRATION:-HDJ864L}"
CAMERA_IP="${CAMERA_IP:-192.168.8.200}"
DEPLOYMENT_MODE="${DEPLOYMENT_MODE:-local}"  # local, cloud, edge
UPDATE_STRATEGY="${UPDATE_STRATEGY:-git}"    # git, webhook, registry

echo "🚖 Deploying Taxi Streaming System"
echo "Vehicle: $VEHICLE_REG"
echo "Camera: $CAMERA_IP"
echo "Mode: $DEPLOYMENT_MODE"
echo "Update Strategy: $UPDATE_STRATEGY"

# Create necessary directories
mkdir -p logs config footage backups

# Generate configuration
cat > config/${VEHICLE_REG}_production.yaml << EOF
vehicle:
  registration_number: $VEHICLE_REG
  device_id: rpi_${VEHICLE_REG,,}_prod
  make: Toyota
  model: Quantum
  capacity: 14

camera:
  ip_address: $CAMERA_IP
  username: admin
  password: Random336#
  rtsp_url: rtsp://admin:Random336%23@$CAMERA_IP:554/stream1
  resolution: 1920x1080
  fps: 25

streaming:
  port: 8000
  host: 0.0.0.0
  qualities:
    low: {resolution: "480x360", fps: 15, bitrate: "200k"}
    medium: {resolution: "720x540", fps: 15, bitrate: "400k"}
    high: {resolution: "1920x1080", fps: 15, bitrate: "800k"}

update:
  strategy: $UPDATE_STRATEGY
  interval: 300
  auto_restart: true
  backup_count: 5
EOF

# Deployment based on mode
case $DEPLOYMENT_MODE in
  "local")
    echo "🏠 Local deployment"
    docker-compose up -d
    ;;
  "cloud")
    echo "☁️ Cloud deployment"
    deploy_to_cloud
    ;;
  "edge")
    echo "📡 Edge deployment (Raspberry Pi)"
    deploy_to_edge
    ;;
esac

# Setup update mechanism
setup_updates() {
  case $UPDATE_STRATEGY in
    "git")
      echo "📦 Setting up Git-based updates"
      # Already handled in Dockerfile
      ;;
    "webhook")
      echo "🔗 Setting up webhook updates"
      setup_webhook_updates
      ;;
    "registry")
      echo "🐳 Setting up Docker registry updates"
      setup_registry_updates
      ;;
  esac
}

deploy_to_cloud() {
  # Deploy to cloud provider (AWS, GCP, Azure)
  echo "Deploying to cloud..."
  
  # Example for AWS ECS
  if command -v aws &> /dev/null; then
    aws ecs update-service \
      --cluster taxi-fleet \
      --service taxi-streaming-$VEHICLE_REG \
      --force-new-deployment
  fi
}

deploy_to_edge() {
  # Deploy to Raspberry Pi or edge device
  echo "Deploying to edge device..."
  
  # Optimize for ARM architecture
  docker build --platform linux/arm64 -t taxi-streaming:$VEHICLE_REG .
  docker run -d \
    --name taxi-$VEHICLE_REG \
    --restart unless-stopped \
    -p 8000:8000 \
    -v $(pwd)/config:/app/config \
    -v $(pwd)/logs:/app/logs \
    taxi-streaming:$VEHICLE_REG
}

setup_webhook_updates() {
  # Create webhook endpoint for updates
  cat > webhook_update.py << 'EOF'
from fastapi import FastAPI, Request
import subprocess
import hmac
import hashlib

app = FastAPI()

@app.post("/webhook/update")
async def handle_update(request: Request):
    # Verify webhook signature (GitHub/GitLab)
    signature = request.headers.get("X-Hub-Signature-256")
    if verify_signature(await request.body(), signature):
        subprocess.run(["/app/scripts/remote_update.py"])
        return {"status": "update_triggered"}
    return {"status": "unauthorized"}

def verify_signature(payload, signature):
    secret = os.getenv("WEBHOOK_SECRET", "")
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
EOF
}

setup_registry_updates() {
  # Setup Docker registry polling
  echo "Setting up registry updates with Watchtower"
  # Already configured in docker-compose.yml
}

# Health check
health_check() {
  echo "🏥 Performing health check..."
  sleep 10
  
  if curl -f http://localhost:8000/health; then
    echo "✅ Service is healthy"
    return 0
  else
    echo "❌ Service health check failed"
    return 1
  fi
}

# Main execution
setup_updates
health_check

echo "🎉 Deployment completed successfully!"
echo "📊 Access dashboard: http://localhost:8000/viewer"
echo "📱 Mobile API: http://localhost:8000/mobile/vehicles"
echo "📋 Logs: docker logs taxi-hdj864l-stream"
