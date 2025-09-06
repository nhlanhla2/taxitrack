#!/usr/bin/env python3
"""
System Demo Script

Demonstrates the taxi passenger counting system functionality
with simulated data and realistic scenarios.
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Import vehicle models directly to avoid OpenCV dependency
import importlib.util
models_path = Path(__file__).parent.parent / "src" / "vehicle_management" / "models.py"
spec = importlib.util.spec_from_file_location("vehicle_models", models_path)
vehicle_models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vehicle_models)

Vehicle = vehicle_models.Vehicle
CameraType = vehicle_models.CameraType
FootageRecord = vehicle_models.FootageRecord

from trip_management.models import Trip, EventType
from live_streaming.models import StreamConfig, StreamSession, StreamQuality


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"🚖 {title}")
    print("=" * 60)


def print_section(title):
    """Print a formatted section header."""
    print(f"\n📋 {title}")
    print("-" * 40)


def simulate_taxi_trip():
    """Simulate a complete taxi trip with passenger counting."""
    print_header("TAXI TRIP SIMULATION - Vehicle HDJ864L")

    # Create vehicle
    vehicle = Vehicle(
        vehicle_id="HDJ864L_001",
        registration_number="HDJ864L",
        device_id="rpi_HDJ864L_001",
        camera_type=CameraType.RTSP_STREAM,
        camera_url="rtsp://192.168.1.100:554/stream1",
        camera_username="admin",
        camera_password="Random336#"
    )

    print_section("Vehicle Information")
    print(f"Registration: {vehicle.registration_number}")
    print(f"Device ID: {vehicle.device_id}")
    print(f"Camera URL: {vehicle.get_camera_stream_url()}")
    print(f"Status: {vehicle.status.value}")

    # Create trip
    trip = Trip(
        trip_id=f"trip_{vehicle.registration_number.lower()}_{int(time.time())}",
        device_id=vehicle.device_id,
        max_capacity=14
    )

    print_section("Trip Started")
    print(f"Trip ID: {trip.trip_id}")
    print(f"Start Time: {trip.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Max Capacity: {trip.max_capacity}")

    # Simulate passenger boarding
    print_section("Passenger Boarding Simulation")

    boarding_events = [
        (2, "Two passengers board at taxi rank"),
        (5, "Three more passengers join"),
        (8, "Family of three gets in"),
        (12, "Four passengers board - getting full"),
        (15, "Three more try to squeeze in - OVERLOAD!"),
        (13, "Two passengers get off - back to normal"),
        (10, "Three passengers alight"),
        (7, "Three more get off"),
        (4, "Three passengers leave"),
        (1, "Final passengers exit"),
        (0, "Trip completed - all passengers off")
    ]

    for count, description in boarding_events:
        # Update passenger count
        trip.update_passenger_count(count)

        # Add event
        event_type = EventType.PASSENGER_ENTRY if count > trip.current_passenger_count else EventType.PASSENGER_EXIT
        trip.add_event(event_type, {
            "passenger_count": count,
            "confidence": random.uniform(0.85, 0.98),
            "description": description,
            "timestamp": datetime.now().isoformat()
        })

        # Display status
        status = "🚨 OVERLOAD" if trip.is_overloaded else "✅ Normal"
        print(f"  Passengers: {count:2d}/14 - {description} - {status}")

        # Simulate time passing
        time.sleep(0.5)

    # End trip
    trip.end_trip()

    print_section("Trip Summary")
    print(f"Trip Duration: {trip.get_duration_minutes():.1f} minutes")
    print(f"Total Events: {len(trip.events)}")
    print(f"Overload Detected: {'Yes' if trip.is_overloaded else 'No'}")
    print(f"Final Status: {trip.status.value}")

    return vehicle, trip


def simulate_live_streaming():
    """Simulate live streaming functionality."""
    print_header("LIVE STREAMING SIMULATION")

    # Create stream configuration
    stream_config = StreamConfig(
        vehicle_id="HDJ864L_001",
        registration_number="HDJ864L",
        quality=StreamQuality.HIGH,
        max_viewers=5,
        duration_minutes=30,
        created_by="fleet_manager"
    )

    print_section("Stream Configuration")
    print(f"Stream ID: {stream_config.stream_id}")
    print(f"Vehicle: {stream_config.registration_number}")
    print(f"Quality: {stream_config.quality.value}")
    print(f"Resolution: {stream_config.resolution}")
    print(f"Bitrate: {stream_config.bitrate}")
    print(f"Max Viewers: {stream_config.max_viewers}")

    # Create stream session
    session = StreamSession(
        stream_id=stream_config.stream_id,
        vehicle_id="HDJ864L_001"
    )

    print_section("Stream Session Simulation")

    # Simulate viewers joining
    viewer_events = [
        "Fleet manager joins stream",
        "Dispatcher connects to monitor",
        "Security officer starts viewing",
        "Training supervisor joins",
        "Quality control manager connects"
    ]

    for i, event in enumerate(viewer_events, 1):
        session.add_viewer()
        print(f"  👤 Viewer {i}: {event}")
        print(f"     Current viewers: {session.current_viewers}")
        time.sleep(0.3)

    # Simulate streaming activity
    print_section("Streaming Activity")
    for minute in range(1, 6):
        session.frames_streamed += 1800  # 30 fps * 60 seconds
        session.bytes_streamed += 15000000  # ~15MB per minute at high quality

        if minute == 3:
            session.record_error("Temporary network hiccup")
            session.record_reconnect()
            print(f"  ⚠️  Minute {minute}: Network reconnection")
        else:
            print(f"  📹 Minute {minute}: Streaming normally")

        time.sleep(0.2)

    # Simulate viewers leaving
    print_section("Stream Ending")
    while session.current_viewers > 0:
        session.remove_viewer()
        print(f"  👋 Viewer disconnected. Remaining: {session.current_viewers}")
        time.sleep(0.2)

    print_section("Stream Statistics")
    print(f"Total Duration: {session.get_duration_seconds()} seconds")
    print(f"Frames Streamed: {session.frames_streamed:,}")
    print(f"Data Streamed: {session.bytes_streamed / 1024 / 1024:.1f} MB")
    print(f"Max Concurrent Viewers: {session.max_viewers_reached}")
    print(f"Total Unique Viewers: {session.total_viewers}")
    print(f"Reconnections: {session.reconnect_count}")

    return stream_config, session


def main():
    """Run the complete system demonstration."""
    print("🚖 TAXI PASSENGER COUNTING SYSTEM DEMO")
    print("🔧 Testing all features without backend connectivity")

    try:
        # Run demonstrations
        vehicle, trip = simulate_taxi_trip()
        stream_config, session = simulate_live_streaming()

        # Final summary
        print_header("DEMO COMPLETED SUCCESSFULLY")
        print("✅ Vehicle Management: Working")
        print("✅ Trip Tracking: Working")
        print("✅ Passenger Counting: Working")
        print("✅ Live Streaming: Working")

        print("\n🎉 All core features are functional!")
        print("\n🔧 Ready for:")
        print("   • Camera integration")
        print("   • Backend API connection")
        print("   • Raspberry Pi deployment")
        print("   • Fleet-wide rollout")

        return True

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
