#!/usr/bin/env python3
"""
Local Features Test Suite

Test all local features of the taxi passenger counting system
without requiring backend connectivity or camera hardware.
"""

import sys
import logging
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LocalFeatureTester:
    """Test suite for local features."""

    def __init__(self):
        self.test_results = {}
        self.passed_tests = 0
        self.total_tests = 0

    def run_test(self, test_name: str, test_func):
        """Run a single test and record results."""
        self.total_tests += 1
        logger.info(f"\n🧪 Testing: {test_name}")

        try:
            result = test_func()
            if result:
                self.passed_tests += 1
                self.test_results[test_name] = "PASSED"
                logger.info(f"✅ {test_name} - PASSED")
            else:
                self.test_results[test_name] = "FAILED"
                logger.error(f"❌ {test_name} - FAILED")
        except Exception as e:
            self.test_results[test_name] = f"ERROR: {str(e)}"
            logger.error(f"💥 {test_name} - ERROR: {e}")

    def test_vehicle_models(self):
        """Test vehicle management models."""
        try:
            from vehicle_management.models import Vehicle, VehicleStatus, CameraType, FootageRecord

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

            logger.info(f"   Vehicle: {vehicle.registration_number}")
            logger.info(f"   Stream URL: {stream_url}")
            logger.info(f"   Summary fields: {len(summary)}")
            logger.info(f"   Footage: {footage.filename}")
            logger.info(f"   Upload attempts: {footage.upload_attempts}")

            return True

        except Exception as e:
            logger.error(f"   Vehicle models test failed: {e}")
            return False

    def test_trip_models(self):
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

            logger.info(f"   Trip ID: {trip.trip_id}")
            logger.info(f"   Final passenger count: {trip.current_passenger_count}")
            logger.info(f"   Overload detected: {trip.is_overloaded}")
            logger.info(f"   Events recorded: {len(trip.events)}")
            logger.info(f"   Trip status: {trip.status.value}")
            logger.info(f"   Duration: {trip.get_duration_minutes()} minutes")

            return True

        except Exception as e:
            logger.error(f"   Trip models test failed: {e}")
            return False

    def test_live_streaming_models(self):
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

            logger.info(f"   Stream ID: {stream_config.stream_id}")
            logger.info(f"   Quality: {stream_config.quality.value}")
            logger.info(f"   Resolution: {resolution}")
            logger.info(f"   Bitrate: {bitrate} kbps")
            logger.info(f"   Current viewers: {session.current_viewers}")
            logger.info(f"   Error count: {session.error_count}")
            logger.info(f"   Duration: {duration} seconds")

            return True

        except Exception as e:
            logger.error(f"   Live streaming models test failed: {e}")
            return False

    def test_configuration_generation(self):
        """Test vehicle configuration generation."""
        try:
            sys.path.append(str(Path(__file__).parent))
            from configure_vehicle import create_vehicle_config

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

            # Validate configuration structure
            required_sections = [
                "vehicle", "camera", "computer_vision", "face_tracking",
                "trip", "footage", "backend", "system", "logging", "development"
            ]

            for section in required_sections:
                if section not in config:
                    raise ValueError(f"Missing configuration section: {section}")

            # Test specific values
            assert config["vehicle"]["registration_number"] == "HDJ864L"
            assert config["camera"]["stream_url"] == "rtsp://192.168.1.100:554/stream1"
            assert config["camera"]["username"] == "admin"
            assert config["vehicle"]["capacity"] == 14
            assert "rpi_HDJ864L_" in config["system"]["device_id"]

            logger.info(f"   Registration: {config['vehicle']['registration_number']}")
            logger.info(f"   Device ID: {config['system']['device_id']}")
            logger.info(f"   Camera URL: {config['camera']['stream_url']}")
            logger.info(f"   Fleet ID: {config['vehicle']['fleet_id']}")
            logger.info(f"   Configuration sections: {len(config)}")

            return True

        except Exception as e:
            logger.error(f"   Configuration generation test failed: {e}")
            return False

    def test_stream_manager(self):
        """Test stream manager functionality."""
        try:
            from live_streaming.stream_manager import StreamManager
            from live_streaming.models import StreamConfig, StreamQuality

            # Create test configuration
            test_config = {
                "live_streaming": {
                    "base_url": "https://test.stream.com",
                    "rtmp_server": "rtmp://test.stream.com/live",
                    "storage_path": "test_streams"
                }
            }

            # Create stream manager
            manager = StreamManager(
                config=test_config,
                vehicle_id="test_HDJ864L",
                registration_number="HDJ864L"
            )

            # Test stream configuration
            stream_config = StreamConfig(
                vehicle_id="test_HDJ864L",
                registration_number="HDJ864L",
                quality=StreamQuality.MEDIUM,
                created_by="test_user"
            )

            # Test manager methods (without actually starting streams)
            active_streams = manager.get_active_streams()
            viewer_count = manager.get_viewer_count("nonexistent_stream")

            logger.info(f"   Manager created for: {manager.registration_number}")
            logger.info(f"   Base URL: {manager.base_url}")
            logger.info(f"   Active streams: {len(active_streams)}")
            logger.info(f"   Storage path: {manager.stream_storage_path}")
            logger.info(f"   Stats: {manager.stats}")

            return True

        except Exception as e:
            logger.error(f"   Stream manager test failed: {e}")
            return False

    def test_json_serialization(self):
        """Test JSON serialization of models."""
        try:
            from vehicle_management.models import Vehicle, CameraType
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

            logger.info(f"   Vehicle JSON keys: {len(vehicle_dict)}")
            logger.info(f"   Trip JSON keys: {len(trip_dict)}")
            logger.info(f"   Stream config JSON keys: {len(stream_dict)}")
            logger.info(f"   All models serializable to JSON")

            return True

        except Exception as e:
            logger.error(f"   JSON serialization test failed: {e}")
            return False

    def test_file_operations(self):
        """Test file operations and path handling."""
        try:
            import tempfile
            import shutil

            # Create temporary directory for testing
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Test configuration file creation
                config_path = temp_path / "test_config.json"
                test_config = {
                    "vehicle": {
                        "registration_number": "HDJ864L",
                        "device_id": "rpi_HDJ864L_001"
                    },
                    "camera": {
                        "stream_url": "rtsp://192.168.1.100:554/stream1"
                    }
                }

                # Write configuration
                with open(config_path, 'w') as f:
                    json.dump(test_config, f, indent=2)

                # Read configuration back
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)

                # Test footage directory creation
                footage_dir = temp_path / "footage"
                footage_dir.mkdir(parents=True, exist_ok=True)

                # Test log directory creation
                logs_dir = temp_path / "logs"
                logs_dir.mkdir(parents=True, exist_ok=True)

                # Test stream directory creation
                streams_dir = temp_path / "streams"
                streams_dir.mkdir(parents=True, exist_ok=True)

                logger.info(f"   Config file created: {config_path.exists()}")
                logger.info(f"   Config loaded correctly: {loaded_config['vehicle']['registration_number']}")
                logger.info(f"   Footage directory: {footage_dir.exists()}")
                logger.info(f"   Logs directory: {logs_dir.exists()}")
                logger.info(f"   Streams directory: {streams_dir.exists()}")

                return True

        except Exception as e:
            logger.error(f"   File operations test failed: {e}")
            return False

    def run_all_tests(self):
        """Run all local feature tests."""
        logger.info("🚀 Starting Local Features Test Suite")
        logger.info("=" * 60)

        # Define all tests
        tests = [
            ("Vehicle Models", self.test_vehicle_models),
            ("Trip Models", self.test_trip_models),
            ("Live Streaming Models", self.test_live_streaming_models),
            ("Configuration Generation", self.test_configuration_generation),
            ("Stream Manager", self.test_stream_manager),
            ("JSON Serialization", self.test_json_serialization),
            ("File Operations", self.test_file_operations)
        ]

        # Run each test
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)

        for test_name, result in self.test_results.items():
            status_emoji = "✅" if result == "PASSED" else "❌"
            logger.info(f"{status_emoji} {test_name}: {result}")

        logger.info(f"\n📈 Results: {self.passed_tests}/{self.total_tests} tests passed")

        if self.passed_tests == self.total_tests:
            logger.info("🎉 ALL TESTS PASSED! System is ready for deployment.")
            logger.info("\n🔧 Next Steps:")
            logger.info("   1. Install camera dependencies: pip install opencv-python")
            logger.info("   2. Test camera connectivity: python3 scripts/test_camera.py")
            logger.info("   3. Configure your vehicle: python3 scripts/configure_vehicle.py")
            logger.info("   4. Set up backend API endpoints")
            logger.info("   5. Deploy to Raspberry Pi")
            return True
        else:
            failed_count = self.total_tests - self.passed_tests
            logger.error(f"❌ {failed_count} tests failed. Please fix issues before deployment.")
            return False


def main():
    """Main test execution function."""
    tester = LocalFeatureTester()
    success = tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
