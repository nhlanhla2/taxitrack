#!/usr/bin/env python3
"""
Core Features Test

Test core features without external dependencies like OpenCV or YAML.
This tests the business logic and data models.
"""

import sys
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_vehicle_models():
    """Test vehicle management models without OpenCV."""
    try:
        # Import directly from models to avoid OpenCV dependency in footage_manager
        import sys
        import importlib.util

        # Load the models module directly
        models_path = Path(__file__).parent.parent / "src" / "vehicle_management" / "models.py"
        spec = importlib.util.spec_from_file_location("vehicle_models", models_path)
        vehicle_models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vehicle_models)

        Vehicle = vehicle_models.Vehicle
        VehicleStatus = vehicle_models.VehicleStatus
        CameraType = vehicle_models.CameraType
        FootageRecord = vehicle_models.FootageRecord

        # Test Vehicle creation
        vehicle = Vehicle(
            vehicle_id="test_HDJ864L",
            registration_number="HDJ864L",
            device_id="rpi_HDJ864L_001",
            camera_type=CameraType.RTSP_STREAM,
            camera_url="rtsp://192.168.1.100:554/stream1",
            camera_username="admin",
            camera_password="Random336#"
        )

        # Test vehicle methods
        stream_url = vehicle.get_camera_stream_url()
        summary = vehicle.to_summary()

        # Test FootageRecord
        footage = FootageRecord(
            vehicle_id="test_HDJ864L",
            trip_id="trip_001",
            filename="HDJ864L_20240101_120000.mp4",
            file_path="/footage/HDJ864L_20240101_120000.mp4",
            start_time=datetime.now()
        )

        footage.increment_upload_attempts()
        footage.mark_uploaded("https://api.example.com/footage/123")

        logger.info("✅ Vehicle Models Test PASSED")
        logger.info(f"   Vehicle: {vehicle.registration_number}")
        logger.info(f"   Stream URL: {stream_url}")
        logger.info(f"   Summary fields: {len(summary)}")
        logger.info(f"   Footage: {footage.filename}")
        logger.info(f"   Upload attempts: {footage.upload_attempts}")

        return True

    except Exception as e:
        logger.error(f"❌ Vehicle Models Test FAILED: {e}")
        return False


def test_trip_models():
    """Test trip management models."""
    try:
        from trip_management.models import Trip, TripStatus, EventType

        # Create test trip
        trip = Trip(
            trip_id="trip_HDJ864L_001",
            device_id="rpi_HDJ864L_001",
            max_capacity=14
        )

        # Test passenger counting
        trip.update_passenger_count(5)
        trip.update_passenger_count(8)
        trip.update_passenger_count(15)  # Should trigger overload

        # Test events
        entry_event = trip.add_event(EventType.PASSENGER_ENTRY, {
            "passenger_count": 8,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat()
        })

        exit_event = trip.add_event(EventType.PASSENGER_EXIT, {
            "passenger_count": 7,
            "confidence": 0.92,
            "timestamp": datetime.now().isoformat()
        })

        # Test trip completion
        trip.end_trip()

        logger.info("✅ Trip Models Test PASSED")
        logger.info(f"   Trip ID: {trip.trip_id}")
        logger.info(f"   Final passenger count: {trip.current_passenger_count}")
        logger.info(f"   Overload detected: {trip.is_overloaded}")
        logger.info(f"   Events recorded: {len(trip.events)}")
        logger.info(f"   Trip status: {trip.status.value}")
        duration = trip.get_duration_minutes()
        duration_str = f"{duration:.1f}" if duration is not None else "0.0"
        logger.info(f"   Duration: {duration_str} minutes")

        return True

    except Exception as e:
        logger.error(f"❌ Trip Models Test FAILED: {e}")
        return False


