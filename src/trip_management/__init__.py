"""
Trip Management Module

Provides trip lifecycle management, API endpoints, and integration
with passenger counting and backend systems.
"""

from .models import Trip, TripStatus, TripEvent, EventType

__all__ = [
    "Trip",
    "TripStatus",
    "TripEvent",
    "EventType"
]
