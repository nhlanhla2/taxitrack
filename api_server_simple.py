#!/usr/bin/env python3
"""
Simple API Server for Taxi Passenger Counting System (Docker Version)
This version runs without computer vision dependencies for Docker deployment.
"""

import os
import sys
import json
import yaml
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models
class PassengerCount(BaseModel):
    count: int
    timestamp: str
    vehicle_id: str

class TripData(BaseModel):
    trip_id: str
    start_time: str
    end_time: Optional[str] = None
    passenger_count: int
    vehicle_id: str

class SystemStatus(BaseModel):
    status: str
    vehicle_id: str
    camera_connected: bool
    ai_processing: bool
    last_update: str

# Initialize FastAPI app
app = FastAPI(
    title="Taxi Passenger Counting API",
    description="API for HDJ864L Taxi Passenger Counting System",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
VEHICLE_ID = os.getenv("VEHICLE_REGISTRATION", "HDJ864L")
current_passenger_count = 0
trip_data = []
system_status = {
    "status": "running",
    "vehicle_id": VEHICLE_ID,
    "camera_connected": False,  # Simulated for Docker
    "ai_processing": False,     # Simulated for Docker
    "last_update": datetime.now().isoformat()
}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Taxi Passenger Counting API for {VEHICLE_ID}",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "vehicle_id": VEHICLE_ID,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Get current system status"""
    system_status["last_update"] = datetime.now().isoformat()
    return SystemStatus(**system_status)

@app.get("/passenger-count", response_model=PassengerCount)
async def get_passenger_count():
    """Get current passenger count"""
    return PassengerCount(
        count=current_passenger_count,
        timestamp=datetime.now().isoformat(),
        vehicle_id=VEHICLE_ID
    )

@app.post("/passenger-count")
async def update_passenger_count(count_data: PassengerCount):
    """Update passenger count (for external updates)"""
    global current_passenger_count
    current_passenger_count = count_data.count
    logger.info(f"Passenger count updated to: {current_passenger_count}")
    return {"message": "Passenger count updated", "count": current_passenger_count}

@app.get("/trips", response_model=List[TripData])
async def get_trips():
    """Get all trip data"""
    return trip_data

@app.post("/trips")
async def create_trip(trip: TripData):
    """Create a new trip"""
    trip_data.append(trip)
    logger.info(f"New trip created: {trip.trip_id}")
    return {"message": "Trip created", "trip_id": trip.trip_id}

@app.get("/config")
async def get_config():
    """Get system configuration"""
    config_path = Path("config/HDJ864L_live.yaml")
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"Error reading config: {e}")
            raise HTTPException(status_code=500, detail="Error reading configuration")
    else:
        return {
            "vehicle": {
                "registration": VEHICLE_ID,
                "type": "taxi"
            },
            "camera": {
                "ip": os.getenv("CAMERA_IP", "192.168.8.200"),
                "type": "ip",
                "stream_url": f"rtsp://{os.getenv('CAMERA_USERNAME', 'admin')}:{os.getenv('CAMERA_PASSWORD', 'Random336%23')}@{os.getenv('CAMERA_IP', '192.168.8.200')}:554/stream1"
            },
            "processing": {
                "model": "yolov8n.pt",
                "confidence_threshold": 0.5
            }
        }

