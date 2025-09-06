"""
Trip Management Data Models

Defines data structures for trip management, status tracking,
and event logging.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass


class TripStatus(str, Enum):
    """Trip status enumeration."""
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class EventType(str, Enum):
    """Trip event types."""
    TRIP_STARTED = "trip_started"
    TRIP_STOPPED = "trip_stopped"
    PASSENGER_ENTRY = "passenger_entry"
    PASSENGER_EXIT = "passenger_exit"
    OVERLOAD_DETECTED = "overload_detected"
    CAPACITY_WARNING = "capacity_warning"
    SYSTEM_ERROR = "system_error"
    BACKEND_SYNC = "backend_sync"


class TripEvent(BaseModel):
    """Individual trip event model."""
    event_id: str = Field(..., description="Unique event identifier")
    trip_id: str = Field(..., description="Associated trip ID")
    event_type: EventType = Field(..., description="Type of event")
    timestamp: datetime = Field(..., description="Event timestamp")
    passenger_count: int = Field(..., description="Passenger count at time of event")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event data")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Trip(BaseModel):
    """Trip data model."""
    trip_id: str = Field(..., description="Unique trip identifier")
    device_id: str = Field(..., description="Device/taxi identifier")
    status: TripStatus = Field(default=TripStatus.NOT_STARTED, description="Current trip status")

    # Timing
    start_time: Optional[datetime] = Field(default_factory=datetime.now, description="Trip start timestamp")
    end_time: Optional[datetime] = Field(None, description="Trip end timestamp")
    duration_seconds: Optional[int] = Field(None, description="Trip duration in seconds")

    # Passenger data
    current_passenger_count: int = Field(default=0, description="Current passenger count")
    max_passenger_count: int = Field(default=0, description="Maximum passengers during trip")
    total_entries: int = Field(default=0, description="Total passenger entries")
    total_exits: int = Field(default=0, description="Total passenger exits")

    # Capacity management
    max_capacity: int = Field(default=14, description="Maximum allowed capacity")
    overload_events: int = Field(default=0, description="Number of overload events")
    is_overloaded: bool = Field(default=False, description="Current overload status")

    # Route information
    route_info: Dict[str, Any] = Field(default_factory=dict, description="Route details")

    # Events
    events: List[TripEvent] = Field(default_factory=list, description="Trip events")

    # Statistics
    stats: Dict[str, Any] = Field(default_factory=dict, description="Trip statistics")

    # Backend sync
    last_backend_sync: Optional[datetime] = Field(None, description="Last backend synchronization")
    sync_status: str = Field(default="pending", description="Backend sync status")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def add_event(self, event_type: EventType, metadata: Dict[str, Any] = None) -> TripEvent:
        """
        Add an event to the trip.

        Args:
            event_type: Type of event to add
            metadata: Additional event metadata

        Returns:
            TripEvent: Created event
        """
        import uuid

        event = TripEvent(
            event_id=str(uuid.uuid4()),
            trip_id=self.trip_id,
            event_type=event_type,
            timestamp=datetime.now(),
            passenger_count=self.current_passenger_count,
            metadata=metadata or {}
        )

        self.events.append(event)
        return event

    def update_passenger_count(self, new_count: int):
        """
        Update passenger count and related statistics.

        Args:
            new_count: New passenger count
        """
        self.current_passenger_count = new_count
        self.max_passenger_count = max(self.max_passenger_count, new_count)

        # Check for overload
        if new_count > self.max_capacity:
            if not self.is_overloaded:
                self.is_overloaded = True
                self.overload_events += 1
                self.add_event(EventType.OVERLOAD_DETECTED, {
                    "passenger_count": new_count,
                    "max_capacity": self.max_capacity
                })
        else:
            self.is_overloaded = False

    def get_duration(self) -> Optional[int]:
        """
        Get trip duration in seconds.

        Returns:
            Optional[int]: Duration in seconds or None if trip not completed
        """
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds())
        elif self.start_time:
            return int((datetime.now() - self.start_time).total_seconds())
        return None

    def to_summary(self) -> Dict[str, Any]:
        """
        Get trip summary for API responses.

        Returns:
            Dict[str, Any]: Trip summary
        """
        return {
            "trip_id": self.trip_id,
            "device_id": self.device_id,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.get_duration(),
            "current_passenger_count": self.current_passenger_count,
            "max_passenger_count": self.max_passenger_count,
            "total_entries": self.total_entries,
            "total_exits": self.total_exits,
            "is_overloaded": self.is_overloaded,
            "overload_events": self.overload_events,
            "event_count": len(self.events),
            "last_backend_sync": self.last_backend_sync.isoformat() if self.last_backend_sync else None,
            "sync_status": self.sync_status
        }

    def end_trip(self):
        """End the trip and set final status."""
        self.end_time = datetime.now()
        self.status = TripStatus.COMPLETED

    def get_duration_minutes(self) -> Optional[float]:
        """Get trip duration in minutes."""
        duration_seconds = self.get_duration()
        return duration_seconds / 60 if duration_seconds else None
