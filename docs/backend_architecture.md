# Taxi Passenger Counting System - Backend Architecture

## Overview

This document outlines the comprehensive backend architecture for the multi-vehicle taxi passenger counting system. The backend supports multiple vehicles, real-time data synchronization, footage management, and fleet analytics.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Backend System Architecture                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │   Vehicle   │  │   Fleet      │  │     Analytics       │   │
│  │ Management  │→ │ Management   │→ │     & Reporting     │   │
│  │     API     │  │     API      │  │        API          │   │
│  └─────────────┘  └──────────────┘  └─────────────────────┘   │
│         │                  │                      │           │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │    Trip     │  │   Footage    │  │   Real-time         │   │
│  │ Management  │  │ Management   │  │   WebSocket         │   │
│  │     API     │  │     API      │  │     Server          │   │
│  └─────────────┘  └──────────────┘  └─────────────────────┘   │
│         │                  │                      │           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Database Layer (PostgreSQL)               │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           File Storage (AWS S3 / MinIO)                │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend Framework
- **FastAPI** - High-performance async API framework
- **Python 3.9+** - Programming language
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation and serialization

### Database
- **PostgreSQL 14+** - Primary database
- **Redis** - Caching and session management
- **TimescaleDB** - Time-series data for analytics

### File Storage
- **AWS S3** or **MinIO** - Video footage storage
- **Local Storage** - Temporary file handling

### Authentication & Security
- **JWT** - Token-based authentication
- **OAuth 2.0** - Third-party authentication
- **HTTPS/TLS** - Encrypted communication

### Monitoring & Logging
- **Prometheus** - Metrics collection
- **Grafana** - Monitoring dashboards
- **ELK Stack** - Centralized logging

## Database Schema

### Core Tables

#### 1. Fleets Table
```sql
CREATE TABLE fleets (
    fleet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    address TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
```

#### 2. Vehicles Table
```sql
CREATE TABLE vehicles (
    vehicle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fleet_id UUID REFERENCES fleets(fleet_id),
    registration_number VARCHAR(20) UNIQUE NOT NULL,
    make VARCHAR(100),
    model VARCHAR(100),
    year INTEGER,
    color VARCHAR(50),
    capacity INTEGER DEFAULT 14,
    status VARCHAR(20) DEFAULT 'active',
    route VARCHAR(255),
    device_id VARCHAR(255) UNIQUE NOT NULL,

    -- Camera Configuration
    camera_type VARCHAR(50) DEFAULT 'ip_camera',
    camera_url TEXT,
    camera_username VARCHAR(255),
    camera_password_hash VARCHAR(255),

    -- Location
    gps_enabled BOOLEAN DEFAULT FALSE,
    current_latitude DECIMAL(10, 8),
    current_longitude DECIMAL(11, 8),

    -- Statistics
    total_trips INTEGER DEFAULT 0,
    total_passengers INTEGER DEFAULT 0,
    last_trip_date TIMESTAMP,

    -- Maintenance
    installation_date TIMESTAMP DEFAULT NOW(),
    last_maintenance TIMESTAMP,
    next_maintenance TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_vehicles_registration ON vehicles(registration_number);
CREATE INDEX idx_vehicles_fleet ON vehicles(fleet_id);
CREATE INDEX idx_vehicles_device ON vehicles(device_id);
```

#### 3. Drivers Table
```sql
CREATE TABLE drivers (
    driver_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fleet_id UUID REFERENCES fleets(fleet_id),
    license_number VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),
    date_of_birth DATE,
    hire_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    current_vehicle_id UUID REFERENCES vehicles(vehicle_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_drivers_license ON drivers(license_number);
CREATE INDEX idx_drivers_fleet ON drivers(fleet_id);
```

