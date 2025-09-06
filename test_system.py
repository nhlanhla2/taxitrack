#!/usr/bin/env python3
"""
Test Script for Taxi Passenger Counting System

Simple test script to validate system components and integration.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported."""
    logger.info("Testing module imports...")

    try:
        from src.computer_vision import CameraStream, PersonDetector, ZoneDetector, PassengerCounter
        logger.info("✓ Computer vision modules imported successfully")

        from src.face_tracking import FaceTracker, AntiFraudManager
        logger.info("✓ Face tracking modules imported successfully")

        from src.trip_management.models import Trip, TripStatus, TripEvent
        logger.info("✓ Trip management models imported successfully")

        return True

    except ImportError as e:
        logger.error(f"✗ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error during import: {e}")
        return False

def test_configuration():
    """Test configuration loading."""
    logger.info("Testing configuration...")

    try:
        import yaml

        # Test default config creation
        from main import TaxiCounterApplication
        app = TaxiCounterApplication("nonexistent_config.yaml")

        # Verify default config has required sections
        required_sections = ["camera", "computer_vision", "face_tracking", "trip", "system"]
        for section in required_sections:
            if section not in app.config:
                logger.error(f"✗ Missing config section: {section}")
                return False

        logger.info("✓ Configuration loading works correctly")
        return True

    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False

def test_models():
    """Test data models."""
    logger.info("Testing data models...")

    try:
        from src.trip_management.models import Trip, TripStatus, EventType
        from datetime import datetime

        # Create a test trip
        trip = Trip(
            trip_id="test_001",
            device_id="test_device",
            max_capacity=14
        )

        # Test passenger count update
        trip.update_passenger_count(5)
        assert trip.current_passenger_count == 5
        assert trip.max_passenger_count == 5

        # Test overload detection
        trip.update_passenger_count(15)
        assert trip.is_overloaded == True
        assert trip.overload_events == 1

        # Test event addition
        event = trip.add_event(EventType.PASSENGER_ENTRY, {"test": "data"})
        assert len(trip.events) == 2  # overload + entry events

        logger.info("✓ Data models work correctly")
        return True

    except Exception as e:
        logger.error(f"✗ Model test failed: {e}")
        return False

async def test_basic_functionality():
    """Test basic system functionality."""
    logger.info("Testing basic functionality...")

    try:
        # Test with mock configuration
        config = {
            "camera": {
                "type": "usb",
                "usb_camera_index": 0,
                "width": 320,
                "height": 240,
                "fps": 10
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
                "max_capacity": 14
            }
        }

        # Test passenger counter initialization (without starting camera)
        from src.computer_vision import PassengerCounter
        counter = PassengerCounter(config)

        # Test basic methods
        assert counter.get_current_count() == 0
        stats = counter.get_statistics()
        assert isinstance(stats, dict)

        logger.info("✓ Basic functionality test passed")
        return True

    except Exception as e:
        logger.error(f"✗ Basic functionality test failed: {e}")
        return False

async def run_tests():
    """Run all tests."""
    logger.info("Starting Taxi Counter System Tests")
    logger.info("=" * 50)

    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_configuration),
        ("Data Models", test_models),
        ("Basic Functionality", test_basic_functionality)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\nRunning test: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()

            if result:
                passed += 1
                logger.info(f"✓ {test_name} PASSED")
            else:
                logger.error(f"✗ {test_name} FAILED")

        except Exception as e:
            logger.error(f"✗ {test_name} FAILED with exception: {e}")

    logger.info("\n" + "=" * 50)
    logger.info(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed!")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    # Create required directories
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)

    # Run tests
    success = asyncio.run(run_tests())

    if not success:
        sys.exit(1)

    logger.info("\nSystem validation complete!")
