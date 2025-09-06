"""
Person Detection Module using YOLO

Detects people in video frames using YOLOv8 models optimized for Raspberry Pi.
Provides bounding box coordinates and confidence scores for detected persons.
"""

import cv2
import numpy as np
import logging
from typing import List, Tuple, Optional
from ultralytics import YOLO
import torch

logger = logging.getLogger(__name__)


class Detection:
    """Represents a person detection with bounding box and confidence."""

    def __init__(self, bbox: Tuple[int, int, int, int], confidence: float, class_id: int = 0):
        """
        Initialize detection.

        Args:
            bbox: Bounding box as (x1, y1, x2, y2)
            confidence: Detection confidence score (0-1)
            class_id: Class ID (0 for person)
        """
        self.bbox = bbox
        self.confidence = confidence
        self.class_id = class_id
        self.center = self._calculate_center()

    def _calculate_center(self) -> Tuple[int, int]:
        """Calculate center point of bounding box."""
        x1, y1, x2, y2 = self.bbox
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))

    @property
    def area(self) -> int:
        """Calculate area of bounding box."""
        x1, y1, x2, y2 = self.bbox
        return (x2 - x1) * (y2 - y1)

    def __repr__(self) -> str:
        return f"Detection(bbox={self.bbox}, conf={self.confidence:.2f})"


class PersonDetector:
    """
    YOLO-based person detector optimized for Raspberry Pi.

    Uses YOLOv8 models with configurable confidence thresholds and
    non-maximum suppression for accurate person detection.
    """

    def __init__(self, config: dict):
        """
        Initialize person detector.

        Args:
            config: Configuration dictionary containing:
                - detection_model: YOLO model path/name
                - confidence_threshold: Minimum confidence for detections
                - nms_threshold: Non-maximum suppression threshold
                - roi: Region of interest [x1, y1, x2, y2] (normalized)
        """
        self.config = config
        self.model: Optional[YOLO] = None
        self.confidence_threshold = config.get("confidence_threshold", 0.5)
        self.nms_threshold = config.get("nms_threshold", 0.4)
        self.roi = config.get("roi", [0.0, 0.0, 1.0, 1.0])
        self.device = self._get_device()

        # Initialize model
        self._load_model()

    def _get_device(self) -> str:
        """
        Determine the best available device for inference.

        Returns:
            str: Device name ('cuda', 'mps', or 'cpu')
        """
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def _load_model(self):
        """Load YOLO model with error handling."""
        try:
            model_path = self.config["detection_model"]
            logger.info(f"Loading YOLO model: {model_path}")

            self.model = YOLO(model_path)

            # Move model to appropriate device
            if self.device != "cpu":
                self.model.to(self.device)

            logger.info(f"Model loaded successfully on device: {self.device}")

        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect people in the given frame.

        Args:
            frame: Input frame as numpy array

        Returns:
            List[Detection]: List of person detections
        """
        if self.model is None:
            logger.error("Model not loaded")
            return []

        try:
            # Apply ROI if specified
            roi_frame = self._apply_roi(frame)

            # Run inference
            results = self.model(roi_frame, verbose=False)

            # Process results
            detections = self._process_results(results[0], frame.shape)

            logger.debug(f"Detected {len(detections)} people")
            return detections

        except Exception as e:
            logger.error(f"Error during detection: {e}")
            return []

    def _apply_roi(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply region of interest to frame.

        Args:
            frame: Input frame

        Returns:
            np.ndarray: Cropped frame based on ROI
        """
        if self.roi == [0.0, 0.0, 1.0, 1.0]:
            return frame

        h, w = frame.shape[:2]
        x1 = int(self.roi[0] * w)
        y1 = int(self.roi[1] * h)
        x2 = int(self.roi[2] * w)
        y2 = int(self.roi[3] * h)

        return frame[y1:y2, x1:x2]

    def _process_results(self, result, original_shape: Tuple[int, int, int]) -> List[Detection]:
        """
        Process YOLO detection results.

        Args:
            result: YOLO detection result
            original_shape: Original frame shape (H, W, C)

        Returns:
            List[Detection]: Processed detections
        """
        detections = []

        if result.boxes is None:
            return detections

        # Extract detection data
        boxes = result.boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2
        confidences = result.boxes.conf.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy()

        # Filter for person class (class 0 in COCO dataset)
        person_mask = classes == 0

        if not person_mask.any():
            return detections

        person_boxes = boxes[person_mask]
        person_confidences = confidences[person_mask]

        # Apply confidence threshold
        conf_mask = person_confidences >= self.confidence_threshold
        person_boxes = person_boxes[conf_mask]
        person_confidences = person_confidences[conf_mask]

        # Convert coordinates back to original frame if ROI was applied
        if self.roi != [0.0, 0.0, 1.0, 1.0]:
            person_boxes = self._convert_roi_to_original(person_boxes, original_shape)

        # Create Detection objects
        for box, conf in zip(person_boxes, person_confidences):
            x1, y1, x2, y2 = map(int, box)
            detection = Detection((x1, y1, x2, y2), float(conf))
            detections.append(detection)

        return detections

    def _convert_roi_to_original(self, boxes: np.ndarray, original_shape: Tuple[int, int, int]) -> np.ndarray:
        """
        Convert bounding boxes from ROI coordinates to original frame coordinates.

        Args:
            boxes: Bounding boxes in ROI coordinates
            original_shape: Original frame shape (H, W, C)

        Returns:
            np.ndarray: Bounding boxes in original frame coordinates
        """
        h, w = original_shape[:2]
        roi_x1 = int(self.roi[0] * w)
        roi_y1 = int(self.roi[1] * h)

        # Offset boxes by ROI position
        boxes[:, [0, 2]] += roi_x1  # x coordinates
        boxes[:, [1, 3]] += roi_y1  # y coordinates

        return boxes

    def visualize_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """
        Draw detection bounding boxes on frame for visualization.

        Args:
            frame: Input frame
            detections: List of detections to visualize

        Returns:
            np.ndarray: Frame with drawn bounding boxes
        """
        vis_frame = frame.copy()

        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            confidence = detection.confidence

            # Draw bounding box
            cv2.rectangle(vis_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Draw confidence score
            label = f"Person: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(vis_frame, (x1, y1 - label_size[1] - 10),
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            cv2.putText(vis_frame, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

        return vis_frame
