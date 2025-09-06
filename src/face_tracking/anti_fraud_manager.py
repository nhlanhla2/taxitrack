"""
Anti-Fraud Manager

Integrates face tracking with passenger counting to prevent double counting
and handle temporary exits/re-entries for accurate passenger counts.
"""

import logging
import time
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

from .face_tracker import FaceTracker, FaceDetection, TrackedFace
from ..computer_vision.person_detector import Detection

logger = logging.getLogger(__name__)


@dataclass
class PassengerRecord:
    """Record of a passenger with face tracking information."""
    face_id: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    status: str = "inside"  # inside, outside, temporary_exit
    zone_events: List[str] = None

    def __post_init__(self):
        if self.zone_events is None:
            self.zone_events = []


class AntiFraudManager:
    """
    Anti-fraud system that prevents double counting using face tracking.

    Tracks passenger faces to handle scenarios like:
    - Temporary exits and re-entries
    - Multiple people entering/exiting simultaneously
    - Preventing counting the same person multiple times
    """

    def __init__(self, config: dict):
        """
        Initialize anti-fraud manager.

        Args:
            config: Configuration dictionary for face tracking
        """
        self.config = config
        self.face_tracker = FaceTracker(config)

        # Passenger tracking
        self.passenger_records: Dict[str, PassengerRecord] = {}
        self.temporary_exit_timeout = 30  # seconds

        # Anti-fraud statistics
        self.stats = {
            "prevented_double_counts": 0,
            "temporary_exits_handled": 0,
            "unique_passengers_seen": 0,
            "false_positives_prevented": 0
        }

    def process_frame_with_detections(self, frame, person_detections: List[Detection],
                                    zone_events: List[Dict]) -> Dict:
        """
        Process frame with person detections and zone events for anti-fraud analysis.

        Args:
            frame: Current video frame
            person_detections: List of person detections from YOLO
            zone_events: List of zone crossing events

        Returns:
            Dict: Anti-fraud analysis results
        """
        # Detect faces in frame
        face_detections = self.face_tracker.detect_faces(frame)

        # Update face tracking
        tracked_faces = self.face_tracker.update_tracking(face_detections)

        # Process zone events with face tracking
        validated_events = self._validate_zone_events(zone_events, face_detections)

        # Update passenger records
        self._update_passenger_records(validated_events, tracked_faces)

        # Clean up old records
        self._cleanup_old_records()

        return {
            "validated_events": validated_events,
            "tracked_faces": tracked_faces,
            "passenger_records": list(self.passenger_records.values()),
            "stats": self.stats.copy()
        }

    def _validate_zone_events(self, zone_events: List[Dict],
                            face_detections: List[FaceDetection]) -> List[Dict]:
        """
        Validate zone events against face tracking to prevent double counting.

        Args:
            zone_events: Raw zone crossing events
            face_detections: Current face detections

        Returns:
            List[Dict]: Validated zone events
        """
        validated_events = []

        for event in zone_events:
            event_type = event["type"]
            person_id = event["person_id"]

            # Try to match zone event to a face
            matched_face = self._match_zone_event_to_face(event, face_detections)

            if matched_face:
                face_id = matched_face.face_id

                # Check if this is a legitimate event or double counting
                if self._is_legitimate_event(event_type, face_id):
                    event["face_id"] = face_id
                    validated_events.append(event)
                    logger.info(f"Validated {event_type} event for face {face_id}")
                else:
                    self.stats["prevented_double_counts"] += 1
                    logger.warning(f"Prevented double counting for face {face_id}")

            else:
                # No face match - could be legitimate or false positive
                # For now, allow events without face matches but log them
                validated_events.append(event)
                logger.warning(f"Zone event without face match: {event_type}")

        return validated_events

    def _match_zone_event_to_face(self, event: Dict,
                                face_detections: List[FaceDetection]) -> Optional[FaceDetection]:
        """
        Match a zone event to a face detection based on spatial proximity.

        Args:
            event: Zone crossing event
            face_detections: Current face detections

        Returns:
            Optional[FaceDetection]: Matched face detection or None
        """
        if not face_detections:
            return None

        # Get person detection from event
        person_detection = event.get("detection")
        if not person_detection:
            return None

        person_center = person_detection.center

        # Find closest face detection
        min_distance = float('inf')
        closest_face = None

        for face_detection in face_detections:
            # Calculate face center
            top, right, bottom, left = face_detection.bbox
            face_center = ((left + right) // 2, (top + bottom) // 2)

            # Calculate distance
            distance = ((person_center[0] - face_center[0]) ** 2 +
                       (person_center[1] - face_center[1]) ** 2) ** 0.5

            if distance < min_distance:
                min_distance = distance
                closest_face = face_detection

        # Return closest face if within reasonable distance
        max_distance = 100  # pixels
        if closest_face and min_distance <= max_distance:
            return closest_face

        return None

    def _is_legitimate_event(self, event_type: str, face_id: str) -> bool:
        """
        Check if a zone event is legitimate or a double counting attempt.

        Args:
            event_type: Type of event ('entry' or 'exit')
            face_id: Face ID associated with the event

        Returns:
            bool: True if event is legitimate
        """
        current_time = datetime.now()

        if face_id not in self.passenger_records:
            # New passenger - always legitimate
            return True

        record = self.passenger_records[face_id]

        if event_type == "entry":
            # Entry is legitimate if passenger is currently outside
            return record.status in ["outside", "temporary_exit"]

        elif event_type == "exit":
            # Exit is legitimate if passenger is currently inside
            return record.status == "inside"

        return False

    def _update_passenger_records(self, validated_events: List[Dict],
                                tracked_faces: List[TrackedFace]):
        """
        Update passenger records based on validated events.

        Args:
            validated_events: List of validated zone events
            tracked_faces: List of currently tracked faces
        """
        current_time = datetime.now()

        # Process validated events
        for event in validated_events:
            face_id = event.get("face_id")
            if not face_id:
                continue

            event_type = event["type"]

            if face_id not in self.passenger_records:
                # Create new passenger record
                record = PassengerRecord(
                    face_id=face_id,
                    entry_time=current_time if event_type == "entry" else None,
                    status="inside" if event_type == "entry" else "outside"
                )
                self.passenger_records[face_id] = record
                self.stats["unique_passengers_seen"] += 1

            else:
                # Update existing record
                record = self.passenger_records[face_id]

                if event_type == "entry":
                    if record.status == "temporary_exit":
                        self.stats["temporary_exits_handled"] += 1
                        logger.info(f"Handled temporary exit for face {face_id}")
                    record.status = "inside"
                    record.entry_time = current_time

                elif event_type == "exit":
                    record.status = "outside"
                    record.exit_time = current_time

            record.zone_events.append(f"{event_type}_{current_time.isoformat()}")

        # Update status based on face tracking
        active_face_ids = {face.face_id for face in tracked_faces if face.status == "active"}

        for face_id, record in self.passenger_records.items():
            if record.status == "inside" and face_id not in active_face_ids:
                # Passenger inside but face not detected - possible temporary exit
                time_since_last_seen = current_time - record.entry_time
                if time_since_last_seen.total_seconds() > self.temporary_exit_timeout:
                    record.status = "temporary_exit"

    def _cleanup_old_records(self):
        """Clean up old passenger records."""
        current_time = datetime.now()
        cleanup_threshold = current_time - timedelta(hours=1)  # Keep records for 1 hour

        records_to_remove = []
        for face_id, record in self.passenger_records.items():
            last_activity = record.exit_time or record.entry_time
            if last_activity and last_activity < cleanup_threshold:
                records_to_remove.append(face_id)

        for face_id in records_to_remove:
            del self.passenger_records[face_id]

    def get_current_passenger_count(self) -> int:
        """
        Get current passenger count based on face tracking.

        Returns:
            int: Number of passengers currently inside
        """
        return sum(1 for record in self.passenger_records.values()
                  if record.status in ["inside", "temporary_exit"])

    def reset(self):
        """Reset all anti-fraud data."""
        self.passenger_records.clear()
        self.face_tracker.reset_tracking()
        self.stats = {
            "prevented_double_counts": 0,
            "temporary_exits_handled": 0,
            "unique_passengers_seen": 0,
            "false_positives_prevented": 0
        }
        logger.info("Anti-fraud manager reset")
