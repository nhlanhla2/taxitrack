"""
Live Streaming API Endpoints

FastAPI endpoints for managing live video streams from taxi vehicles.
Provides REST API and WebSocket endpoints for real-time streaming.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
import asyncio
import json
import logging
from datetime import datetime

from ..live_streaming.models import StreamConfig, StreamSession, StreamQuality, StreamProtocol
from ..live_streaming.stream_manager import StreamManager
from ..vehicle_management.models import Vehicle

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Global stream managers (in production, this would be managed differently)
stream_managers: Dict[str, StreamManager] = {}

app = FastAPI(title="Taxi Live Streaming API", version="1.0.0")


class ConnectionManager:
    """Manages WebSocket connections for live streaming."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, stream_id: str):
        """Connect a WebSocket to a stream."""
        await websocket.accept()
        if stream_id not in self.active_connections:
            self.active_connections[stream_id] = []
        self.active_connections[stream_id].append(websocket)

    def disconnect(self, websocket: WebSocket, stream_id: str):
        """Disconnect a WebSocket from a stream."""
        if stream_id in self.active_connections:
            if websocket in self.active_connections[stream_id]:
                self.active_connections[stream_id].remove(websocket)

    async def send_to_stream(self, stream_id: str, message: dict):
        """Send message to all connections for a stream."""
        if stream_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[stream_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.append(connection)

            # Remove disconnected connections
            for conn in disconnected:
                self.active_connections[stream_id].remove(conn)


manager = ConnectionManager()


@app.get("/api/v1/footage/{vehicle_id}/live")
async def get_live_stream_info(
    vehicle_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get live stream information for a specific vehicle.

    Args:
        vehicle_id: Vehicle identifier
        credentials: Authentication credentials

    Returns:
        Live stream information including URLs and metadata
    """
    try:
        # Verify vehicle exists and user has access
        # This would typically check against a database

        if vehicle_id not in stream_managers:
            raise HTTPException(status_code=404, detail="Vehicle not found or not streaming")

        stream_manager = stream_managers[vehicle_id]
        active_streams = stream_manager.get_active_streams()

        if not active_streams:
            return JSONResponse({
                "vehicle_id": vehicle_id,
                "stream_status": "inactive",
                "message": "No active streams for this vehicle"
            })

        # Get the most recent active stream
        stream_session = active_streams[0]

        return {
            "vehicle_id": vehicle_id,
            "registration_number": stream_manager.registration_number,
            "stream_id": stream_session.stream_id,
            "stream_status": stream_session.status.value,
            "stream_urls": stream_session.stream_urls,
            "websocket_url": stream_session.websocket_url,
            "quality_options": [
                {
                    "quality": "high",
                    "resolution": "1920x1080",
                    "bitrate": "2000kbps",
                    "url": stream_session.stream_urls.get("high")
                },
                {
                    "quality": "medium",
                    "resolution": "1280x720",
                    "bitrate": "1000kbps",
                    "url": stream_session.stream_urls.get("medium")
                },
                {
                    "quality": "low",
                    "resolution": "640x480",
                    "bitrate": "500kbps",
                    "url": stream_session.stream_urls.get("low")
                }
            ],
            "metadata": {
                "current_viewers": stream_session.current_viewers,
                "start_time": stream_session.start_time.isoformat(),
                "duration_seconds": stream_session.get_duration_seconds(),
                "frames_streamed": stream_session.frames_streamed
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting live stream info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/footage/{vehicle_id}/live/start")
async def start_live_stream(
    vehicle_id: str,
    stream_request: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Start live streaming for a vehicle.

    Args:
        vehicle_id: Vehicle identifier
        stream_request: Stream configuration request
        credentials: Authentication credentials

    Returns:
        Started stream session information
    """
    try:
        # Verify permissions
        # This would check if user can start streams for this vehicle

        if vehicle_id not in stream_managers:
            raise HTTPException(status_code=404, detail="Vehicle not found")

        stream_manager = stream_managers[vehicle_id]

        # Check if already streaming
        active_streams = stream_manager.get_active_streams()
        if active_streams:
            raise HTTPException(status_code=409, detail="Stream already active for this vehicle")

        # Create stream configuration
        stream_config = StreamConfig(
            vehicle_id=vehicle_id,
            registration_number=stream_manager.registration_number,
            quality=StreamQuality(stream_request.get("quality", "medium")),
            protocol=StreamProtocol(stream_request.get("protocol", "hls")),
            duration_minutes=stream_request.get("duration_minutes"),
            max_viewers=stream_request.get("max_viewers", 10),
            authorized_viewers=stream_request.get("authorized_viewers", []),
            auto_record=stream_request.get("auto_record", True),
            created_by=credentials.credentials  # In practice, extract user ID from token
        )

        # Start the stream
        session = await stream_manager.start_stream(stream_config)
        if not session:
            raise HTTPException(status_code=500, detail="Failed to start stream")

        return {
            "stream_id": session.stream_id,
            "vehicle_id": vehicle_id,
            "status": session.status.value,
            "stream_urls": session.stream_urls,
            "websocket_url": session.websocket_url,
            "started_at": session.start_time.isoformat(),
            "message": "Live stream started successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting live stream: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/footage/{vehicle_id}/live/stop")
async def stop_live_stream(
    vehicle_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Stop live streaming for a vehicle.

    Args:
        vehicle_id: Vehicle identifier
        credentials: Authentication credentials

    Returns:
        Stream stop confirmation
    """
    try:
        if vehicle_id not in stream_managers:
            raise HTTPException(status_code=404, detail="Vehicle not found")

        stream_manager = stream_managers[vehicle_id]
        active_streams = stream_manager.get_active_streams()

        if not active_streams:
            raise HTTPException(status_code=404, detail="No active stream for this vehicle")

        # Stop the most recent stream
        stream_session = active_streams[0]
        success = await stream_manager.stop_stream(stream_session.stream_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to stop stream")

        return {
            "stream_id": stream_session.stream_id,
            "vehicle_id": vehicle_id,
            "status": "stopped",
            "stopped_at": datetime.now().isoformat(),
            "message": "Live stream stopped successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping live stream: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/footage/live/active")
async def get_active_streams(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get all active live streams.

    Args:
        credentials: Authentication credentials

    Returns:
        List of active streams across all vehicles
    """
    try:
        active_streams = []

        for vehicle_id, stream_manager in stream_managers.items():
            streams = stream_manager.get_active_streams()
            for stream in streams:
                active_streams.append({
                    "vehicle_id": vehicle_id,
                    "registration_number": stream_manager.registration_number,
                    "stream_id": stream.stream_id,
                    "status": stream.status.value,
                    "viewers": stream.current_viewers,
                    "started_at": stream.start_time.isoformat(),
                    "duration_seconds": stream.get_duration_seconds(),
                    "stream_urls": stream.stream_urls
                })

        return {
            "active_streams": active_streams,
            "total_active": len(active_streams),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting active streams: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.websocket("/ws/stream/{stream_id}")
async def websocket_stream_endpoint(websocket: WebSocket, stream_id: str):
    """
    WebSocket endpoint for real-time stream metadata.

    Args:
        websocket: WebSocket connection
        stream_id: Stream identifier
    """
    await manager.connect(websocket, stream_id)

    try:
        while True:
            # Send periodic updates about the stream
            message = {
                "type": "stream_update",
                "stream_id": stream_id,
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "status": "active",
                    "viewers": len(manager.active_connections.get(stream_id, [])),
                    "uptime_seconds": 0  # Calculate actual uptime
                }
            }

            await websocket.send_text(json.dumps(message))
            await asyncio.sleep(5)  # Send updates every 5 seconds

    except WebSocketDisconnect:
        manager.disconnect(websocket, stream_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, stream_id)