#### 4. Trips Table
```sql
CREATE TABLE trips (
    trip_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID REFERENCES vehicles(vehicle_id) NOT NULL,
    driver_id UUID REFERENCES drivers(driver_id),

    -- Trip Details
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    route VARCHAR(255),

    -- Passenger Data
    current_passenger_count INTEGER DEFAULT 0,
    max_passenger_count INTEGER DEFAULT 0,
    total_entries INTEGER DEFAULT 0,
    total_exits INTEGER DEFAULT 0,

    -- Capacity Management
    max_capacity INTEGER DEFAULT 14,
    overload_events INTEGER DEFAULT 0,
    is_overloaded BOOLEAN DEFAULT FALSE,

    -- Location Data
    start_latitude DECIMAL(10, 8),
    start_longitude DECIMAL(11, 8),
    end_latitude DECIMAL(10, 8),
    end_longitude DECIMAL(11, 8),

    -- Status
    status VARCHAR(20) DEFAULT 'active',

    -- Backend Sync
    last_backend_sync TIMESTAMP,
    sync_status VARCHAR(20) DEFAULT 'pending',

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_trips_vehicle ON trips(vehicle_id);
CREATE INDEX idx_trips_start_time ON trips(start_time);
CREATE INDEX idx_trips_status ON trips(status);
```

#### 5. Trip Events Table
```sql
CREATE TABLE trip_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID REFERENCES trips(trip_id) NOT NULL,
    vehicle_id UUID REFERENCES vehicles(vehicle_id) NOT NULL,

    -- Event Details
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    passenger_count INTEGER DEFAULT 0,

    -- Location
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),

    -- Metadata
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_trip_events_trip ON trip_events(trip_id);
CREATE INDEX idx_trip_events_timestamp ON trip_events(timestamp);
CREATE INDEX idx_trip_events_type ON trip_events(event_type);
```

#### 6. Footage Records Table
```sql
CREATE TABLE footage_records (
    footage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID REFERENCES vehicles(vehicle_id) NOT NULL,
    trip_id UUID REFERENCES trips(trip_id),

    -- File Information
    filename VARCHAR(255) NOT NULL,
    file_path TEXT,
    file_size BIGINT DEFAULT 0,
    duration_seconds INTEGER DEFAULT 0,

    -- Recording Details
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    resolution VARCHAR(20) DEFAULT '1920x1080',
    fps INTEGER DEFAULT 30,

    -- Upload Status
    uploaded BOOLEAN DEFAULT FALSE,
    upload_url TEXT,
    upload_date TIMESTAMP,
    upload_attempts INTEGER DEFAULT 0,

    -- Processing Status
    processed BOOLEAN DEFAULT FALSE,
    passenger_events_extracted BOOLEAN DEFAULT FALSE,

    -- Storage
    storage_provider VARCHAR(50) DEFAULT 's3',
    storage_bucket VARCHAR(255),
    storage_key TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_footage_vehicle ON footage_records(vehicle_id);
CREATE INDEX idx_footage_trip ON footage_records(trip_id);
CREATE INDEX idx_footage_uploaded ON footage_records(uploaded);
```

#### 7. Device Status Table
```sql
CREATE TABLE device_status (
    status_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID REFERENCES vehicles(vehicle_id) NOT NULL,
    device_id VARCHAR(255) NOT NULL,

    -- Status Information
    status VARCHAR(20) DEFAULT 'online',
    last_heartbeat TIMESTAMP DEFAULT NOW(),

    -- System Information
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(5,2),
    disk_usage DECIMAL(5,2),
    temperature DECIMAL(5,2),

    -- Network Information
    ip_address INET,
    network_quality INTEGER,

    -- Software Information
    software_version VARCHAR(50),
    last_update TIMESTAMP,

    -- Camera Status
    camera_status VARCHAR(20) DEFAULT 'connected',
    camera_fps DECIMAL(5,2),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_device_status_vehicle ON device_status(vehicle_id);
CREATE INDEX idx_device_status_device ON device_status(device_id);
CREATE INDEX idx_device_status_heartbeat ON device_status(last_heartbeat);
```

