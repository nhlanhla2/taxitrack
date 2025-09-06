#!/usr/bin/env python3
"""
Vehicle Configuration Script

Script to configure a new vehicle in the taxi passenger counting system.
Handles vehicle registration, camera setup, and system configuration.
"""

import argparse
import yaml
import json
import logging
import sys
import uuid
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_vehicle_config(registration_number, camera_url, camera_username=None,
                         camera_password=None, fleet_id=None, **kwargs):
    """Create vehicle configuration."""

    # Generate unique device ID
    device_id = f"rpi_{registration_number.lower()}_{uuid.uuid4().hex[:8]}"

    config = {
        "vehicle": {
            "registration_number": registration_number.upper(),
            "fleet_id": fleet_id or "default_fleet",
            "make": kwargs.get("make", ""),
            "model": kwargs.get("model", ""),
            "year": kwargs.get("year"),
            "color": kwargs.get("color", ""),
            "capacity": kwargs.get("capacity", 14),
            "route": kwargs.get("route", "")
        },
        "camera": {
            "type": "rtsp_stream" if camera_url.startswith("rtsp://") else "http_stream",
            "stream_url": camera_url,
            "username": camera_username,
            "password": camera_password,
            "width": kwargs.get("width", 1920),
            "height": kwargs.get("height", 1080),
            "fps": kwargs.get("fps", 30),
            "timeout": 30,
            "reconnect_attempts": 5,
            "reconnect_delay": 5
        },
        "computer_vision": {
            "detection_model": "yolov8n.pt",
            "confidence_threshold": 0.5,
            "nms_threshold": 0.4,
            "roi": [0.0, 0.0, 1.0, 1.0],
            "entry_zone": [0.0, 0.0, 0.5, 1.0],
            "exit_zone": [0.5, 0.0, 1.0, 1.0]
        },
        "face_tracking": {
            "model": "hog",
            "tolerance": 0.6,
            "max_tracking_time": 10,
            "min_face_size": 50
        },
        "trip": {
            "max_capacity": kwargs.get("capacity", 14),
            "timeout_minutes": 120,
            "min_duration": 60
        },
        "footage": {
            "record_during_trips": True,
            "storage_path": "footage",
            "max_storage_gb": 50,
            "retention_days": 30,
            "quality": "high",
            "fps": 15,
            "auto_upload": True,
            "upload_on_trip_end": True
        },
        "backend": {
            "base_url": kwargs.get("api_endpoint", "https://api.taxitrack.com"),
            "endpoints": {
                "trip_start": "/api/v1/trips/start",
                "trip_stop": "/api/v1/trips/stop",
                "trip_update": "/api/v1/trips/update",
                "footage_upload": "/api/v1/footage/upload",
                "vehicle_register": "/api/v1/vehicles",
                "health_check": "/api/v1/health"
            },
            "api_key": kwargs.get("api_key", ""),
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 5,
            "update_interval": 30
        },
        "system": {
            "device_id": device_id,
            "location": {
                "city": kwargs.get("city", ""),
                "route": kwargs.get("route", "")
            },
            "max_cpu_usage": 80,
            "max_memory_usage": 80,
            "watchdog_enabled": True,
            "watchdog_timeout": 60
        },
        "logging": {
            "level": "INFO",
            "file": "logs/taxi_counter.log",
            "max_file_size": "10MB",
            "backup_count": 5,
            "console": True,
            "format": "json"
        },
        "development": {
            "debug": False,
            "mock_camera": False,
            "mock_backend": False,
            "save_debug_images": False,
            "debug_image_path": "debug_images/"
        }
    }

    return config


def save_config(config, output_path):
    """Save configuration to file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)

    logger.info(f"Configuration saved to: {output_file}")


def register_vehicle_with_backend(config, api_endpoint, api_key):
    """Register vehicle with backend API."""
    import requests

    vehicle_data = {
        "registration_number": config["vehicle"]["registration_number"],
        "fleet_id": config["vehicle"]["fleet_id"],
        "make": config["vehicle"]["make"],
        "model": config["vehicle"]["model"],
        "year": config["vehicle"]["year"],
        "color": config["vehicle"]["color"],
        "capacity": config["vehicle"]["capacity"],
        "device_id": config["system"]["device_id"],
        "camera_config": {
            "type": config["camera"]["type"],
            "url": config["camera"]["stream_url"],
            "username": config["camera"]["username"],
            "resolution": f"{config['camera']['width']}x{config['camera']['height']}"
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.post(
            f"{api_endpoint}/api/v1/vehicles",
            json=vehicle_data,
            headers=headers,
            timeout=30
        )

        if response.status_code == 201:
            logger.info("✓ Vehicle registered successfully with backend")
            return response.json()
        else:
            logger.error(f"✗ Failed to register vehicle: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"✗ Error registering vehicle: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Configure vehicle for taxi counting system")

    # Required arguments
    parser.add_argument("--registration", required=True, help="Vehicle registration number (e.g., HDJ864L)")
    parser.add_argument("--camera-url", required=True, help="Camera stream URL")

    # Optional camera authentication
    parser.add_argument("--camera-username", help="Camera username")
    parser.add_argument("--camera-password", help="Camera password")

    # Vehicle details
    parser.add_argument("--fleet-id", help="Fleet identifier")
    parser.add_argument("--make", help="Vehicle make")
    parser.add_argument("--model", help="Vehicle model")
    parser.add_argument("--year", type=int, help="Vehicle year")
    parser.add_argument("--color", help="Vehicle color")
    parser.add_argument("--capacity", type=int, default=14, help="Vehicle capacity")
    parser.add_argument("--route", help="Vehicle route")

    # Camera settings
    parser.add_argument("--width", type=int, default=1920, help="Camera width")
    parser.add_argument("--height", type=int, default=1080, help="Camera height")
    parser.add_argument("--fps", type=int, default=30, help="Camera FPS")

    # Backend settings
    parser.add_argument("--api-endpoint", default="https://api.taxitrack.com", help="Backend API endpoint")
    parser.add_argument("--api-key", help="Backend API key")

    # Location
    parser.add_argument("--city", help="City location")

    # Output
    parser.add_argument("--output", default="config/config.yaml", help="Output configuration file")
    parser.add_argument("--register", action="store_true", help="Register vehicle with backend")

    args = parser.parse_args()

    # Create configuration
    config = create_vehicle_config(
        registration_number=args.registration,
        camera_url=args.camera_url,
        camera_username=args.camera_username,
        camera_password=args.camera_password,
        fleet_id=args.fleet_id,
        make=args.make,
        model=args.model,
        year=args.year,
        color=args.color,
        capacity=args.capacity,
        route=args.route,
        width=args.width,
        height=args.height,
        fps=args.fps,
        api_endpoint=args.api_endpoint,
        api_key=args.api_key,
        city=args.city
    )

    # Save configuration
    save_config(config, args.output)

    # Register with backend if requested
    if args.register and args.api_key:
        result = register_vehicle_with_backend(config, args.api_endpoint, args.api_key)
        if result:
            logger.info(f"Vehicle ID: {result.get('vehicle_id')}")

    logger.info("✓ Vehicle configuration completed!")
    logger.info(f"Registration: {args.registration}")
    logger.info(f"Device ID: {config['system']['device_id']}")
    logger.info(f"Camera: {args.camera_url}")
    logger.info(f"Config file: {args.output}")


if __name__ == "__main__":
    main()
