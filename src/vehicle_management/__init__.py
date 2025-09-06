"""
Vehicle Management Module

Handles vehicle identification, registration, and multi-vehicle support
for the taxi passenger counting system.
"""

from .models import Vehicle, VehicleStatus, CameraType, FootageRecord
from .footage_manager import FootageManager

__all__ = [
    "Vehicle",
    "VehicleStatus",
    "CameraType",
    "FootageRecord",
    "FootageManager"
]
