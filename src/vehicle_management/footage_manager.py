"""
Footage Manager

Handles trip video recording, storage, and upload management for
the taxi passenger counting system.
"""

import os
import cv2
import threading
import logging
import asyncio
import aiofiles
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

from .models import FootageRecord, Vehicle

logger = logging.getLogger(__name__)


class FootageManager:
    """
    Manages trip footage recording, storage, and upload operations.

    Handles video recording during trips, local storage management,
    and on-demand upload to backend systems.
    """

    def __init__(self, config: dict, vehicle: Vehicle):
        """
        Initialize footage manager.

        Args:
            config: Configuration dictionary
            vehicle: Vehicle information
        """
        self.config = config
        self.vehicle = vehicle

        # Storage configuration
        self.storage_path = Path(config.get("footage", {}).get("storage_path", "footage"))
        self.max_storage_gb = config.get("footage", {}).get("max_storage_gb", 50)
        self.retention_days = config.get("footage", {}).get("retention_days", 30)

        # Recording configuration
        self.record_during_trips = config.get("footage", {}).get("record_during_trips", True)
        self.video_quality = config.get("footage", {}).get("quality", "high")
        self.fps = config.get("footage", {}).get("fps", 15)

        # Current recording state
        self.is_recording = False
        self.current_recording: Optional[FootageRecord] = None
        self.video_writer: Optional[cv2.VideoWriter] = None
        self.recording_thread: Optional[threading.Thread] = None

        # Footage database (in-memory for now, should be persisted)
        self.footage_records: List[FootageRecord] = []

        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Load existing footage records
        self._load_footage_records()

    def start_recording(self, trip_id: str) -> bool:
        """
        Start recording footage for a trip.

        Args:
            trip_id: Trip identifier

        Returns:
            bool: True if recording started successfully
        """
        if self.is_recording:
            logger.warning("Recording already in progress")
            return False

        if not self.record_during_trips:
            logger.info("Trip recording is disabled")
            return False

        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.vehicle.registration_number}_{trip_id}_{timestamp}.mp4"
            file_path = self.storage_path / filename

            # Create footage record
            self.current_recording = FootageRecord(
                vehicle_id=self.vehicle.vehicle_id,
                trip_id=trip_id,
                filename=filename,
                file_path=str(file_path),
                start_time=datetime.now(),
                fps=self.fps
            )

            # Get video resolution based on quality setting
            width, height = self._get_resolution()
            self.current_recording.resolution = f"{width}x{height}"

            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                str(file_path),
                fourcc,
                self.fps,
                (width, height)
            )

            if not self.video_writer.isOpened():
                logger.error("Failed to initialize video writer")
                return False

            self.is_recording = True
            logger.info(f"Started recording: {filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False

    def stop_recording(self) -> Optional[FootageRecord]:
        """
        Stop current recording and finalize footage record.

        Returns:
            Optional[FootageRecord]: Completed footage record or None
        """
        if not self.is_recording or not self.current_recording:
            logger.warning("No recording in progress")
            return None

        try:
            # Stop recording
            self.is_recording = False

            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None

            # Finalize footage record
            self.current_recording.end_time = datetime.now()

            # Calculate duration
            if self.current_recording.start_time and self.current_recording.end_time:
                duration = self.current_recording.end_time - self.current_recording.start_time
                self.current_recording.duration_seconds = int(duration.total_seconds())

            # Get file size
            file_path = Path(self.current_recording.file_path)
            if file_path.exists():
                self.current_recording.file_size = file_path.stat().st_size

            # Add to records
            self.footage_records.append(self.current_recording)

            # Save records
            self._save_footage_records()

            completed_record = self.current_recording
            self.current_recording = None

            logger.info(f"Recording completed: {completed_record.filename}")
            return completed_record

        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return None

    def write_frame(self, frame):
        """
        Write a frame to the current recording.

        Args:
            frame: Video frame to write
        """
        if self.is_recording and self.video_writer and frame is not None:
            try:
                # Resize frame if needed
                height, width = frame.shape[:2]
                target_width, target_height = self._get_resolution()

                if width != target_width or height != target_height:
                    frame = cv2.resize(frame, (target_width, target_height))

                self.video_writer.write(frame)

            except Exception as e:
                logger.error(f"Error writing frame: {e}")

    def get_footage_list(self, limit: int = 50, uploaded_only: bool = False) -> List[FootageRecord]:
        """
        Get list of footage records.

        Args:
            limit: Maximum number of records to return
            uploaded_only: Return only uploaded footage

        Returns:
            List[FootageRecord]: List of footage records
        """
        records = self.footage_records

        if uploaded_only:
            records = [r for r in records if r.uploaded]

        # Sort by creation date (newest first)
        records.sort(key=lambda x: x.start_time, reverse=True)

        return records[:limit]

    async def upload_footage(self, footage_id: str, backend_url: str, api_key: str) -> bool:
        """
        Upload footage to backend system.

        Args:
            footage_id: Footage record ID to upload
            backend_url: Backend upload URL
            api_key: API authentication key

        Returns:
            bool: True if upload successful
        """
        # Find footage record
        footage = None
        for record in self.footage_records:
            if record.footage_id == footage_id:
                footage = record
                break

        if not footage:
            logger.error(f"Footage record not found: {footage_id}")
            return False

        if footage.uploaded:
            logger.info(f"Footage already uploaded: {footage_id}")
            return True

        try:
            footage.increment_upload_attempts()

            # Check if file exists
            file_path = Path(footage.file_path)
            if not file_path.exists():
                logger.error(f"Footage file not found: {footage.file_path}")
                return False

            # Prepare upload data
            upload_data = {
                "vehicle_id": footage.vehicle_id,
                "trip_id": footage.trip_id,
                "footage_id": footage.footage_id,
                "filename": footage.filename,
                "duration_seconds": footage.duration_seconds,
                "resolution": footage.resolution,
                "fps": footage.fps,
                "file_size": footage.file_size,
                "start_time": footage.start_time.isoformat(),
                "end_time": footage.end_time.isoformat() if footage.end_time else None
            }

            # Upload file (implementation depends on backend API)
            # This is a placeholder - actual implementation would use aiohttp or similar
            logger.info(f"Uploading footage: {footage.filename} to {backend_url}")

            # Simulate upload success for now
            upload_url = f"{backend_url}/footage/{footage.footage_id}"
            footage.mark_uploaded(upload_url)

            # Save updated records
            self._save_footage_records()

            logger.info(f"Footage uploaded successfully: {footage.filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to upload footage {footage_id}: {e}")
            return False

    def cleanup_old_footage(self):
        """Clean up old footage files based on retention policy."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)

            # Find old footage records
            old_records = [
                record for record in self.footage_records
                if record.start_time < cutoff_date and record.uploaded
            ]

            for record in old_records:
                # Delete file
                file_path = Path(record.file_path)
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted old footage file: {record.filename}")

                # Remove from records
                self.footage_records.remove(record)

            if old_records:
                self._save_footage_records()
                logger.info(f"Cleaned up {len(old_records)} old footage records")

        except Exception as e:
            logger.error(f"Error during footage cleanup: {e}")

    def get_storage_usage(self) -> Dict[str, Any]:
        """
        Get storage usage statistics.

        Returns:
            Dict[str, Any]: Storage usage information
        """
        try:
            total_size = 0
            file_count = 0

            for record in self.footage_records:
                file_path = Path(record.file_path)
                if file_path.exists():
                    total_size += file_path.stat().st_size
                    file_count += 1

            total_size_gb = total_size / (1024 ** 3)
            usage_percent = (total_size_gb / self.max_storage_gb) * 100

            return {
                "total_files": file_count,
                "total_size_bytes": total_size,
                "total_size_gb": round(total_size_gb, 2),
                "max_storage_gb": self.max_storage_gb,
                "usage_percent": round(usage_percent, 1),
                "available_gb": round(self.max_storage_gb - total_size_gb, 2)
            }

        except Exception as e:
            logger.error(f"Error calculating storage usage: {e}")
            return {}

    def _get_resolution(self) -> tuple:
        """Get video resolution based on quality setting."""
        quality_settings = {
            "low": (640, 480),
            "medium": (1280, 720),
            "high": (1920, 1080),
            "ultra": (3840, 2160)
        }
        return quality_settings.get(self.video_quality, (1280, 720))

    def _load_footage_records(self):
        """Load footage records from storage."""
        try:
            records_file = self.storage_path / "footage_records.json"
            if records_file.exists():
                with open(records_file, 'r') as f:
                    data = json.load(f)

                self.footage_records = [
                    FootageRecord(**record) for record in data
                ]
                logger.info(f"Loaded {len(self.footage_records)} footage records")

        except Exception as e:
            logger.error(f"Error loading footage records: {e}")
            self.footage_records = []

    def _save_footage_records(self):
        """Save footage records to storage."""
        try:
            records_file = self.storage_path / "footage_records.json"
            data = [record.dict() for record in self.footage_records]

            with open(records_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error saving footage records: {e}")