@app.post("/simulate/passenger-entry")
async def simulate_passenger_entry():
    """Simulate a passenger entering (for testing)"""
    global current_passenger_count
    current_passenger_count += 1
    logger.info(f"Simulated passenger entry. Count: {current_passenger_count}")
    return {
        "message": "Passenger entry simulated",
        "count": current_passenger_count,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/simulate/passenger-exit")
async def simulate_passenger_exit():
    """Simulate a passenger exiting (for testing)"""
    global current_passenger_count
    if current_passenger_count > 0:
        current_passenger_count -= 1
    logger.info(f"Simulated passenger exit. Count: {current_passenger_count}")
    return {
        "message": "Passenger exit simulated",
        "count": current_passenger_count,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/reset")
async def reset_system():
    """Reset passenger count and trip data"""
    global current_passenger_count, trip_data
    current_passenger_count = 0
    trip_data = []
    logger.info("System reset completed")
    return {
        "message": "System reset completed",
        "timestamp": datetime.now().isoformat()
    }

# Footage streaming endpoints
@app.get("/api/v1/footage/{vehicle_id}/live")
async def get_live_footage(vehicle_id: str):
    """Get live footage stream for a vehicle"""
    logger.info(f"Live footage requested for vehicle: {vehicle_id}")

    # For Docker deployment, return a placeholder response
    # In production, this would stream actual camera footage
    return JSONResponse({
        "message": f"Live footage endpoint for {vehicle_id}",
        "status": "simulated",
        "vehicle_id": vehicle_id,
        "stream_url": f"rtsp://{os.getenv('CAMERA_USERNAME', 'admin')}:{os.getenv('CAMERA_PASSWORD', 'Random336%23')}@{os.getenv('CAMERA_IP', '192.168.8.200')}:554/stream1",
        "note": "This is a simulated response. In production, this would stream live camera footage.",
        "timestamp": datetime.now().isoformat()
    })

@app.get("/api/v1/footage/{vehicle_id}/status")
async def get_footage_status(vehicle_id: str):
    """Get footage streaming status for a vehicle"""
    return {
        "vehicle_id": vehicle_id,
        "camera_connected": vehicle_id == VEHICLE_ID,  # Only true for our configured vehicle
        "streaming": vehicle_id == VEHICLE_ID,
        "resolution": "2304x1296" if vehicle_id == VEHICLE_ID else "unknown",
        "fps": 25 if vehicle_id == VEHICLE_ID else 0,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/vehicles")
async def list_vehicles():
    """List all available vehicles"""
    return {
        "vehicles": [
            {
                "id": VEHICLE_ID,
                "registration": VEHICLE_ID,
                "type": "taxi",
                "status": "active",
                "camera_connected": True,
                "last_seen": datetime.now().isoformat()
            }
        ],
        "total": 1
    }

@app.get("/mobile/vehicles")
async def mobile_list_vehicles():
    """Mobile API: List all available vehicles"""
    return {
        "vehicles": [
            {
                "vehicle_id": VEHICLE_ID,
                "registration_number": VEHICLE_ID,
                "type": "mini_bus_taxi",
                "status": "active",
                "location": {
                    "latitude": -33.9249,  # Cape Town coordinates
                    "longitude": 18.4241,
                    "address": "Cape Town, South Africa"
                },
                "camera": {
                    "ip": os.getenv("CAMERA_IP", "192.168.8.200"),
                    "status": "connected",
                    "stream_url": f"rtsp://{os.getenv('CAMERA_USERNAME', 'admin')}:{os.getenv('CAMERA_PASSWORD', 'Random336%23')}@{os.getenv('CAMERA_IP', '192.168.8.200')}:554/stream1"
                },
                "passenger_count": current_passenger_count,
                "capacity": 14,
                "last_update": datetime.now().isoformat(),
                "trip_status": "in_progress" if current_passenger_count > 0 else "waiting"
            }
        ],
        "total_vehicles": 1,
        "active_vehicles": 1,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/mobile/vehicle/{vehicle_id}")
async def mobile_get_vehicle(vehicle_id: str):
    """Mobile API: Get specific vehicle details"""
    if vehicle_id != VEHICLE_ID:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    return {
        "vehicle_id": VEHICLE_ID,
        "registration_number": VEHICLE_ID,
        "type": "mini_bus_taxi",
        "status": "active",
        "location": {
            "latitude": -33.9249,
            "longitude": 18.4241,
            "address": "Cape Town, South Africa"
        },
        "camera": {
            "ip": os.getenv("CAMERA_IP", "192.168.8.200"),
            "status": "connected",
            "stream_url": f"rtsp://{os.getenv('CAMERA_USERNAME', 'admin')}:{os.getenv('CAMERA_PASSWORD', 'Random336%23')}@{os.getenv('CAMERA_IP', '192.168.8.200')}:554/stream1"
        },
        "passenger_count": current_passenger_count,
        "capacity": 14,
        "current_trip": {
            "trip_id": f"trip_{VEHICLE_ID}_{datetime.now().strftime('%Y%m%d_%H%M')}",
            "start_time": datetime.now().isoformat(),
            "status": "in_progress" if current_passenger_count > 0 else "waiting",
            "passenger_count": current_passenger_count
        },
        "last_update": datetime.now().isoformat()
    }

@app.get("/mobile/vehicle/{vehicle_id}/stream/info")
async def mobile_get_stream_info(vehicle_id: str):
    """Mobile API: Get vehicle stream information"""
    if vehicle_id != VEHICLE_ID:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    return {
        "vehicle_id": vehicle_id,
        "stream_url": f"rtsp://{os.getenv('CAMERA_USERNAME', 'admin')}:{os.getenv('CAMERA_PASSWORD', 'Random336%23')}@{os.getenv('CAMERA_IP', '192.168.8.200')}:554/stream1",
        "hls_url": f"http://100.69.8.80:8000/hls/{vehicle_id}/playlist.m3u8",
        "status": "active",
        "resolution": "1920x1080",
        "fps": 30,
        "camera_ip": os.getenv("CAMERA_IP", "192.168.8.200"),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    logger.info(f"Starting Taxi API Server for vehicle: {VEHICLE_ID}")
    logger.info(f"Camera IP: {os.getenv('CAMERA_IP', '192.168.8.200')}")
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
