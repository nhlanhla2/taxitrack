"""
Tracking Manager

Manages object tracking for passenger counting in taxi vehicles.
Handles person detection, tracking, and counting logic.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class TrackingManager:
    """
    Manages object tracking for passenger counting.

    Handles person detection, tracking across frames, and counting
    passengers entering/exiting the vehicle.
    """

    def __init__(self, config: dict):
        """
        Initialize tracking manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.tracking_config = config.get("computer_vision", {})

        # Tracking parameters
        self.max_tracking_distance = 50  # pixels
        self.max_tracking_time = 30  # frames
        self.min_confidence = self.tracking_config.get("confidence_threshold", 0.5)

        # Active tracks
        self.active_tracks: Dict[int, Dict[str, Any]] = {}
        self.next_track_id = 1
        self.frame_count = 0

        # Counting zones
        self.entry_zone = self.tracking_config.get("entry_zone", [0.0, 0.0, 0.5, 1.0])
        self.exit_zone = self.tracking_config.get("exit_zone", [0.5, 0.0, 1.0, 1.0])

        # Statistics
        self.total_entries = 0
        self.total_exits = 0

        logger.info("TrackingManager initialized")

    def get_passenger_count(self) -> int:
        """Get current passenger count."""
        return self.total_entries - self.total_exits

    def get_statistics(self) -> Dict[str, Any]:
        """Get tracking statistics."""
        return {
            "total_entries": self.total_entries,
            "total_exits": self.total_exits,
            "current_count": self.get_passenger_count(),
            "active_tracks": len(self.active_tracks),
            "frame_count": self.frame_count
        }

    def reset_counts(self):
        """Reset passenger counts."""
        self.total_entries = 0
        self.total_exits = 0
        logger.info("Passenger counts reset")
