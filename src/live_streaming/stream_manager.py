"""
Stream Manager

Manages live video streaming for taxi vehicles, handling multiple
concurrent streams, viewer management, and stream quality adaptation.
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from pathlib import Path
import json

from .models import StreamConfig, StreamSession, StreamStatus, StreamQuality, ViewerSession

logger = logging.getLogger(__name__)


class StreamManager:
    """
    Manages live video streams for taxi vehicles.

    Handles stream lifecycle, viewer management, quality adaptation,
    and integration with backend streaming services.
    """

    def __init__(self, config: dict, vehicle_id: str, registration_number: str):
        """
        Initialize stream manager.

        Args:
            config: Configuration dictionary
            vehicle_id: Vehicle identifier
            registration_number: Vehicle registration number
        """
        self.config = config
        self.vehicle_id = vehicle_id
        self.registration_number = registration_number

        # Stream configuration
        self.streaming_config = config.get("live_streaming", {})
        self.base_url = self.streaming_config.get("base_url", "https://stream.taxitrack.com")
        self.rtmp_server = self.streaming_config.get("rtmp_server", "rtmp://stream.taxitrack.com/live")

        # Active streams
        self.active_streams: Dict[str, StreamSession] = {}
        self.viewers: Dict[str, ViewerSession] = {}
        self.viewer_callbacks: List[Callable] = []

        # Stream storage
        self.stream_storage_path = Path(config.get("live_streaming", {}).get("storage_path", "streams"))
        self.stream_storage_path.mkdir(parents=True, exist_ok=True)

        # Performance monitoring
        self.stats = {
            "total_streams_started": 0,
            "total_viewers": 0,
            "current_bandwidth_mbps": 0.0,
            "average_stream_duration": 0,
            "error_count": 0
        }

    async def start_stream(self, stream_config: StreamConfig) -> Optional[StreamSession]:
        """
        Start a new live stream.

        Args:
            stream_config: Stream configuration

        Returns:
            Optional[StreamSession]: Created stream session or None if failed
        """
        try:
            logger.info(f"Starting live stream for vehicle {self.registration_number}")

            # Create stream session
            session = StreamSession(
                stream_id=stream_config.stream_id,
                vehicle_id=self.vehicle_id,
                status=StreamStatus.STARTING
            )

            # Generate stream URLs
            stream_urls = self._generate_stream_urls(stream_config)
            session.stream_urls = stream_urls
            session.websocket_url = f"wss://{self.base_url}/ws/stream/{stream_config.stream_id}"

            # Store active stream
            self.active_streams[stream_config.stream_id] = session
            session.status = StreamStatus.ACTIVE

            # Update statistics
            self.stats["total_streams_started"] += 1

            logger.info(f"Live stream started successfully: {stream_config.stream_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to start live stream: {e}")
            return None

    async def stop_stream(self, stream_id: str) -> bool:
        """
        Stop an active live stream.

        Args:
            stream_id: Stream identifier

        Returns:
            bool: True if stopped successfully
        """
        try:
            if stream_id not in self.active_streams:
                logger.warning(f"Stream not found: {stream_id}")
                return False

            logger.info(f"Stopping live stream: {stream_id}")

            session = self.active_streams[stream_id]
            session.status = StreamStatus.STOPPING

            # Disconnect all viewers
            stream_viewers = [v for v in self.viewers.values() if v.stream_session_id == stream_id]
            for viewer in stream_viewers:
                await self._disconnect_viewer(viewer.viewer_id)

            # Finalize session
            session.end_time = datetime.now()
            session.status = StreamStatus.INACTIVE

            # Remove from active streams
            del self.active_streams[stream_id]

            logger.info(f"Live stream stopped successfully: {stream_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop live stream {stream_id}: {e}")
            return False

    def get_active_streams(self) -> List[StreamSession]:
        """Get list of active stream sessions."""
        return list(self.active_streams.values())

    def get_stream_status(self, stream_id: str) -> Optional[StreamSession]:
        """Get status of a specific stream."""
        return self.active_streams.get(stream_id)

    def get_viewer_count(self, stream_id: str) -> int:
        """Get current viewer count for a stream."""
        if stream_id in self.active_streams:
            return self.active_streams[stream_id].current_viewers
        return 0

    def _generate_stream_urls(self, stream_config: StreamConfig) -> Dict[str, str]:
        """Generate stream URLs for different quality levels."""
        base_url = f"{self.base_url}/stream/{stream_config.stream_id}"

        return {
            "high": f"{base_url}/high.m3u8",
            "medium": f"{base_url}/medium.m3u8",
            "low": f"{base_url}/low.m3u8",
            "websocket": f"wss://{self.base_url}/ws/stream/{stream_config.stream_id}"
        }

    async def _disconnect_viewer(self, viewer_id: str):
        """Disconnect a viewer from the stream."""
        if viewer_id in self.viewers:
            viewer = self.viewers[viewer_id]
            viewer.leave_time = datetime.now()

            # Update stream session
            if viewer.stream_session_id in self.active_streams:
                self.active_streams[viewer.stream_session_id].remove_viewer()

            del self.viewers[viewer_id]
            logger.info(f"Viewer disconnected: {viewer_id}")

    def process_frame(self, frame, stream_id: str):
        """Process a frame for streaming."""
        if stream_id in self.active_streams:
            session = self.active_streams[stream_id]
            session.frames_streamed += 1

            # Here you would send the frame to streaming components
            # This is a placeholder for actual streaming logic
            pass
