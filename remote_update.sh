#!/bin/bash
# Remote update script for Taxi Passenger Counting System

set -e

# Configuration
PI_USER="admin"
PI_HOST=""
PROJECT_DIR="taxitrack"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check if PI_HOST is provided
if [ -z "$1" ]; then
    print_error "Usage: $0 <raspberry-pi-ip> [command]"
    print_error "Commands:"
    print_error "  update    - Update code and restart system (default)"
    print_error "  status    - Check system status"
    print_error "  logs      - Show recent logs"
    print_error "  restart   - Restart containers"
    print_error "  stop      - Stop system"
    print_error "  start     - Start system"
    print_error "  health    - Check system health"
    print_error ""
    print_error "Example: $0 192.168.1.100 update"
    exit 1
fi

PI_HOST=$1
COMMAND=${2:-update}

print_header "Remote Management for $PI_HOST"

# Test SSH connection
test_connection() {
    print_status "Testing SSH connection to $PI_HOST..."
    if ! ssh -o ConnectTimeout=10 $PI_USER@$PI_HOST "echo 'Connected successfully'" >/dev/null 2>&1; then
        print_error "Cannot connect to $PI_USER@$PI_HOST"
        print_error "Make sure SSH is enabled and the IP is correct"
        exit 1
    fi
    print_status "SSH connection successful"
}

# Update system
update_system() {
    print_header "Updating System"
    
    ssh $PI_USER@$PI_HOST << EOF
cd $PROJECT_DIR

echo "=== Pulling latest code ==="
git fetch origin
git reset --hard origin/main

echo "=== Stopping containers ==="
docker-compose -f docker-compose.simple.yml down

echo "=== Starting updated containers ==="
docker-compose -f docker-compose.simple.yml up -d

echo "=== Waiting for startup ==="
sleep 15

echo "=== System Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo "=== Health Check ==="
for i in {1..5}; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ API is healthy"
        break
    else
        echo "⏳ Waiting for API... (attempt \$i/5)"
        sleep 5
    fi
done

echo "=== Recent Logs ==="
docker logs taxi-hdj864l-api --tail 10

echo "Update completed!"
EOF
}

# Check system status
check_status() {
    print_header "System Status"
    
    ssh $PI_USER@$PI_HOST << EOF
cd $PROJECT_DIR

echo "=== Container Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== System Resources ==="
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" | awk '{print \$2 \$3}' | sed 's/%us,/% user,/' | sed 's/%sy/% system/'

echo "Memory Usage:"
free -h | grep Mem | awk '{printf "Used: %s/%s (%.1f%%)\n", \$3, \$2, (\$3/\$2)*100}'

echo "Disk Usage:"
df -h / | tail -1 | awk '{printf "Used: %s/%s (%s)\n", \$3, \$2, \$5}'

echo ""
echo "=== Temperature ==="
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    temp=\$(cat /sys/class/thermal/thermal_zone0/temp)
    temp=\$((\$temp / 1000))
    echo "CPU Temperature: \${temp}°C"
else
    echo "Temperature monitoring not available"
fi

echo ""
echo "=== Network Status ==="
ping -c 1 8.8.8.8 >/dev/null 2>&1 && echo "✅ Internet connection: OK" || echo "❌ Internet connection: FAILED"

echo ""
echo "=== API Health ==="
curl -f http://localhost:8000/health >/dev/null 2>&1 && echo "✅ API health: OK" || echo "❌ API health: FAILED"
EOF
}

# Show logs
show_logs() {
    print_header "Recent Logs"
    
    ssh $PI_USER@$PI_HOST << EOF
cd $PROJECT_DIR

echo "=== Container Logs (last 50 lines) ==="
docker logs taxi-hdj864l-api --tail 50

echo ""
echo "=== System Logs ==="
journalctl -u docker --no-pager -n 20
EOF
}

# Restart system
restart_system() {
    print_header "Restarting System"
    
    ssh $PI_USER@$PI_HOST << EOF
cd $PROJECT_DIR

echo "=== Restarting containers ==="
docker-compose -f docker-compose.simple.yml restart

echo "=== Waiting for startup ==="
sleep 10

echo "=== Status Check ==="
docker ps --format "table {{.Names}}\t{{.Status}}"

curl -f http://localhost:8000/health >/dev/null 2>&1 && echo "✅ System restarted successfully" || echo "❌ System restart failed"
EOF
}

# Stop system
stop_system() {
    print_header "Stopping System"
    
    ssh $PI_USER@$PI_HOST << EOF
cd $PROJECT_DIR

echo "=== Stopping containers ==="
docker-compose -f docker-compose.simple.yml down

echo "=== Verifying shutdown ==="
docker ps --format "table {{.Names}}\t{{.Status}}"

echo "System stopped"
EOF
}

# Start system
start_system() {
    print_header "Starting System"
    
    ssh $PI_USER@$PI_HOST << EOF
cd $PROJECT_DIR

echo "=== Starting containers ==="
docker-compose -f docker-compose.simple.yml up -d

echo "=== Waiting for startup ==="
sleep 10

echo "=== Status Check ==="
docker ps --format "table {{.Names}}\t{{.Status}}"

curl -f http://localhost:8000/health >/dev/null 2>&1 && echo "✅ System started successfully" || echo "❌ System start failed"
EOF
}

# Health check
health_check() {
    print_header "Health Check"
    
    ssh $PI_USER@$PI_HOST << EOF
echo "=== API Health Check ==="
if curl -f http://localhost:8000/health 2>/dev/null; then
    echo ""
    echo "✅ API is responding"
else
    echo "❌ API is not responding"
fi

echo ""
echo "=== Container Health ==="
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "=== Quick System Check ==="
uptime
EOF
}

# Main execution
test_connection

case $COMMAND in
    "update")
        update_system
        ;;
    "status")
        check_status
        ;;
    "logs")
        show_logs
        ;;
    "restart")
        restart_system
        ;;
    "stop")
        stop_system
        ;;
    "start")
        start_system
        ;;
    "health")
        health_check
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        print_error "Available commands: update, status, logs, restart, stop, start, health"
        exit 1
        ;;
esac

print_status "Operation completed successfully!"
