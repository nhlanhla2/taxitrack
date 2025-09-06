#!/bin/bash
# Deploy Taxi Passenger Counting System to Raspberry Pi

set -e

# Configuration
PI_USER="admin"
PI_HOST=""
REPO_URL="https://github.com/nhlanhla2/taxitrack.git"
PROJECT_DIR="taxitrack"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if PI_HOST is provided
if [ -z "$1" ]; then
    print_error "Usage: $0 <raspberry-pi-ip>"
    print_error "Examples:"
    print_error "  Local network: $0 192.168.1.100"
    print_error "  Tailscale VPN: $0 100.x.x.x"
    print_error "  Mobile router: $0 mobile-router-ip"
    exit 1
fi

PI_HOST=$1

print_status "Deploying to Raspberry Pi at $PI_HOST"

# Test SSH connection
print_status "Testing SSH connection..."
if ! ssh -o ConnectTimeout=10 $PI_USER@$PI_HOST "echo 'SSH connection successful'"; then
    print_error "Cannot connect to $PI_USER@$PI_HOST"
    print_error "Make sure SSH is enabled and the IP is correct"
    exit 1
fi

# Install Docker if not present
print_status "Installing Docker on Raspberry Pi..."
ssh $PI_USER@$PI_HOST << 'EOF'
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker admin
    rm get-docker.sh
    echo "Docker installed successfully"
else
    echo "Docker already installed"
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo apt update
    sudo apt install -y docker-compose
    echo "Docker Compose installed successfully"
else
    echo "Docker Compose already installed"
fi
EOF

# Clone or update repository
print_status "Setting up project on Raspberry Pi..."
ssh $PI_USER@$PI_HOST << EOF
if [ -d "$PROJECT_DIR" ]; then
    echo "Project directory exists, updating..."
    cd $PROJECT_DIR
    git pull origin main
else
    echo "Cloning repository..."
    git clone $REPO_URL $PROJECT_DIR
    cd $PROJECT_DIR
fi

# Make scripts executable
chmod +x *.sh 2>/dev/null || true
EOF

# Copy configuration files
print_status "Copying configuration files..."
scp config/HDJ864L_live.yaml $PI_USER@$PI_HOST:~/$PROJECT_DIR/config/
scp docker-compose.simple.yml $PI_USER@$PI_HOST:~/$PROJECT_DIR/
scp api_server_simple.py $PI_USER@$PI_HOST:~/$PROJECT_DIR/

# Deploy with Docker
print_status "Deploying with Docker..."
ssh $PI_USER@$PI_HOST << EOF
cd $PROJECT_DIR

# Stop existing containers
docker-compose -f docker-compose.simple.yml down 2>/dev/null || true

# Start new deployment
docker-compose -f docker-compose.simple.yml up -d

# Wait for container to start
sleep 10

# Check status
echo "=== Container Status ==="
docker ps

echo "=== Container Logs ==="
docker logs taxi-hdj864l-api --tail 20

echo "=== Health Check ==="
curl -f http://localhost:8000/health || echo "Health check failed"
EOF

# Create update script on Pi
print_status "Creating update script on Raspberry Pi..."
ssh $PI_USER@$PI_HOST << 'EOF'
cat > ~/update_taxi_system.sh << 'SCRIPT_EOF'
#!/bin/bash
echo "=== Updating Taxi System ==="
cd ~/taxitrack

echo "Pulling latest code..."
git pull origin main

echo "Restarting containers..."
docker-compose -f docker-compose.simple.yml down
docker-compose -f docker-compose.simple.yml up -d

echo "Waiting for startup..."
sleep 10

echo "=== System Status ==="
docker ps
docker logs taxi-hdj864l-api --tail 10

echo "=== Health Check ==="
curl -f http://localhost:8000/health && echo " - API is healthy" || echo " - API health check failed"

echo "Update completed!"
SCRIPT_EOF

chmod +x ~/update_taxi_system.sh
echo "Update script created at ~/update_taxi_system.sh"
EOF

# Create monitoring cron job
print_status "Setting up monitoring..."
ssh $PI_USER@$PI_HOST << 'EOF'
# Add health check to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * curl -f http://localhost:8000/health >/dev/null 2>&1 || (cd ~/taxitrack && docker-compose -f docker-compose.simple.yml restart)") | crontab -
echo "Health monitoring cron job added"
EOF

print_status "Deployment completed successfully!"
print_status "You can now:"
print_status "  - Access API at: http://$PI_HOST:8000"
print_status "  - Update remotely: ssh $PI_USER@$PI_HOST './update_taxi_system.sh'"
print_status "  - Check logs: ssh $PI_USER@$PI_HOST 'docker logs taxi-hdj864l-api'"
print_status "  - Monitor status: ssh $PI_USER@$PI_HOST 'docker ps'"

print_warning "Remember to:"
print_warning "  1. Configure your camera IP to use local network (192.168.1.x)"
print_warning "  2. Set up DHCP reservation for camera in router"
print_warning "  3. Test the system with actual camera feed"
