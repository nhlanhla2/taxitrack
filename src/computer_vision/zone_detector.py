"""
Zone Detection Module for Entry/Exit Detection

Detects when people cross predefined zones to determine entry and exit events.
Uses geometric calculations to track movement between zones.
"""

import cv2
import numpy as np
import logging
import time
from typing import List, Tuple, Optional, Dict
from enum import Enum
from .person_detector import Detection

logger = logging.getLogger(__name__)


class ZoneType(Enum):
    """Types of detection zones."""
    ENTRY = "entry"
    EXIT = "exit"
    NEUTRAL = "neutral"


class Zone:
    """Represents a detection zone with geometric boundaries."""

    def __init__(self, zone_type: ZoneType, coordinates: List[float], name: str = ""):
        """
        Initialize detection zone.

        Args:
            zone_type: Type of zone (entry/exit/neutral)
            coordinates: Zone boundaries [x1, y1, x2, y2] (normalized 0-1)
            name: Optional zone name for debugging
        """
        self.zone_type = zone_type
        self.coordinates = coordinates
        self.name = name or zone_type.value

    def contains_point(self, point: Tuple[int, int], frame_shape: Tuple[int, int]) -> bool:
        """
        Check if a point is inside this zone.

        Args:
            point: Point coordinates (x, y)
            frame_shape: Frame dimensions (height, width)

        Returns:
            bool: True if point is inside zone
        """
        h, w = frame_shape
        x, y = point

        # Convert normalized coordinates to pixel coordinates
        x1 = int(self.coordinates[0] * w)
        y1 = int(self.coordinates[1] * h)
        x2 = int(self.coordinates[2] * w)
        y2 = int(self.coordinates[3] * h)

        return x1 <= x <= x2 and y1 <= y <= y2

    def get_pixel_coordinates(self, frame_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
        """
        Get zone coordinates in pixel space.

        Args:
            frame_shape: Frame dimensions (height, width)

        Returns:
            Tuple[int, int, int, int]: Pixel coordinates (x1, y1, x2, y2)
        """
        h, w = frame_shape
        x1 = int(self.coordinates[0] * w)
        y1 = int(self.coordinates[1] * h)
        x2 = int(self.coordinates[2] * w)
        y2 = int(self.coordinates[3] * h)
        return (x1, y1, x2, y2)


class ZoneDetector:
    """
    Detects entry and exit events based on zone crossings.

    Tracks person movement between predefined zones to determine
    when passengers enter or exit the vehicle.
    """

    def __init__(self, config: dict):
        """
        Initialize zone detector.

        Args:
            config: Configuration dictionary containing:
                - entry_zone: Entry zone coordinates [x1, y1, x2, y2]
                - exit_zone: Exit zone coordinates [x1, y1, x2, y2]
        """
        self.config = config

        # Create zones from configuration
        self.entry_zone = Zone(
            ZoneType.ENTRY,
            config.get("entry_zone", [0.0, 0.0, 0.5, 1.0]),
            "Entry Zone"
        )

        self.exit_zone = Zone(
            ZoneType.EXIT,
            config.get("exit_zone", [0.5, 0.0, 1.0, 1.0]),
            "Exit Zone"
        )

        # Track person positions and zone history
        self.person_zones: Dict[int, List[ZoneType]] = {}
        self.zone_transition_threshold = 2  # Minimum frames in zone to confirm

    def detect_zone_events(self, detections: List[Detection], frame_shape: Tuple[int, int]) -> List[Dict]:
        """
        Detect entry/exit events based on person positions in zones.

        Args:
            detections: List of person detections
            frame_shape: Frame dimensions (height, width)

        Returns:
            List[Dict]: List of zone events with type and details
        """
        events = []
        current_zones = {}

        # Determine current zone for each detection
        for i, detection in enumerate(detections):
            person_id = i  # Simple ID based on detection index
            center = detection.center

            # Check which zone the person is in
            current_zone = self._get_zone_for_point(center, frame_shape)
            current_zones[person_id] = current_zone

            # Update zone history
            if person_id not in self.person_zones:
                self.person_zones[person_id] = []

            self.person_zones[person_id].append(current_zone)

            # Keep only recent history
            if len(self.person_zones[person_id]) > 10:
                self.person_zones[person_id] = self.person_zones[person_id][-10:]

            # Check for zone transitions
            event = self._check_zone_transition(person_id, detection)
            if event:
                events.append(event)

        # Clean up old person tracks
        self._cleanup_old_tracks(current_zones)

        return events

    def _get_zone_for_point(self, point: Tuple[int, int], frame_shape: Tuple[int, int]) -> Optional[ZoneType]:
        """
        Determine which zone a point belongs to.

        Args:
            point: Point coordinates (x, y)
            frame_shape: Frame dimensions (height, width)

        Returns:
            Optional[ZoneType]: Zone type or None if not in any zone
        """
        if self.entry_zone.contains_point(point, frame_shape):
            return ZoneType.ENTRY
        elif self.exit_zone.contains_point(point, frame_shape):
            return ZoneType.EXIT
        else:
            return ZoneType.NEUTRAL

    def _check_zone_transition(self, person_id: int, detection: Detection) -> Optional[Dict]:
        """
        Check if a person has transitioned between zones.

        Args:
            person_id: Unique person identifier
            detection: Current detection

        Returns:
            Optional[Dict]: Zone transition event or None
        """
        if person_id not in self.person_zones or len(self.person_zones[person_id]) < 2:
            return None

        zone_history = self.person_zones[person_id]

        # Check for entry event (neutral -> entry)
        if (len(zone_history) >= 2 and
            zone_history[-2] == ZoneType.NEUTRAL and
            zone_history[-1] == ZoneType.ENTRY):

            return {
                "type": "entry",
                "person_id": person_id,
                "detection": detection,
                "timestamp": time.time(),
                "zone": "entry"
            }

        # Check for exit event (neutral -> exit)
        elif (len(zone_history) >= 2 and
              zone_history[-2] == ZoneType.NEUTRAL and
              zone_history[-1] == ZoneType.EXIT):

            return {
                "type": "exit",
                "person_id": person_id,
                "detection": detection,
                "timestamp": time.time(),
                "zone": "exit"
            }

        return None

    def _cleanup_old_tracks(self, current_zones: Dict[int, ZoneType]):
        """
        Remove tracking data for people no longer detected.

        Args:
            current_zones: Currently active person zones
        """
        # Remove tracks for people not currently detected
        active_ids = set(current_zones.keys())
        tracked_ids = set(self.person_zones.keys())

        for person_id in tracked_ids - active_ids:
            del self.person_zones[person_id]

    def visualize_zones(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw zone boundaries on frame for visualization.

        Args:
            frame: Input frame

        Returns:
            np.ndarray: Frame with drawn zone boundaries
        """
        vis_frame = frame.copy()
        h, w = frame.shape[:2]

        # Draw entry zone
        entry_coords = self.entry_zone.get_pixel_coordinates((h, w))
        cv2.rectangle(vis_frame, (entry_coords[0], entry_coords[1]),
                     (entry_coords[2], entry_coords[3]), (0, 255, 0), 2)
        cv2.putText(vis_frame, "ENTRY", (entry_coords[0] + 10, entry_coords[1] + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Draw exit zone
        exit_coords = self.exit_zone.get_pixel_coordinates((h, w))
        cv2.rectangle(vis_frame, (exit_coords[0], exit_coords[1]),
                     (exit_coords[2], exit_coords[3]), (0, 0, 255), 2)
        cv2.putText(vis_frame, "EXIT", (exit_coords[0] + 10, exit_coords[1] + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return vis_frame
