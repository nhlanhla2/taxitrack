#!/usr/bin/env python3
"""
Basic System Test

Test basic system functionality without requiring OpenCV or camera hardware.
Validates configuration, imports, and core functionality.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_vehicle_configuration():
    """Test vehicle configuration creation."""
    logger.info("Testing vehicle configuration...")

    try:
        from vehicle_management.models import Vehicle, VehicleStatus, CameraType

        # Create test vehicle
        vehicle = Vehicle(
            vehicle_id="test_001",
            registration_number="HDJ864L",
            device_id="rpi_HDJ864L_001",
            camera_type=CameraType.RTSP_STREAM,
            camera_url="rtsp://192.168.1.100:554/stream1",
            camera_username="admin",
            camera_password="Random336#"
        )

        # Test methods
        stream_url = vehicle.get_camera_stream_url()
        summary = vehicle.to_summary()

        logger.info(f"✓ Vehicle created: {vehicle.registration_number}")
        logger.info(f"✓ Stream URL: {stream_url}")
        logger.info(f"✓ Summary generated: {len(summary)} fields")

        return True

    except Exception as e:
        logger.error(f"✗ Vehicle configuration test failed: {e}")
        return False


def test_footage_management():
    """Test footage management functionality."""
    logger.info("Testing footage management...")

    try:
        from vehicle_management.models import FootageRecord
        from datetime import datetime

        # Create test footage record
        footage = FootageRecord(
            vehicle_id="test_001",
            trip_id="trip_001",
            filename="HDJ864L_trip_20240101_080000.mp4",
            file_path="/footage/HDJ864L_trip_20240101_080000.mp4",
            start_time=datetime.now()
        )

        # Test methods
        footage.increment_upload_attempts()
        footage.mark_uploaded("https://api.example.com/footage/123")

        logger.info(f"✓ Footage record created: {footage.filename}")
        logger.info(f"✓ Upload attempts: {footage.upload_attempts}")
        logger.info(f"✓ Upload status: {footage.uploaded}")

        return True

    except Exception as e:
        logger.error(f"✗ Footage management test failed: {e}")
        return False


def test_trip_models():
    """Test trip management models."""
    logger.info("Testing trip models...")

    try:
        from trip_management.models import Trip, TripStatus, EventType

        # Create test trip
        trip = Trip(
            trip_id="trip_001",
            device_id="rpi_HDJ864L_001",
            max_capacity=14
        )

        # Test passenger count updates
        trip.update_passenger_count(5)
        trip.update_passenger_count(15)  # Should trigger overload

        # Test event addition
        event = trip.add_event(EventType.PASSENGER_ENTRY, {"test": "data"})

        logger.info(f"✓ Trip created: {trip.trip_id}")
        logger.info(f"✓ Passenger count: {trip.current_passenger_count}")
        logger.info(f"✓ Overload detected: {trip.is_overloaded}")
        logger.info(f"✓ Events: {len(trip.events)}")

        return True

    except Exception as e:
        logger.error(f"✗ Trip models test failed: {e}")
        return False


def test_configuration_script():
    """Test vehicle configuration script."""
    logger.info("Testing configuration script...")

    try:
        # Import the configuration function
        sys.path.append(str(Path(__file__).parent))
        from configure_vehicle import create_vehicle_config

        # Create test configuration
        config = create_vehicle_config(
            registration_number="HDJ864L",
            camera_url="rtsp://192.168.1.100:554/stream1",
            camera_username="admin",
            camera_password="password123",
            fleet_id="test_fleet",
            make="Toyota",
            model="Quantum",
            capacity=14
        )

        # Validate configuration structure
        required_sections = ["vehicle", "camera", "computer_vision", "face_tracking",
                           "trip", "footage", "backend", "system"]

        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing configuration section: {section}")

        logger.info(f"✓ Configuration created for: {config['vehicle']['registration_number']}")
        logger.info(f"✓ Device ID: {config['system']['device_id']}")
        logger.info(f"✓ All required sections present")

        return True

    except Exception as e:
        logger.error(f"✗ Configuration script test failed: {e}")
        return False


def main():
    """Run all basic system tests."""
    logger.info("Starting Basic System Tests")
    logger.info("=" * 50)

    tests = [
        ("Vehicle Configuration", test_vehicle_configuration),
        ("Footage Management", test_footage_management),
        ("Trip Models", test_trip_models),
        ("Configuration Script", test_configuration_script)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\nRunning test: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✓ {test_name} PASSED")
            else:
                logger.error(f"✗ {test_name} FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} FAILED with exception: {e}")

    logger.info("\n" + "=" * 50)
    logger.info(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All basic tests passed!")
        logger.info("\nNext steps:")
        logger.info("1. Install OpenCV: pip install opencv-python")
        logger.info("2. Test camera: python3 scripts/test_camera.py --usb 0")
        logger.info("3. Configure vehicle: python3 scripts/configure_vehicle.py --help")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
