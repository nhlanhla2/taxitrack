#!/usr/bin/env python3
"""
Test Specific Camera

Test the camera at 192.168.8.200 with the provided credentials.
"""

import cv2
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_camera():
    """Test the specific camera."""
    camera_url = "rtsp://admin:Random336%23@192.168.8.200:554/stream1"
    
    logger.info(f"Testing camera: {camera_url}")
    
    try:
        # Try to open the camera
        cap = cv2.VideoCapture(camera_url)
        
        if not cap.isOpened():
            logger.error("Failed to open camera stream")
            return False
        
        logger.info("✅ Camera stream opened successfully!")
        
        # Get camera properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        logger.info(f"Camera properties:")
        logger.info(f"  Resolution: {width}x{height}")
        logger.info(f"  FPS: {fps}")
        
        # Try to read a few frames
        frame_count = 0
        for i in range(5):
            ret, frame = cap.read()
            if ret:
                frame_count += 1
                logger.info(f"  Frame {i+1}: {frame.shape if frame is not None else 'None'}")
            else:
                logger.warning(f"  Frame {i+1}: Failed to read")
        
        cap.release()
        
        if frame_count > 0:
            logger.info(f"✅ Successfully read {frame_count}/5 frames")
            return True
        else:
            logger.error("❌ Failed to read any frames")
            return False
            
    except Exception as e:
        logger.error(f"❌ Camera test failed: {e}")
        return False


def main():
    """Main test function."""
    logger.info("🎥 Testing Camera at 192.168.8.200")
    logger.info("=" * 50)
    
    success = test_camera()
    
    if success:
        logger.info("\n🎉 Camera test successful!")
        logger.info("Camera is ready for live streaming")
    else:
        logger.error("\n❌ Camera test failed!")
        logger.error("Please check camera connection and credentials")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
