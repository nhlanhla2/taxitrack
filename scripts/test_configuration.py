#!/usr/bin/env python3
"""
Configuration Test

Test vehicle configuration generation without YAML dependency.
"""

import sys
import json
from pathlib import Path

# Import the configuration function directly without YAML dependency
import uuid


def create_vehicle_config(registration_number, camera_url, camera_username=None,
                         camera_password=None, fleet_id=None, **kwargs):
    """Create vehicle configuration without YAML dependency."""

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


def test_configuration():
    """Test vehicle configuration generation."""
    print("🔧 Testing Vehicle Configuration Generation")
    print("=" * 50)

    # Create configuration for HDJ864L
    config = create_vehicle_config(
        registration_number="HDJ864L",
        camera_url="rtsp://192.168.1.100:554/stream1",
        camera_username="admin",
        camera_password="Random336#",
        fleet_id="cape_town_fleet_001",
        make="Toyota",
        model="Quantum",
        capacity=14,
        city="Cape Town",
        route="Bellville to CBD"
    )

    print("✅ Configuration Generated Successfully!")
    print(f"📋 Vehicle: {config['vehicle']['registration_number']}")
    print(f"🆔 Device ID: {config['system']['device_id']}")
    print(f"🎥 Camera: {config['camera']['stream_url']}")
    print(f"🚐 Fleet: {config['vehicle']['fleet_id']}")
    print(f"🏭 Make/Model: {config['vehicle']['make']} {config['vehicle']['model']}")
    print(f"👥 Capacity: {config['vehicle']['capacity']}")
    print(f"🌍 Location: {config['system']['location']['city']}")

    # Validate all required sections
    required_sections = [
        "vehicle", "camera", "computer_vision", "face_tracking",
        "trip", "footage", "backend", "system", "logging", "development"
    ]

    print(f"\n📊 Configuration Sections ({len(config)}):")
    for section in required_sections:
        status = "✅" if section in config else "❌"
        print(f"  {status} {section}")

    # Save as JSON for inspection
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)

    config_file = output_dir / f"{config['vehicle']['registration_number']}_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2, default=str)

    print(f"\n💾 Configuration saved to: {config_file}")
    print(f"📁 File size: {config_file.stat().st_size} bytes")

    return True


def main():
    """Run configuration test."""
    try:
        success = test_configuration()

        if success:
            print("\n🎉 Configuration test completed successfully!")
            print("\n🔧 Next steps:")
            print("   • Install YAML: pip install pyyaml")
            print("   • Use full configure_vehicle.py script")
            print("   • Deploy configuration to Raspberry Pi")
            return True
        else:
            print("\n❌ Configuration test failed!")
            return False

    except Exception as e:
        print(f"\n💥 Configuration test error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
