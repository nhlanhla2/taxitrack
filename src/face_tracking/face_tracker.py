"""
Face Tracking Module

Provides face detection, encoding, and tracking capabilities for passenger
identification and anti-fraud features.
"""

import cv2
import numpy as np
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Warning: face_recognition not available. Face tracking will be disabled.")
import logging
import time
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class FaceDetection:
    """Represents a detected face with encoding and metadata."""
    bbox: Tuple[int, int, int, int]  # (top, right, bottom, left)
    encoding: np.ndarray
    confidence: float
    timestamp: datetime
    face_id: Optional[str] = None


@dataclass
class TrackedFace:
    """Represents a tracked face across multiple frames."""
    face_id: str
    encodings: List[np.ndarray]
    last_seen: datetime
    first_seen: datetime
    detection_count: int
    status: str = "active"  # active, lost, exited


class FaceTracker:
    """
    Face detection and tracking system for passenger identification.

    Uses face_recognition library to detect, encode, and track faces
    across video frames for anti-fraud purposes.
    """

    def __init__(self, config: dict):
        """
        Initialize face tracker.

        Args:
            config: Configuration dictionary containing:
                - model: Face recognition model ('hog' or 'cnn')
                - tolerance: Face matching tolerance (0.0-1.0)
                - max_tracking_time: Maximum time to track without detection
                - min_face_size: Minimum face size for detection
        """
        self.config = config
        self.model = config.get("model", "hog")
        self.tolerance = config.get("tolerance", 0.6)
        self.max_tracking_time = config.get("max_tracking_time", 10)  # seconds
        self.min_face_size = config.get("min_face_size", 50)

        # Tracking state
        self.tracked_faces: Dict[str, TrackedFace] = {}
        self.next_face_id = 1
        self.enabled = FACE_RECOGNITION_AVAILABLE

        # Performance optimization
        self.face_locations_cache = {}
        self.last_detection_time = 0
        self.detection_interval = 0.5  # seconds between detections

        if not self.enabled:
            logger.warning("Face recognition not available - face tracking disabled")
        else:
            logger.info(f"FaceTracker initialized with model={self.model}, tolerance={self.tolerance}")

    def detect_faces(self, frame: np.ndarray) -> List[FaceDetection]:
        """
        Detect faces in the given frame.

        Args:
            frame: Input frame as numpy array

        Returns:
            List[FaceDetection]: List of detected faces with encodings
        """
        if not self.enabled:
            return []  # Return empty list if face recognition is not available

        current_time = time.time()

        # Skip detection if too soon (performance optimization)
        if current_time - self.last_detection_time < self.detection_interval:
            return []

        self.last_detection_time = current_time

        try:
            # Convert BGR to RGB for face_recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Resize frame for faster processing
            small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.5, fy=0.5)

            # Find face locations
            face_locations = face_recognition.face_locations(small_frame, model=self.model)

            if not face_locations:
                return []

            # Scale back up face locations
            face_locations = [(top*2, right*2, bottom*2, left*2)
                            for (top, right, bottom, left) in face_locations]

            # Filter faces by minimum size
            valid_faces = []
            for (top, right, bottom, left) in face_locations:
                face_width = right - left
                face_height = bottom - top
                if face_width >= self.min_face_size and face_height >= self.min_face_size:
                    valid_faces.append((top, right, bottom, left))

            if not valid_faces:
                return []

            # Get face encodings
            face_encodings = face_recognition.face_encodings(rgb_frame, valid_faces)

            # Create FaceDetection objects
            detections = []
            for (top, right, bottom, left), encoding in zip(valid_faces, face_encodings):
                detection = FaceDetection(
                    bbox=(top, right, bottom, left),
                    encoding=encoding,
                    confidence=1.0,  # face_recognition doesn't provide confidence
                    timestamp=datetime.now()
                )
                detections.append(detection)

            logger.debug(f"Detected {len(detections)} faces")
            return detections

        except Exception as e:
            logger.error(f"Error detecting faces: {e}")
            return []

    def update_tracking(self, detections: List[FaceDetection]) -> List[TrackedFace]:
        """
        Update face tracking with new detections.

        Args:
            detections: List of face detections from current frame

        Returns:
            List[TrackedFace]: List of currently tracked faces
        """
        current_time = datetime.now()

        # Match detections to existing tracked faces
        for detection in detections:
            matched_face_id = self._match_detection_to_tracked_face(detection)

            if matched_face_id:
                # Update existing tracked face
                tracked_face = self.tracked_faces[matched_face_id]
                tracked_face.encodings.append(detection.encoding)
                tracked_face.last_seen = current_time
                tracked_face.detection_count += 1
                tracked_face.status = "active"

                # Keep only recent encodings (last 10)
                if len(tracked_face.encodings) > 10:
                    tracked_face.encodings = tracked_face.encodings[-10:]

                detection.face_id = matched_face_id

            else:
                # Create new tracked face
                face_id = f"face_{self.next_face_id:04d}"
                self.next_face_id += 1

                tracked_face = TrackedFace(
                    face_id=face_id,
                    encodings=[detection.encoding],
                    last_seen=current_time,
                    first_seen=current_time,
                    detection_count=1,
                    status="active"
                )

                self.tracked_faces[face_id] = tracked_face
                detection.face_id = face_id

        # Update status of tracked faces not seen recently
        timeout_threshold = current_time - timedelta(seconds=self.max_tracking_time)

        for face_id, tracked_face in self.tracked_faces.items():
            if tracked_face.last_seen < timeout_threshold and tracked_face.status == "active":
                tracked_face.status = "lost"
                logger.debug(f"Face {face_id} marked as lost")

        # Clean up very old tracked faces
        cleanup_threshold = current_time - timedelta(seconds=self.max_tracking_time * 2)
        faces_to_remove = [
            face_id for face_id, tracked_face in self.tracked_faces.items()
            if tracked_face.last_seen < cleanup_threshold
        ]

        for face_id in faces_to_remove:
            del self.tracked_faces[face_id]
            logger.debug(f"Removed old tracked face {face_id}")

        return list(self.tracked_faces.values())

    def _match_detection_to_tracked_face(self, detection: FaceDetection) -> Optional[str]:
        """
        Match a face detection to an existing tracked face.

        Args:
            detection: Face detection to match

        Returns:
            Optional[str]: Face ID of matched tracked face or None
        """
        if not self.tracked_faces:
            return None

        # Compare with all active tracked faces
        for face_id, tracked_face in self.tracked_faces.items():
            if tracked_face.status != "active":
                continue

            # Use the most recent encoding for comparison
            if tracked_face.encodings:
                recent_encoding = tracked_face.encodings[-1]
                distance = face_recognition.face_distance([recent_encoding], detection.encoding)[0]

                if distance <= self.tolerance:
                    return face_id

        return None

    def get_active_faces(self) -> List[TrackedFace]:
        """
        Get list of currently active tracked faces.

        Returns:
            List[TrackedFace]: Active tracked faces
        """
        return [face for face in self.tracked_faces.values() if face.status == "active"]

    def reset_tracking(self):
        """Reset all tracking data."""
        self.tracked_faces.clear()
        self.next_face_id = 1
        logger.info("Face tracking reset")

    def visualize_faces(self, frame: np.ndarray, detections: List[FaceDetection]) -> np.ndarray:
        """
        Draw face detection boxes and IDs on frame.

        Args:
            frame: Input frame
            detections: List of face detections

        Returns:
            np.ndarray: Frame with face visualizations
        """
        vis_frame = frame.copy()

        for detection in detections:
            top, right, bottom, left = detection.bbox

            # Draw face rectangle
            cv2.rectangle(vis_frame, (left, top), (right, bottom), (0, 255, 0), 2)

            # Draw face ID if available
            if detection.face_id:
                label = f"ID: {detection.face_id}"
                cv2.putText(vis_frame, label, (left, top - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return vis_frame
