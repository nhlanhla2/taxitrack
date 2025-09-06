"""
Backend Integration Module

Handles communication with backend systems, including trip data sync,
footage upload, and real-time updates.
"""

from .api_client import BackendAPIClient
from .sync_manager import SyncManager
from .models import SyncStatus, APIResponse

__all__ = [
    "BackendAPIClient",
    "SyncManager",
    "SyncStatus",
    "APIResponse"
]
