#!/usr/bin/env python3
"""
Face Database Module

Manages a database of known faces for passenger identification and anti-fraud.
This is a stub implementation that can be extended with actual database functionality.
"""

import logging
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class FaceDatabase:
    """
    Database for storing and retrieving face encodings and passenger information.
    
    This is a simplified stub implementation. In production, this would connect
    to a proper database system.
    """
    
    def __init__(self, db_path: str = "data/faces.db"):
        """
        Initialize face database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.enabled = False  # Disabled for now since face_recognition is not available
        
        if self.enabled:
            self._init_database()
            logger.info(f"FaceDatabase initialized at {db_path}")
        else:
            logger.warning("FaceDatabase disabled - face recognition not available")
    
    def _init_database(self):
        """Initialize database tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS faces (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        face_id TEXT UNIQUE NOT NULL,
                        encoding BLOB NOT NULL,
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        passenger_info TEXT,
                        status TEXT DEFAULT 'active'
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS face_sightings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        face_id TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        confidence REAL,
                        location TEXT,
                        FOREIGN KEY (face_id) REFERENCES faces (face_id)
                    )
                """)
                
                conn.commit()
                logger.info("Database tables initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def add_face(self, face_id: str, encoding: np.ndarray, passenger_info: Optional[Dict] = None) -> bool:
        """
        Add a new face to the database.
        
        Args:
            face_id: Unique identifier for the face
            encoding: Face encoding vector
            passenger_info: Optional passenger information
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            encoding_blob = encoding.tobytes()
            info_str = str(passenger_info) if passenger_info else None
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO faces (face_id, encoding, passenger_info)
                    VALUES (?, ?, ?)
                """, (face_id, encoding_blob, info_str))
                conn.commit()
                
            logger.debug(f"Added face {face_id} to database")
            return True
        except Exception as e:
            logger.error(f"Failed to add face {face_id}: {e}")
            return False
    
    def find_matching_face(self, encoding: np.ndarray, threshold: float = 0.6) -> Optional[str]:
        """
        Find a matching face in the database.
        
        Args:
            encoding: Face encoding to match
            threshold: Similarity threshold
            
        Returns:
            Optional[str]: Face ID if match found, None otherwise
        """
        if not self.enabled:
            return None
            
        # This would require face_recognition library for actual matching
        # For now, return None (no matches)
        return None
    
    def update_last_seen(self, face_id: str) -> bool:
        """
        Update the last seen timestamp for a face.
        
        Args:
            face_id: Face identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE faces SET last_seen = CURRENT_TIMESTAMP
                    WHERE face_id = ?
                """, (face_id,))
                conn.commit()
                
            return True
        except Exception as e:
            logger.error(f"Failed to update last seen for {face_id}: {e}")
            return False
    
    def record_sighting(self, face_id: str, confidence: float, location: str = "unknown") -> bool:
        """
        Record a face sighting.
        
        Args:
            face_id: Face identifier
            confidence: Detection confidence
            location: Location of sighting
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO face_sightings (face_id, confidence, location)
                    VALUES (?, ?, ?)
                """, (face_id, confidence, location))
                conn.commit()
                
            return True
        except Exception as e:
            logger.error(f"Failed to record sighting for {face_id}: {e}")
            return False
    
    def get_face_info(self, face_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a face.
        
        Args:
            face_id: Face identifier
            
        Returns:
            Optional[Dict]: Face information if found, None otherwise
        """
        if not self.enabled:
            return None
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT face_id, first_seen, last_seen, passenger_info, status
                    FROM faces WHERE face_id = ?
                """, (face_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "face_id": row[0],
                        "first_seen": row[1],
                        "last_seen": row[2],
                        "passenger_info": row[3],
                        "status": row[4]
                    }
                    
            return None
        except Exception as e:
            logger.error(f"Failed to get face info for {face_id}: {e}")
            return None
    
    def get_recent_faces(self, hours: int = 24) -> List[str]:
        """
        Get faces seen in the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List[str]: List of face IDs
        """
        if not self.enabled:
            return []
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT face_id FROM face_sightings
                    WHERE timestamp > datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                """.format(hours))
                
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get recent faces: {e}")
            return []
    
    def cleanup_old_faces(self, days: int = 30) -> int:
        """
        Clean up old face records.
        
        Args:
            days: Number of days to keep records
            
        Returns:
            int: Number of records cleaned up
        """
        if not self.enabled:
            return 0
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM faces
                    WHERE last_seen < datetime('now', '-{} days')
                """.format(days))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} old face records")
                return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old faces: {e}")
            return 0
