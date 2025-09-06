# Camera Setup Guide for Taxi Passenger Counting System

## Overview

This guide provides comprehensive instructions for setting up cameras in mini bus taxis for the passenger counting system. The system supports various camera types and configurations for optimal performance.

## Supported Camera Types

### 1. IP Cameras (Recommended)
- **RTSP Streaming Cameras**
- **HTTP/MJPEG Cameras**
- **Dome cameras for vehicle mounting**

### 2. USB Cameras
- **USB 3.0 cameras for high resolution**
- **USB 2.0 cameras for basic setups**

## Camera Requirements

### Technical Specifications
- **Resolution**: Minimum 1280x720, Recommended 1920x1080
- **Frame Rate**: Minimum 15 FPS, Recommended 30 FPS
- **Field of View**: Wide angle (90-120 degrees)
- **Low Light Performance**: Good performance in vehicle lighting
- **Mounting**: Dome or compact form factor

### Network Requirements (IP Cameras)
- **Ethernet or WiFi connectivity**
- **RTSP or HTTP streaming support**
- **Authentication support (username/password)**
- **Stable network connection**

## Camera Positioning

### Optimal Placement
```
    [Front of Vehicle]
         Door
    ┌─────────────┐
    │      🎥     │  ← Camera mounted on ceiling
    │             │    facing down towards door
    │   Passenger │
    │    Seats    │
    │             │
    └─────────────┘
    [Back of Vehicle]
```

### Mounting Guidelines
1. **Height**: 2.5-3 meters from floor
2. **Angle**: 45-60 degrees downward
3. **Coverage**: Full door area and entry path
4. **Lighting**: Avoid direct sunlight interference
5. **Security**: Tamper-resistant mounting

## Network Configuration

### Vehicle Network Setup
```
Internet (4G/WiFi)
        │
    ┌───▼───┐
    │Router │ 192.168.1.1
    └───┬───┘
        │
    ┌───▼───┐     ┌─────────┐
    │Camera │     │Raspberry│
    │.1.100 │◄────┤Pi .1.10 │
    └───────┘     └─────────┘
```

### IP Address Allocation
- **Router**: 192.168.1.1
- **Raspberry Pi**: 192.168.1.10
- **Camera**: 192.168.1.100
- **Subnet**: 192.168.1.0/24

## Camera Configuration Examples

### Example 1: RTSP IP Camera (HDJ864L)
```yaml
vehicle:
  registration_number: "HDJ864L"
  fleet_id: "cape_town_fleet_001"

camera:
  type: "rtsp_stream"
  stream_url: "rtsp://192.168.1.100:554/stream1"
  username: "admin"
  password: "camera123"
  width: 1920
  height: 1080
  fps: 30
```

### Example 2: HTTP Camera
```yaml
camera:
  type: "http_stream"
  stream_url: "http://192.168.1.100:8080/video"
  username: "admin"
  password: "camera123"
  width: 1280
  height: 720
  fps: 15
```

### Example 3: USB Camera
```yaml
camera:
  type: "usb_camera"
  usb_camera_index: 0
  width: 1280
  height: 720
  fps: 15
```

## Installation Process

### Step 1: Physical Installation
1. **Mount camera** in optimal position
2. **Run power cable** to camera
3. **Connect network cable** (for IP cameras)
4. **Secure all cables** to prevent damage
5. **Test camera power** and connectivity

### Step 2: Network Configuration
```bash
# Configure camera IP address
# Access camera web interface at default IP
# Set static IP: 192.168.1.100
# Configure username/password
# Enable RTSP streaming
# Set resolution and frame rate
```

### Step 3: Test Camera Connection
```bash
# Test camera connectivity
python3 scripts/test_camera.py --rtsp rtsp://192.168.1.100:554/stream1 \
  --username admin --password camera123

# Or scan for cameras on network
python3 scripts/test_camera.py --scan 192.168.1
```

### Step 4: Vehicle Configuration
```bash
# Configure vehicle with camera details
python3 scripts/configure_vehicle.py \
  --registration HDJ864L \
  --camera-url rtsp://192.168.1.100:554/stream1 \
  --camera-username admin \
  --camera-password camera123 \
  --make Toyota \
  --model Quantum \
  --capacity 14 \
  --fleet-id cape_town_fleet_001
```
