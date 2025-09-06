"""
Face Tracking Module for Anti-Fraud Features

This module provides face recognition and tracking capabilities to prevent
double counting and handle temporary passenger exits/re-entries.
"""

from .face_tracker import FaceTracker
from .face_database import FaceDatabase
from .anti_fraud_manager import AntiFraudManager

__all__ = [
    "FaceTracker",
    "FaceDatabase",
    "AntiFraudManager"
]