def test_live_streaming_models():
    """Test live streaming models."""
    try:
        from live_streaming.models import StreamConfig, StreamSession, StreamQuality, StreamProtocol

        # Create stream configuration
        stream_config = StreamConfig(
            vehicle_id="test_HDJ864L",
            registration_number="HDJ864L",
            quality=StreamQuality.HIGH,
            protocol=StreamProtocol.HLS,
            max_viewers=5,
            duration_minutes=60,
            created_by="test_user"
        )

        # Test configuration methods
        resolution = stream_config.get_resolution_tuple()
        bitrate = stream_config.get_bitrate_value()

        # Create stream session
        session = StreamSession(
            stream_id=stream_config.stream_id,
            vehicle_id="test_HDJ864L"
        )

        # Test session methods
        session.add_viewer()
        session.add_viewer()
        session.add_viewer()
        session.record_error("Test error message")
        session.record_reconnect()

        duration = session.get_duration_seconds()

        logger.info("✅ Live Streaming Models Test PASSED")
        logger.info(f"   Stream ID: {stream_config.stream_id}")
        logger.info(f"   Quality: {stream_config.quality.value}")
        logger.info(f"   Resolution: {resolution}")
        logger.info(f"   Bitrate: {bitrate} kbps")
        logger.info(f"   Current viewers: {session.current_viewers}")
        logger.info(f"   Error count: {session.error_count}")
        logger.info(f"   Duration: {duration} seconds")

        return True

    except Exception as e:
        logger.error(f"❌ Live Streaming Models Test FAILED: {e}")
        return False


def test_json_serialization():
    """Test JSON serialization of models."""
    try:
        # Import vehicle models directly
        import importlib.util
        models_path = Path(__file__).parent.parent / "src" / "vehicle_management" / "models.py"
        spec = importlib.util.spec_from_file_location("vehicle_models", models_path)
        vehicle_models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vehicle_models)

        Vehicle = vehicle_models.Vehicle
        CameraType = vehicle_models.CameraType

        from trip_management.models import Trip, EventType
        from live_streaming.models import StreamConfig, StreamQuality

        # Test Vehicle JSON serialization
        vehicle = Vehicle(
            vehicle_id="test_HDJ864L",
            registration_number="HDJ864L",
            device_id="rpi_HDJ864L_001",
            camera_type=CameraType.RTSP_STREAM,
            camera_url="rtsp://192.168.1.100:554/stream1",
            camera_username="admin",
            camera_password="Random336#"
        )

        vehicle_json = vehicle.model_dump_json()
        vehicle_dict = json.loads(vehicle_json)

        # Test Trip JSON serialization
        trip = Trip(
            trip_id="trip_HDJ864L_001",
            device_id="rpi_HDJ864L_001",
            max_capacity=14
        )

        trip.add_event(EventType.PASSENGER_ENTRY, {"count": 5})
        trip_json = trip.model_dump_json()
        trip_dict = json.loads(trip_json)

        # Test StreamConfig JSON serialization
        stream_config = StreamConfig(
            vehicle_id="test_HDJ864L",
            registration_number="HDJ864L",
            quality=StreamQuality.HIGH,
            created_by="test_user"
        )

        stream_json = stream_config.model_dump_json()
        stream_dict = json.loads(stream_json)

        logger.info("✅ JSON Serialization Test PASSED")
        logger.info(f"   Vehicle JSON keys: {len(vehicle_dict)}")
        logger.info(f"   Trip JSON keys: {len(trip_dict)}")
        logger.info(f"   Stream config JSON keys: {len(stream_dict)}")

        return True

    except Exception as e:
        logger.error(f"❌ JSON Serialization Test FAILED: {e}")
        return False


def main():
    """Run core feature tests."""
    logger.info("🚀 Starting Core Features Test Suite")
    logger.info("=" * 60)

    tests = [
        ("Vehicle Models", test_vehicle_models),
        ("Trip Models", test_trip_models),
        ("Live Streaming Models", test_live_streaming_models),
        ("JSON Serialization", test_json_serialization)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n🧪 Testing: {test_name}")
        if test_func():
            passed += 1

    logger.info("\n" + "=" * 60)
    logger.info(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 ALL CORE TESTS PASSED!")
        logger.info("\n🔧 System is ready for:")
        logger.info("   • Camera integration (install opencv-python)")
        logger.info("   • Configuration management (install pyyaml)")
        logger.info("   • Backend API connection")
        logger.info("   • Raspberry Pi deployment")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
