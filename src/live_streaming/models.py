"""
Live Streaming Data Models

Defines data structures for live video streaming configuration,
status tracking, and viewer management.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class StreamStatus(str, Enum):
    """Live stream status enumeration."""
    INACTIVE = "inactive"
    STARTING = "starting"
    ACTIVE = "active"
    STOPPING = "stopping"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class StreamQuality(str, Enum):
    """Stream quality levels."""
    LOW = "low"          # 640x480, 500kbps
    MEDIUM = "medium"    # 1280x720, 1000kbps
    HIGH = "high"        # 1920x1080, 2000kbps
    ULTRA = "ultra"      # 3840x2160, 4000kbps


class StreamProtocol(str, Enum):
    """Streaming protocols."""
    RTMP = "rtmp"
    HLS = "hls"
    WEBRTC = "webrtc"
    MJPEG = "mjpeg"


class StreamConfig(BaseModel):
    """Live streaming configuration."""

    # Stream Identification
    stream_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique stream identifier")
    vehicle_id: str = Field(..., description="Associated vehicle ID")
    registration_number: str = Field(..., description="Vehicle registration number")

    # Stream Settings
    quality: StreamQuality = Field(default=StreamQuality.MEDIUM, description="Stream quality level")
    protocol: StreamProtocol = Field(default=StreamProtocol.HLS, description="Streaming protocol")
    max_viewers: int = Field(default=10, description="Maximum concurrent viewers")
    duration_minutes: Optional[int] = Field(None, description="Stream duration limit (None = unlimited)")

    # Technical Settings
    resolution: str = Field(default="1280x720", description="Video resolution")
    fps: int = Field(default=15, description="Frames per second")
    bitrate: str = Field(default="1000kbps", description="Video bitrate")
    audio_enabled: bool = Field(default=False, description="Enable audio streaming")

    # Security Settings
    authorized_viewers: List[str] = Field(default_factory=list, description="Authorized viewer IDs")
    require_authentication: bool = Field(default=True, description="Require viewer authentication")
    encryption_enabled: bool = Field(default=True, description="Enable stream encryption")

    # Recording Settings
    auto_record: bool = Field(default=True, description="Automatically record stream")
    record_quality: StreamQuality = Field(default=StreamQuality.HIGH, description="Recording quality")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Configuration creation time")
    created_by: str = Field(..., description="User who created the stream")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def get_resolution_tuple(self) -> tuple:
        """Get resolution as (width, height) tuple."""
        width, height = self.resolution.split('x')
        return (int(width), int(height))

    def get_bitrate_value(self) -> int:
        """Get bitrate as integer value in kbps."""
        return int(self.bitrate.replace('kbps', ''))


class StreamSession(BaseModel):
    """Active streaming session information."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique session identifier")
    stream_id: str = Field(..., description="Associated stream ID")
    vehicle_id: str = Field(..., description="Associated vehicle ID")

    # Session Status
    status: StreamStatus = Field(default=StreamStatus.INACTIVE, description="Current session status")
    start_time: datetime = Field(default_factory=datetime.now, description="Session start time")
    end_time: Optional[datetime] = Field(None, description="Session end time")

    # Stream URLs
    stream_urls: Dict[str, str] = Field(default_factory=dict, description="Stream URLs by quality")
    websocket_url: Optional[str] = Field(None, description="WebSocket URL for metadata")

    # Viewer Information
    current_viewers: int = Field(default=0, description="Current viewer count")
    max_viewers_reached: int = Field(default=0, description="Maximum viewers during session")
    total_viewers: int = Field(default=0, description="Total unique viewers")

    # Performance Metrics
    frames_streamed: int = Field(default=0, description="Total frames streamed")
    bytes_streamed: int = Field(default=0, description="Total bytes streamed")
    average_fps: float = Field(default=0.0, description="Average FPS during session")

    # Error Tracking
    error_count: int = Field(default=0, description="Number of errors during session")
    last_error: Optional[str] = Field(None, description="Last error message")
    reconnect_count: int = Field(default=0, description="Number of reconnections")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def get_duration_seconds(self) -> Optional[int]:
        """Get session duration in seconds."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds())
        elif self.start_time:
            return int((datetime.now() - self.start_time).total_seconds())
        return None

    def add_viewer(self):
        """Add a viewer to the session."""
        self.current_viewers += 1
        self.total_viewers += 1
        self.max_viewers_reached = max(self.max_viewers_reached, self.current_viewers)

    def remove_viewer(self):
        """Remove a viewer from the session."""
        self.current_viewers = max(0, self.current_viewers - 1)

    def record_error(self, error_message: str):
        """Record an error during streaming."""
        self.error_count += 1
        self.last_error = error_message

    def record_reconnect(self):
        """Record a reconnection event."""
        self.reconnect_count += 1


class ViewerSession(BaseModel):
    """Individual viewer session information."""

    viewer_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique viewer identifier")
    stream_session_id: str = Field(..., description="Associated stream session ID")
    user_id: Optional[str] = Field(None, description="Authenticated user ID")

    # Viewer Information
    ip_address: Optional[str] = Field(None, description="Viewer IP address")
    user_agent: Optional[str] = Field(None, description="Viewer user agent")
    location: Optional[Dict[str, str]] = Field(None, description="Viewer location info")

    # Session Details
    join_time: datetime = Field(default_factory=datetime.now, description="Time viewer joined")
    leave_time: Optional[datetime] = Field(None, description="Time viewer left")
    quality_requested: StreamQuality = Field(default=StreamQuality.MEDIUM, description="Requested stream quality")

    # Viewing Statistics
    bytes_received: int = Field(default=0, description="Bytes received by viewer")
    frames_received: int = Field(default=0, description="Frames received by viewer")
    buffer_events: int = Field(default=0, description="Number of buffering events")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional viewer metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def get_viewing_duration(self) -> Optional[int]:
        """Get viewing duration in seconds."""
        if self.join_time and self.leave_time:
            return int((self.leave_time - self.join_time).total_seconds())
        elif self.join_time:
            return int((datetime.now() - self.join_time).total_seconds())
        return None
