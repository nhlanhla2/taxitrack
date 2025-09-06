# Mini Bus Taxi Passenger Counting System

A comprehensive passenger counting system for mini bus taxis using computer vision, face tracking, and real-time API integration.

## Features

- **Real-time Passenger Counting**: Accurate entry/exit detection using computer vision
- **Anti-Fraud Protection**: Face tracking to prevent double counting and handle temporary exits
- **Trip Management**: API-driven trip lifecycle with start/stop controls
- **Capacity Management**: 14-passenger limit with overload detection and flagging
- **Backend Integration**: Real-time updates to backend systems via REST API
- **Offline Capability**: Local data storage with sync when connectivity returns
- **Raspberry Pi Optimized**: Efficient processing for edge deployment

## Hardware Requirements

- Raspberry Pi 4 (4GB+ RAM recommended)
- Dome network camera (IP camera with RTSP stream)
- MicroSD card (32GB+ Class 10)
- Stable power supply for vehicle mounting
- Network connectivity (4G/WiFi)

## Software Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    System Components                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   Camera    │  │   Computer   │  │      Trip       │   │
│  │   Stream    │→ │    Vision    │→ │   Management    │   │
│  │  Processor  │  │   Module     │  │     API         │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
│                           │                   │             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │    Face     │  │    Data      │  │    Backend      │   │
│  │  Tracking   │← │   Storage    │→ │  Integration    │   │
│  │   Module    │  │   & Logging  │  │     Module      │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-venv cmake build-essential
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y libatlas-base-dev libhdf5-dev libhdf5-serial-dev
sudo apt install -y libqtgui4 libqtwebkit4 libqt4-test
```

### Project Setup
```bash
# Clone and setup
git clone <repository-url>
cd TT
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration
```bash
# Copy and edit configuration
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your camera and API settings
```

## Usage

### Starting the System
```bash
# Activate virtual environment
source venv/bin/activate

# Start the passenger counting service
python main.py

# Or run as systemd service
sudo systemctl start taxi-counter
```

### API Endpoints

- `POST /trip/start` - Start a new trip
- `POST /trip/stop` - Stop current trip
- `GET /trip/status` - Get current trip status
- `GET /trip/count` - Get real-time passenger count
- `GET /health` - System health check

## Project Structure

```
TT/
├── src/
│   ├── computer_vision/     # CV modules for detection and tracking
│   ├── face_tracking/       # Face recognition and anti-fraud
│   ├── trip_management/     # Trip lifecycle and API
│   ├── backend_integration/ # API client and sync
│   ├── data_storage/        # Database and logging
│   └── utils/              # Shared utilities
├── config/                 # Configuration files
├── tests/                  # Test suite
├── scripts/               # Deployment and setup scripts
├── docs/                  # Documentation
└── requirements.txt       # Python dependencies
```

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Development Mode
```bash
# Run with hot reload
uvicorn src.trip_management.api:app --reload --host 0.0.0.0 --port 8000
```

## 🚀 **Raspberry Pi Deployment**

### **1. Prepare Raspberry Pi**
```bash
# SSH into your Raspberry Pi
ssh pi@<raspberry-pi-ip>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker pi

# Install Docker Compose
sudo apt install docker-compose -y

# Reboot to apply changes
sudo reboot
```

### **2. Deploy to Raspberry Pi**
```bash
# Clone repository on Pi
git clone <your-repo-url> taxi-streaming
cd taxi-streaming

# Deploy with Docker
docker-compose -f docker-compose.simple.yml up -d

# Check status
docker ps
docker logs taxi-hdj864l-api
```

### **3. Remote Code Updates**
```bash
# Create update script on Pi
cat > update_system.sh << 'EOF'
#!/bin/bash
echo "Updating Taxi System..."
cd ~/taxi-streaming
git pull origin main
docker-compose -f docker-compose.simple.yml down
docker-compose -f docker-compose.simple.yml up -d --build
echo "Update completed!"
EOF

chmod +x update_system.sh

# Run updates remotely via SSH
ssh pi@<raspberry-pi-ip> './update_system.sh'
```

## 📡 **Mobile Network & Dynamic IP Solutions**

### **Problem**: Mobile networks use dynamic IPs, breaking static IP camera connections

### **Solutions**:

#### **Option 1: Use Local Network IPs (Recommended)**
```yaml
# Update config/HDJ864L_live.yaml
camera:
  ip: 192.168.1.100  # Use router's local IP instead of public IP
  stream_url: rtsp://admin:Random336%23@192.168.1.100:554/stream1
```

#### **Option 2: Dynamic DNS**
```bash
# Install ddclient for dynamic DNS
sudo apt install ddclient -y
# Configure camera to use domain name: camera.yourdomain.com
```

### **Mobile Router Configuration**
1. **Set camera to DHCP reservation** (static local IP like 192.168.1.100)
2. **Configure port forwarding**: External:554 → Camera:554
3. **Use router's local IP** in your configuration
4. **Enable UPnP** if available for automatic port mapping

## 🔄 **Automated Remote Management**

### **Remote Monitoring Script**
```bash
# Add to crontab on Pi for health monitoring
*/5 * * * * curl -f http://localhost:8000/health || docker-compose -f ~/taxi-streaming/docker-compose.simple.yml restart
```

### **SSH Remote Updates**
```bash
# Update system remotely
ssh pi@<pi-ip> 'cd taxi-streaming && git pull && docker-compose -f docker-compose.simple.yml restart'
```

## 🌐 **Network Architecture for Mobile Deployment**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Mobile ISP    │    │   4G/5G Router   │    │  Raspberry Pi   │
│  (Dynamic IP)   │◄──►│  192.168.1.1     │◄──►│  192.168.1.10   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                       ┌──────────────────┐    ┌─────────────────┐
                       │   IP Camera      │    │   Docker API    │
                       │  192.168.1.100   │    │   Port: 8000    │
                       └──────────────────┘    └─────────────────┘
```

## License

MIT License - see LICENSE file for details.
