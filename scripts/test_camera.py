#!/usr/bin/env python3
"""
Camera Test Script

Test script to verify camera connectivity and configuration for
the taxi passenger counting system.
"""

import cv2
import argparse
import logging
import time
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from computer_vision.camera_stream import CameraStream

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_camera_connection(config):
    """Test camera connection and display stream."""
    logger.info("Testing camera connection...")

    # Create camera stream
    camera = CameraStream(config)

    try:
        # Start camera
        if not camera.start():
            logger.error("Failed to start camera stream")
            return False

        logger.info("Camera started successfully")

        # Get stream info
        info = camera.get_stream_info()
        logger.info(f"Camera info: {info}")

        # Test frame capture
        frame_count = 0
        start_time = time.time()

        logger.info("Testing frame capture (press 'q' to quit)...")

        while True:
            frame = camera.get_frame(timeout=2.0)

            if frame is None:
                logger.warning("No frame received")
                continue

            frame_count += 1

            # Calculate FPS
            elapsed = time.time() - start_time
            if elapsed > 0:
                fps = frame_count / elapsed

            # Display frame info
            height, width = frame.shape[:2]
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Resolution: {width}x{height}", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Frames: {frame_count}", (10, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Press 'q' to quit", (10, 150),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Show frame
            cv2.imshow("Camera Test", frame)

            # Check for quit
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        logger.info(f"Test completed. Captured {frame_count} frames in {elapsed:.1f}s (avg FPS: {fps:.1f})")
        return True

    except Exception as e:
        logger.error(f"Camera test failed: {e}")
        return False

    finally:
        camera.stop()
        cv2.destroyAllWindows()


def test_rtsp_camera(url, username=None, password=None):
    """Test RTSP camera connection."""
    logger.info(f"Testing RTSP camera: {url}")

    # Build URL with authentication
    if username and password:
        if "://" in url:
            protocol, rest = url.split("://", 1)
            url = f"{protocol}://{username}:{password}@{rest}"

    config = {
        "type": "ip",
        "stream_url": url,
        "width": 1920,
        "height": 1080,
        "fps": 30
    }

    return test_camera_connection(config)


def test_usb_camera(device_index=0):
    """Test USB camera connection."""
    logger.info(f"Testing USB camera: device {device_index}")

    config = {
        "type": "usb",
        "usb_camera_index": device_index,
        "width": 1280,
        "height": 720,
        "fps": 15
    }

    return test_camera_connection(config)


def scan_network_cameras(network="192.168.1"):
    """Scan network for common camera IPs."""
    logger.info(f"Scanning network {network}.x for cameras...")

    common_ports = [554, 8080, 80]
    common_paths = ["/stream1", "/video", "/mjpeg", ""]

    found_cameras = []

    for i in range(1, 255):
        ip = f"{network}.{i}"

        for port in common_ports:
            for path in common_paths:
                if port == 554:
                    url = f"rtsp://{ip}:{port}{path}"
                else:
                    url = f"http://{ip}:{port}{path}"

                try:
                    # Quick test with OpenCV
                    cap = cv2.VideoCapture(url)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            logger.info(f"Found camera at: {url}")
                            found_cameras.append(url)
                    cap.release()
                except:
                    pass

    return found_cameras


def main():
    parser = argparse.ArgumentParser(description="Test camera connectivity")
    parser.add_argument("--rtsp", help="RTSP camera URL")
    parser.add_argument("--username", help="Camera username")
    parser.add_argument("--password", help="Camera password")
    parser.add_argument("--usb", type=int, default=0, help="USB camera device index")
    parser.add_argument("--scan", help="Scan network for cameras (e.g., 192.168.1)")
    parser.add_argument("--config", help="Use configuration file")

    args = parser.parse_args()

    if args.scan:
        cameras = scan_network_cameras(args.scan)
        if cameras:
            logger.info(f"Found {len(cameras)} cameras:")
            for camera in cameras:
                logger.info(f"  - {camera}")
        else:
            logger.info("No cameras found")
        return

    if args.config:
        import yaml
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)

        camera_config = config.get("camera", {})
        success = test_camera_connection(camera_config)

    elif args.rtsp:
        success = test_rtsp_camera(args.rtsp, args.username, args.password)

    else:
        success = test_usb_camera(args.usb)

    if success:
        logger.info("✓ Camera test passed!")
        sys.exit(0)
    else:
        logger.error("✗ Camera test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
