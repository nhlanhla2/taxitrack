"""
Camera Stream Handler for Passenger Counting System

Handles video stream input from IP cameras or USB cameras with proper
error handling and reconnection logic.
"""

import cv2
import time
import logging
import threading
from typing import Optional, Tuple, Callable
from queue import Queue, Empty
import numpy as np

logger = logging.getLogger(__name__)


class CameraStream:
    """
    Manages camera stream input with automatic reconnection and frame buffering.

    Supports both IP cameras (RTSP) and USB cameras with configurable resolution
    and frame rate settings.
    """

    def __init__(self, config: dict):
        """
        Initialize camera stream.

        Args:
            config: Camera configuration dictionary containing:
                - stream_url: RTSP URL for IP cameras
                - usb_camera_index: Index for USB cameras
                - width: Frame width
                - height: Frame height
                - fps: Target frames per second
                - type: 'ip' or 'usb'
        """
        self.config = config
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.frame_queue = Queue(maxsize=10)
        self.capture_thread: Optional[threading.Thread] = None
        self.last_frame_time = 0
        self.frame_count = 0
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds

    def start(self) -> bool:
        """
        Start the camera stream.

        Returns:
            bool: True if stream started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("Camera stream is already running")
            return True

        if not self._initialize_camera():
            return False

        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
        self.capture_thread.start()

        logger.info(f"Camera stream started: {self._get_stream_source()}")
        return True

    def stop(self):
        """Stop the camera stream and cleanup resources."""
        self.is_running = False

        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5)

        if self.cap:
            self.cap.release()
            self.cap = None

        # Clear frame queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except Empty:
                break

        logger.info("Camera stream stopped")

    def get_frame(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Get the latest frame from the camera stream.

        Args:
            timeout: Maximum time to wait for a frame in seconds

        Returns:
            numpy.ndarray: Latest frame or None if no frame available
        """
        try:
            frame = self.frame_queue.get(timeout=timeout)
            return frame
        except Empty:
            logger.warning("No frame available within timeout")
            return None

    def is_connected(self) -> bool:
        """
        Check if camera is connected and streaming.

        Returns:
            bool: True if camera is connected and streaming
        """
        return self.is_running and self.cap is not None and self.cap.isOpened()

    def get_stream_info(self) -> dict:
        """
        Get information about the current stream.

        Returns:
            dict: Stream information including resolution, fps, etc.
        """
        if not self.cap:
            return {}

        return {
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": self.cap.get(cv2.CAP_PROP_FPS),
            "frame_count": self.frame_count,
            "is_connected": self.is_connected(),
            "source": self._get_stream_source()
        }

    def _initialize_camera(self) -> bool:
        """
        Initialize camera capture object.

        Returns:
            bool: True if initialization successful
        """
        try:
            if self.config["type"] == "ip":
                self.cap = cv2.VideoCapture(self.config["stream_url"])
            else:
                self.cap = cv2.VideoCapture(self.config["usb_camera_index"])

            if not self.cap.isOpened():
                logger.error(f"Failed to open camera: {self._get_stream_source()}")
                return False

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config["width"])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config["height"])
            self.cap.set(cv2.CAP_PROP_FPS, self.config["fps"])

            # Set buffer size to reduce latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            logger.info(f"Camera initialized: {self.get_stream_info()}")
            return True

        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            return False

    def _capture_frames(self):
        """
        Capture frames from camera in a separate thread.
        Handles reconnection logic and frame buffering.
        """
        while self.is_running:
            try:
                if not self.cap or not self.cap.isOpened():
                    if not self._reconnect():
                        time.sleep(self.reconnect_delay)
                        continue

                ret, frame = self.cap.read()
                if not ret:
                    logger.warning("Failed to read frame from camera")
                    if not self._reconnect():
                        time.sleep(self.reconnect_delay)
                        continue

                # Update frame statistics
                self.frame_count += 1
                self.last_frame_time = time.time()

                # Add frame to queue (drop oldest if queue is full)
                try:
                    self.frame_queue.put_nowait(frame)
                except:
                    # Queue is full, remove oldest frame and add new one
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame)
                    except Empty:
                        pass

                # Reset reconnect attempts on successful frame
                self.reconnect_attempts = 0

            except Exception as e:
                logger.error(f"Error in frame capture: {e}")
                time.sleep(1)

    def _reconnect(self) -> bool:
        """
        Attempt to reconnect to the camera.

        Returns:
            bool: True if reconnection successful
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached")
            return False

        self.reconnect_attempts += 1
        logger.info(f"Attempting to reconnect to camera (attempt {self.reconnect_attempts})")

        if self.cap:
            self.cap.release()

        return self._initialize_camera()

    def _get_stream_source(self) -> str:
        """
        Get a string representation of the stream source.

        Returns:
            str: Stream source description
        """
        if self.config["type"] == "ip":
            return self.config["stream_url"]
        else:
            return f"USB Camera {self.config['usb_camera_index']}"
