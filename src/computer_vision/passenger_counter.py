"""
Passenger Counter Module

Main module that integrates camera stream, person detection, and zone detection
to provide accurate passenger counting with entry/exit event tracking.
"""

import cv2
import time
import logging
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from .camera_stream import CameraStream
from .person_detector import PersonDetector, Detection
from .zone_detector import ZoneDetector, ZoneType

logger = logging.getLogger(__name__)


@dataclass
class PassengerEvent:
    """Represents a passenger entry or exit event."""
    event_type: str  # 'entry' or 'exit'
    timestamp: datetime
    person_id: int
    detection: Detection
    confidence: float


class PassengerCounter:
    """
    Main passenger counting system that integrates all computer vision components.

    Provides real-time passenger counting with entry/exit detection and
    anti-fraud features through face tracking integration.
    """

    def __init__(self, config: dict):
        """
        Initialize passenger counter.

        Args:
            config: Configuration dictionary containing camera, CV, and zone settings
        """
        self.config = config
        self.is_running = False
        self.current_count = 0
        self.max_capacity = config.get("trip", {}).get("max_capacity", 14)

        # Initialize components
        self.camera_stream = CameraStream(config["camera"])
        self.person_detector = PersonDetector(config["computer_vision"])
        self.zone_detector = ZoneDetector(config["computer_vision"])

        # Event tracking
        self.passenger_events: List[PassengerEvent] = []
        self.event_callbacks: List[Callable] = []

        # Processing thread
        self.processing_thread: Optional[threading.Thread] = None
        self.frame_rate = config["camera"].get("fps", 30)
        self.process_every_n_frames = 3  # Process every 3rd frame for performance
        self.frame_counter = 0

        # Statistics
        self.stats = {
            "total_entries": 0,
            "total_exits": 0,
            "current_passengers": 0,
            "overload_events": 0,
            "processing_fps": 0,
            "last_activity": None
        }

    def start(self) -> bool:
        """
        Start the passenger counting system.

        Returns:
            bool: True if started successfully
        """
        if self.is_running:
            logger.warning("Passenger counter is already running")
            return True

        # Start camera stream
        if not self.camera_stream.start():
            logger.error("Failed to start camera stream")
            return False

        self.is_running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()

        logger.info("Passenger counter started successfully")
        return True

    def stop(self):
        """Stop the passenger counting system."""
        self.is_running = False

        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)

        self.camera_stream.stop()
        logger.info("Passenger counter stopped")

    def reset_count(self):
        """Reset passenger count and clear event history."""
        self.current_count = 0
        self.passenger_events.clear()
        self.stats.update({
            "total_entries": 0,
            "total_exits": 0,
            "current_passengers": 0,
            "overload_events": 0
        })
        logger.info("Passenger count reset")

    def get_current_count(self) -> int:
        """
        Get current passenger count.

        Returns:
            int: Current number of passengers
        """
        return self.current_count

    def get_statistics(self) -> Dict:
        """
        Get detailed counting statistics.

        Returns:
            Dict: Statistics including counts, events, and performance metrics
        """
        self.stats["current_passengers"] = self.current_count
        return self.stats.copy()

    def add_event_callback(self, callback: Callable):
        """
        Add callback function to be called on passenger events.

        Args:
            callback: Function to call with PassengerEvent as argument
        """
        self.event_callbacks.append(callback)

    def get_recent_events(self, limit: int = 10) -> List[PassengerEvent]:
        """
        Get recent passenger events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List[PassengerEvent]: Recent events
        """
        return self.passenger_events[-limit:] if self.passenger_events else []

    def _processing_loop(self):
        """Main processing loop that handles frame analysis and event detection."""
        last_fps_time = time.time()
        fps_frame_count = 0

        while self.is_running:
            try:
                # Get frame from camera
                frame = self.camera_stream.get_frame(timeout=1.0)
                if frame is None:
                    continue

                self.frame_counter += 1

                # Process every Nth frame for performance
                if self.frame_counter % self.process_every_n_frames != 0:
                    continue

                # Detect people in frame
                detections = self.person_detector.detect(frame)

                # Detect zone events
                zone_events = self.zone_detector.detect_zone_events(detections, frame.shape[:2])

                # Process zone events
                for event in zone_events:
                    self._handle_zone_event(event)

                # Update FPS statistics
                fps_frame_count += 1
                current_time = time.time()
                if current_time - last_fps_time >= 1.0:
                    self.stats["processing_fps"] = fps_frame_count / (current_time - last_fps_time)
                    fps_frame_count = 0
                    last_fps_time = current_time

            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(0.1)

    def _handle_zone_event(self, event: Dict):
        """
        Handle a zone crossing event and update passenger count.

        Args:
            event: Zone event dictionary from zone detector
        """
        event_type = event["type"]
        person_id = event["person_id"]
        detection = event["detection"]

        # Create passenger event
        passenger_event = PassengerEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            person_id=person_id,
            detection=detection,
            confidence=detection.confidence
        )

        # Update passenger count
        if event_type == "entry":
            self.current_count += 1
            self.stats["total_entries"] += 1
            logger.info(f"Passenger entered. Count: {self.current_count}")

        elif event_type == "exit":
            self.current_count = max(0, self.current_count - 1)
            self.stats["total_exits"] += 1
            logger.info(f"Passenger exited. Count: {self.current_count}")

        # Check for overload
        if self.current_count > self.max_capacity:
            self.stats["overload_events"] += 1
            logger.warning(f"Vehicle overloaded! Count: {self.current_count}, Max: {self.max_capacity}")

        # Update statistics
        self.stats["last_activity"] = datetime.now()

        # Store event
        self.passenger_events.append(passenger_event)

        # Keep only recent events (last 100)
        if len(self.passenger_events) > 100:
            self.passenger_events = self.passenger_events[-100:]

        # Notify callbacks
        for callback in self.event_callbacks:
            try:
                callback(passenger_event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")

    def is_overloaded(self) -> bool:
        """
        Check if vehicle is currently overloaded.

        Returns:
            bool: True if passenger count exceeds maximum capacity
        """
        return self.current_count > self.max_capacity

    def get_debug_frame(self) -> Optional[cv2.Mat]:
        """
        Get current frame with debug visualizations.

        Returns:
            Optional[cv2.Mat]: Frame with detection and zone overlays
        """
        frame = self.camera_stream.get_frame(timeout=0.1)
        if frame is None:
            return None

        # Add detections
        detections = self.person_detector.detect(frame)
        debug_frame = self.person_detector.visualize_detections(frame, detections)

        # Add zones
        debug_frame = self.zone_detector.visualize_zones(debug_frame)

        # Add count overlay
        cv2.putText(debug_frame, f"Count: {self.current_count}/{self.max_capacity}",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Add overload warning
        if self.is_overloaded():
            cv2.putText(debug_frame, "OVERLOADED!", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        return debug_frame