## API Endpoints

### 1. Fleet Management API

#### GET /api/v1/fleets
Get list of fleets
```json
{
  "fleets": [
    {
      "fleet_id": "uuid",
      "name": "City Taxi Fleet",
      "company_name": "City Transport Ltd",
      "vehicle_count": 25,
      "active_vehicles": 23,
      "total_trips_today": 156,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 50
}
```

#### POST /api/v1/fleets
Create new fleet
```json
{
  "name": "New Fleet",
  "company_name": "Transport Company",
  "contact_email": "contact@company.com",
  "contact_phone": "+27123456789",
  "address": "123 Main St, Cape Town"
}
```

### 2. Vehicle Management API

#### GET /api/v1/vehicles
Get list of vehicles
```json
{
  "vehicles": [
    {
      "vehicle_id": "uuid",
      "registration_number": "HDJ864L",
      "fleet_id": "uuid",
      "make": "Toyota",
      "model": "Quantum",
      "status": "active",
      "current_trip_id": "uuid",
      "passenger_count": 8,
      "location": {
        "latitude": -33.9249,
        "longitude": 18.4241
      },
      "last_update": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### POST /api/v1/vehicles
Register new vehicle
```json
{
  "fleet_id": "uuid",
  "registration_number": "HDJ864L",
  "make": "Toyota",
  "model": "Quantum",
  "year": 2020,
  "color": "White",
  "capacity": 14,
  "device_id": "rpi_HDJ864L_001",
  "camera_config": {
    "type": "ip_camera",
    "url": "rtsp://192.168.1.100:554/stream1",
    "username": "admin",
    "password": "password123"
  }
}
```

#### PUT /api/v1/vehicles/{vehicle_id}
Update vehicle information

#### DELETE /api/v1/vehicles/{vehicle_id}
Deactivate vehicle

### 3. Trip Management API

#### POST /api/v1/trips/start
Start new trip
```json
{
  "vehicle_id": "uuid",
  "driver_id": "uuid",
  "route": "Route 1",
  "start_location": {
    "latitude": -33.9249,
    "longitude": 18.4241
  }
}
```

#### POST /api/v1/trips/{trip_id}/stop
Stop active trip
```json
{
  "end_location": {
    "latitude": -33.9249,
    "longitude": 18.4241
  },
  "final_passenger_count": 0
}
```

#### GET /api/v1/trips/{trip_id}
Get trip details
```json
{
  "trip_id": "uuid",
  "vehicle_id": "uuid",
  "registration_number": "HDJ864L",
  "driver_id": "uuid",
  "start_time": "2024-01-01T08:00:00Z",
  "end_time": "2024-01-01T09:30:00Z",
  "duration_seconds": 5400,
  "passenger_data": {
    "max_passenger_count": 12,
    "total_entries": 15,
    "total_exits": 15,
    "overload_events": 1
  },
  "events": [
    {
      "event_type": "passenger_entry",
      "timestamp": "2024-01-01T08:05:00Z",
      "passenger_count": 1,
      "location": {
        "latitude": -33.9249,
        "longitude": 18.4241
      }
    }
  ]
}
```

### 4. Footage Management API

#### GET /api/v1/footage
Get list of footage records
```json
{
  "footage": [
    {
      "footage_id": "uuid",
      "vehicle_id": "uuid",
      "registration_number": "HDJ864L",
      "trip_id": "uuid",
      "filename": "HDJ864L_trip_20240101_080000.mp4",
      "duration_seconds": 5400,
      "file_size": 1073741824,
      "resolution": "1920x1080",
      "start_time": "2024-01-01T08:00:00Z",
      "end_time": "2024-01-01T09:30:00Z",
      "uploaded": true,
      "upload_date": "2024-01-01T10:00:00Z",
      "download_url": "https://api.example.com/footage/uuid/download"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 50
}
```

#### POST /api/v1/footage/upload
Upload footage file
```json
{
  "vehicle_id": "uuid",
  "trip_id": "uuid",
  "filename": "HDJ864L_trip_20240101_080000.mp4",
  "duration_seconds": 5400,
  "file_size": 1073741824,
  "resolution": "1920x1080",
  "start_time": "2024-01-01T08:00:00Z",
  "end_time": "2024-01-01T09:30:00Z",
  "checksum": "sha256_hash"
}
```

#### GET /api/v1/footage/{footage_id}/download
Download footage file (returns signed URL or direct download)

#### DELETE /api/v1/footage/{footage_id}
Delete footage record and file

#### GET /api/v1/footage/{vehicle_id}/live
Get live footage stream for specific vehicle
```json
{
  "vehicle_id": "uuid",
  "registration_number": "HDJ864L",
  "stream_url": "https://api.example.com/stream/HDJ864L/live.m3u8",
  "websocket_url": "wss://api.example.com/ws/footage/HDJ864L",
  "stream_status": "active",
  "quality_options": [
    {
      "quality": "high",
      "resolution": "1920x1080",
      "bitrate": "2000kbps",
      "url": "https://api.example.com/stream/HDJ864L/high.m3u8"
    },
    {
      "quality": "medium",
      "resolution": "1280x720",
      "bitrate": "1000kbps",
      "url": "https://api.example.com/stream/HDJ864L/medium.m3u8"
    },
    {
      "quality": "low",
      "resolution": "640x480",
      "bitrate": "500kbps",
      "url": "https://api.example.com/stream/HDJ864L/low.m3u8"
    }
  ],
  "metadata": {
    "current_trip_id": "uuid",
    "passenger_count": 8,
    "camera_status": "connected",
    "last_frame_time": "2024-01-01T12:00:00Z"
  }
}
```

#### POST /api/v1/footage/{vehicle_id}/live/start
Start live streaming for vehicle
```json
{
  "quality": "high",
  "duration_minutes": 60,
  "auto_record": true,
  "authorized_viewers": ["fleet_admin", "dispatcher"]
}
```

#### POST /api/v1/footage/{vehicle_id}/live/stop
Stop live streaming for vehicle

#### GET /api/v1/footage/live/active
Get all active live streams
```json
{
  "active_streams": [
    {
      "vehicle_id": "uuid",
      "registration_number": "HDJ864L",
      "stream_url": "https://api.example.com/stream/HDJ864L/live.m3u8",
      "viewers": 3,
      "started_at": "2024-01-01T11:30:00Z",
      "quality": "high"
    }
  ],
  "total_active": 1
}
```

### 5. Real-time Updates API

#### WebSocket: /ws/vehicle/{vehicle_id}
Real-time vehicle updates
```json
{
  "type": "passenger_count_update",
  "vehicle_id": "uuid",
  "trip_id": "uuid",
  "passenger_count": 8,
  "timestamp": "2024-01-01T12:00:00Z",
  "location": {
    "latitude": -33.9249,
    "longitude": 18.4241
  }
}
```

#### WebSocket: /ws/fleet/{fleet_id}
Real-time fleet updates

### 6. Analytics API

#### GET /api/v1/analytics/fleet/{fleet_id}/summary
Fleet analytics summary
```json
{
  "fleet_id": "uuid",
  "period": "today",
  "summary": {
    "total_trips": 156,
    "total_passengers": 1248,
    "average_passengers_per_trip": 8.0,
    "total_revenue": 12480.00,
    "overload_incidents": 5,
    "vehicle_utilization": 92.0
  },
  "vehicles": [
    {
      "vehicle_id": "uuid",
      "registration_number": "HDJ864L",
      "trips": 12,
      "passengers": 96,
      "revenue": 960.00,
      "overload_incidents": 1
    }
  ]
}
```

## Camera Configuration Guide

### Supported Camera Types

#### 1. IP Cameras (RTSP)
```yaml
camera:
  type: "rtsp_stream"
  url: "rtsp://192.168.1.100:554/stream1"
  username: "admin"
  password: "camera_password"
  width: 1920
  height: 1080
  fps: 30
```

#### 2. HTTP Streaming Cameras
```yaml
camera:
  type: "http_stream"
  url: "http://192.168.1.100:8080/video"
  username: "admin"
  password: "camera_password"
  width: 1280
  height: 720
  fps: 15
```

#### 3. USB Cameras
```yaml
camera:
  type: "usb_camera"
  device_index: 0
  width: 1280
  height: 720
  fps: 15
```

### Camera Network Configuration

#### Network Setup for Multiple Vehicles
```
Vehicle Network: 192.168.1.0/24
- Router: 192.168.1.1
- Camera: 192.168.1.100
- Raspberry Pi: 192.168.1.10
- 4G Modem: 192.168.1.1 (if using cellular)
```

#### Port Configuration
- RTSP: 554
- HTTP: 80/8080
- HTTPS: 443
- SSH (Pi): 22
- API: 8000

### Vehicle Registration Process

#### 1. Physical Installation
1. Mount dome camera in optimal position
2. Install Raspberry Pi in secure location
3. Connect camera to Pi via network/USB
4. Configure network connectivity (WiFi/4G)
5. Test camera stream and connectivity

#### 2. System Registration
```bash
# On Raspberry Pi
curl -X POST https://api.taxitrack.com/api/v1/vehicles \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_TOKEN" \
  -d '{
    "registration_number": "HDJ864L",
    "fleet_id": "fleet_uuid",
    "device_id": "rpi_HDJ864L_001",
    "camera_config": {
      "type": "rtsp_stream",
      "url": "rtsp://192.168.1.100:554/stream1",
      "username": "admin",
      "password": "password123"
    }
  }'
```

#### 3. Configuration Deployment
```bash
# Update vehicle configuration
python3 scripts/configure_vehicle.py \
  --registration HDJ864L \
  --camera-url rtsp://192.168.1.100:554/stream1 \
  --api-endpoint https://api.taxitrack.com
```

## Deployment Architecture

### Production Environment
```
┌─────────────────────────────────────────────────────────────┐
│                    Production Deployment                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   Load      │  │   API        │  │   WebSocket     │   │
│  │ Balancer    │→ │  Servers     │  │    Server       │   │
│  │ (Nginx)     │  │ (FastAPI)    │  │   (FastAPI)     │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
│         │                  │                    │         │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Database   │  │    Redis     │  │   File Storage  │   │
│  │(PostgreSQL) │  │   Cache      │  │   (AWS S3)      │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Scaling Considerations
- **Horizontal Scaling**: Multiple API server instances
- **Database Sharding**: By fleet_id for large deployments
- **CDN**: For footage delivery
- **Caching**: Redis for frequently accessed data
- **Message Queue**: For async processing (Celery + Redis)

## Security Considerations

### Authentication & Authorization
- JWT tokens with short expiration
- Role-based access control (Fleet Admin, Driver, Viewer)
- API rate limiting
- Device authentication certificates

### Data Protection
- Encryption at rest (database, file storage)
- Encryption in transit (HTTPS, WSS)
- PII data anonymization
- GDPR compliance for EU operations

### Network Security
- VPN for vehicle communication
- Firewall rules for Pi devices
- Regular security updates
- Intrusion detection

## Monitoring & Alerting

### Key Metrics
- Vehicle online status
- Trip completion rates
- Passenger count accuracy
- System performance metrics
- Storage usage

### Alerts
- Vehicle offline > 5 minutes
- Camera connection lost
- Storage capacity > 80%
- Overload incidents
- System errors

This comprehensive backend architecture provides a scalable, secure foundation for managing multiple taxi vehicles with passenger counting capabilities.
```
