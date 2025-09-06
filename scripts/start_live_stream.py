#!/usr/bin/env python3
"""
Start Live Stream

Start live streaming for the camera at 192.168.8.200
"""

import cv2
import sys
import logging
import time
import threading
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from live_streaming.models import StreamConfig, StreamSession, StreamQuality
from live_streaming.stream_manager import StreamManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LiveStreamDemo:
    """Live streaming demonstration for the taxi camera."""
    
    def __init__(self):
        self.camera_url = "rtsp://admin:Random336%23@192.168.8.200:554/stream1"
        self.running = False
        self.frame_count = 0
        self.viewer_count = 0
        
        # Configuration
        self.config = {
            "live_streaming": {
                "base_url": "http://localhost:8000",
                "rtmp_server": "rtmp://localhost/live",
                "storage_path": "streams"
            }
        }
        
        # Create stream manager
        self.stream_manager = StreamManager(
            config=self.config,
            vehicle_id="HDJ864L_001",
            registration_number="HDJ864L"
        )
        
    def test_camera_connection(self):
        """Test camera connection."""
        logger.info("🎥 Testing camera connection...")
        
        try:
            cap = cv2.VideoCapture(self.camera_url)
            
            if not cap.isOpened():
                logger.error("❌ Failed to open camera stream")
                return False
            
            # Get camera properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"✅ Camera connected successfully!")
            logger.info(f"   Resolution: {width}x{height}")
            logger.info(f"   FPS: {fps}")
            
            # Test frame reading
            ret, frame = cap.read()
            if ret and frame is not None:
                logger.info(f"   Frame shape: {frame.shape}")
                logger.info("✅ Frame reading successful!")
            else:
                logger.warning("⚠️ Could not read frame")
            
            cap.release()
            return True
            
        except Exception as e:
            logger.error(f"❌ Camera test failed: {e}")
            return False
    
    def start_streaming_simulation(self):
        """Start streaming simulation."""
        logger.info("🚀 Starting live streaming simulation...")
        
        # Create stream configuration
        stream_config = StreamConfig(
            vehicle_id="HDJ864L_001",
            registration_number="HDJ864L",
            quality=StreamQuality.HIGH,
            max_viewers=5,
            duration_minutes=60,
            created_by="demo_user"
        )
        
        logger.info(f"Stream Configuration:")
        logger.info(f"   Stream ID: {stream_config.stream_id}")
        logger.info(f"   Quality: {stream_config.quality.value}")
        logger.info(f"   Resolution: {stream_config.resolution}")
        logger.info(f"   Bitrate: {stream_config.bitrate}")
        
        # Start stream session
        session = StreamSession(
            stream_id=stream_config.stream_id,
            vehicle_id="HDJ864L_001"
        )
        
        # Generate stream URLs
        session.stream_urls = {
            "high": f"http://localhost:8000/stream/{stream_config.stream_id}/high.m3u8",
            "medium": f"http://localhost:8000/stream/{stream_config.stream_id}/medium.m3u8",
            "low": f"http://localhost:8000/stream/{stream_config.stream_id}/low.m3u8"
        }
        session.websocket_url = f"ws://localhost:8000/ws/stream/{stream_config.stream_id}"
        
        logger.info("📡 Stream URLs generated:")
        for quality, url in session.stream_urls.items():
            logger.info(f"   {quality.upper()}: {url}")
        logger.info(f"   WebSocket: {session.websocket_url}")
        
        return stream_config, session
    
    def simulate_viewers(self, session):
        """Simulate viewers joining and leaving."""
        viewers = [
            "Fleet Manager",
            "Dispatcher", 
            "Security Officer",
            "Training Supervisor",
            "Quality Control"
        ]
        
        logger.info("👥 Simulating viewers...")
        
        # Viewers joining
        for viewer in viewers:
            session.add_viewer()
            logger.info(f"   👤 {viewer} joined (Total: {session.current_viewers})")
            time.sleep(0.5)
        
        # Simulate streaming activity
        logger.info("📹 Streaming activity simulation...")
        for minute in range(1, 4):
            session.frames_streamed += 1800  # 30 fps * 60 seconds
            session.bytes_streamed += 15000000  # ~15MB per minute
            
            if minute == 2:
                session.record_error("Network hiccup")
                session.record_reconnect()
                logger.info(f"   ⚠️ Minute {minute}: Network reconnection")
            else:
                logger.info(f"   📊 Minute {minute}: Streaming normally")
            
            time.sleep(1)
        
        # Viewers leaving
        logger.info("👋 Viewers leaving...")
        while session.current_viewers > 0:
            session.remove_viewer()
            logger.info(f"   👤 Viewer left (Remaining: {session.current_viewers})")
            time.sleep(0.3)
        
        return session
    
    def display_statistics(self, session):
        """Display streaming statistics."""
        logger.info("📊 STREAMING STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Duration: {session.get_duration_seconds()} seconds")
        logger.info(f"Frames Streamed: {session.frames_streamed:,}")
        logger.info(f"Data Streamed: {session.bytes_streamed / 1024 / 1024:.1f} MB")
        logger.info(f"Max Concurrent Viewers: {session.max_viewers_reached}")
        logger.info(f"Total Unique Viewers: {session.total_viewers}")
        logger.info(f"Reconnections: {session.reconnect_count}")
        logger.info(f"Errors: {session.error_count}")
    
    def run_demo(self):
        """Run the complete live streaming demo."""
        logger.info("🚖 TAXI LIVE STREAMING DEMO - HDJ864L")
        logger.info("Camera: 192.168.8.200")
        logger.info("=" * 60)
        
        # Test camera connection
        if not self.test_camera_connection():
            logger.error("❌ Camera connection failed. Please check:")
            logger.error("   1. Camera is powered on")
            logger.error("   2. Network connectivity to 192.168.8.200")
            logger.error("   3. Credentials: admin / Random336#")
            logger.error("   4. RTSP stream path: /stream1")
            return False
        
        # Start streaming simulation
        stream_config, session = self.start_streaming_simulation()
        
        # Simulate viewers and activity
        session = self.simulate_viewers(session)
        
        # Display final statistics
        self.display_statistics(session)
        
        logger.info("\n🎉 Live streaming demo completed successfully!")
        logger.info("\n🔧 Next steps:")
        logger.info("   1. Set up streaming server (RTMP/HLS)")
        logger.info("   2. Configure backend API endpoints")
        logger.info("   3. Deploy to production environment")
        logger.info("   4. Start real passenger counting")
        
        return True


def main():
    """Main demo function."""
    demo = LiveStreamDemo()
    success = demo.run_demo()
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
