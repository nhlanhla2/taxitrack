"""
Vehicle Management Data Models

Defines data structures for vehicle registration, identification,
and multi-vehicle fleet management.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class VehicleStatus(str, Enum):
    """Vehicle operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    ERROR = "error"


class CameraType(str, Enum):
    """Camera connection types."""
    IP_CAMERA = "ip_camera"
    USB_CAMERA = "usb_camera"
    RTSP_STREAM = "rtsp_stream"
    HTTP_STREAM = "http_stream"


class Vehicle(BaseModel):
    """Vehicle registration and configuration model."""

    # Vehicle Identification
    vehicle_id: str = Field(..., description="Unique vehicle identifier")
    registration_number: str = Field(..., description="Vehicle registration number (e.g., HDJ864L)")
    fleet_id: Optional[str] = Field(None, description="Fleet identifier")

    # Vehicle Details
    make: Optional[str] = Field(None, description="Vehicle make")
    model: Optional[str] = Field(None, description="Vehicle model")
    year: Optional[int] = Field(None, description="Vehicle year")
    color: Optional[str] = Field(None, description="Vehicle color")

    # Operational Details
    status: VehicleStatus = Field(default=VehicleStatus.ACTIVE, description="Current vehicle status")
    route: Optional[str] = Field(None, description="Assigned route")
    driver_id: Optional[str] = Field(None, description="Current driver ID")
    capacity: int = Field(default=14, description="Maximum passenger capacity")

    # Camera Configuration
    camera_config: Dict[str, Any] = Field(default_factory=dict, description="Camera configuration")
    camera_type: CameraType = Field(default=CameraType.IP_CAMERA, description="Camera type")
    camera_url: Optional[str] = Field(None, description="Camera stream URL")
    camera_username: Optional[str] = Field(None, description="Camera username")
    camera_password: Optional[str] = Field(None, description="Camera password")

    # System Configuration
    device_id: str = Field(..., description="Raspberry Pi device identifier")
    installation_date: datetime = Field(default_factory=datetime.now, description="System installation date")
    last_maintenance: Optional[datetime] = Field(None, description="Last maintenance date")

    # Location and Tracking
    gps_enabled: bool = Field(default=False, description="GPS tracking enabled")
    current_location: Optional[Dict[str, float]] = Field(None, description="Current GPS coordinates")

    # Statistics
    total_trips: int = Field(default=0, description="Total trips completed")
    total_passengers: int = Field(default=0, description="Total passengers transported")
    last_trip_date: Optional[datetime] = Field(None, description="Last trip date")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Record creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def get_camera_stream_url(self) -> str:
        """
        Get the complete camera stream URL with authentication.

        Returns:
            str: Complete camera stream URL
        """
        if not self.camera_url:
            return ""

        if self.camera_type == CameraType.RTSP_STREAM and self.camera_username:
            # Format: rtsp://username:password@ip:port/stream
            base_url = self.camera_url
            if "://" in base_url:
                protocol, rest = base_url.split("://", 1)
                if self.camera_password:
                    return f"{protocol}://{self.camera_username}:{self.camera_password}@{rest}"
                else:
                    return f"{protocol}://{self.camera_username}@{rest}"

        return self.camera_url

    def update_stats(self, trip_completed: bool = False, passenger_count: int = 0):
        """
        Update vehicle statistics.

        Args:
            trip_completed: Whether a trip was completed
            passenger_count: Number of passengers in the trip
        """
        if trip_completed:
            self.total_trips += 1
            self.total_passengers += passenger_count
            self.last_trip_date = datetime.now()

        self.updated_at = datetime.now()

    def to_summary(self) -> Dict[str, Any]:
        """
        Get vehicle summary for API responses.

        Returns:
            Dict[str, Any]: Vehicle summary
        """
        return {
            "vehicle_id": self.vehicle_id,
            "registration_number": self.registration_number,
            "status": self.status,
            "route": self.route,
            "capacity": self.capacity,
            "camera_type": self.camera_type,
            "device_id": self.device_id,
            "total_trips": self.total_trips,
            "total_passengers": self.total_passengers,
            "last_trip_date": self.last_trip_date.isoformat() if self.last_trip_date else None,
            "gps_enabled": self.gps_enabled,
            "current_location": self.current_location
        }


class FootageRecord(BaseModel):
    """Trip footage recording information."""

    footage_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique footage identifier")
    vehicle_id: str = Field(..., description="Associated vehicle ID")
    trip_id: str = Field(..., description="Associated trip ID")

    # File Information
    filename: str = Field(..., description="Video filename")
    file_path: str = Field(..., description="Local file path")
    file_size: int = Field(default=0, description="File size in bytes")
    duration_seconds: int = Field(default=0, description="Video duration in seconds")

    # Recording Details
    start_time: datetime = Field(..., description="Recording start time")
    end_time: Optional[datetime] = Field(None, description="Recording end time")
    resolution: str = Field(default="1920x1080", description="Video resolution")
    fps: int = Field(default=30, description="Frames per second")

    # Upload Status
    uploaded: bool = Field(default=False, description="Whether footage is uploaded to backend")
    upload_url: Optional[str] = Field(None, description="Backend upload URL")
    upload_date: Optional[datetime] = Field(None, description="Upload completion date")
    upload_attempts: int = Field(default=0, description="Number of upload attempts")

    # Processing Status
    processed: bool = Field(default=False, description="Whether footage has been processed")
    passenger_events_extracted: bool = Field(default=False, description="Whether events were extracted")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Record creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def mark_uploaded(self, upload_url: str):
        """Mark footage as successfully uploaded."""
        self.uploaded = True
        self.upload_url = upload_url
        self.upload_date = datetime.now()

    def increment_upload_attempts(self):
        """Increment upload attempt counter."""
        self.upload_attempts += 1
