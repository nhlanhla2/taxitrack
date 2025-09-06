#!/usr/bin/env python3
"""
Mini Bus Taxi Passenger Counting System - Main Application

Entry point for the passenger counting system that integrates all components:
- Camera stream processing
- Computer vision for person detection
- Face tracking for anti-fraud
- Trip management and API
- Backend integration

Usage:
    python main.py [--config config.yaml] [--debug] [--mock-camera]
"""

import asyncio
import argparse
import logging
import signal
import sys
import yaml
from pathlib import Path
from typing import Dict, Any

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/taxi_counter.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

# Import application modules
from src.computer_vision import PassengerCounter
from src.face_tracking import AntiFraudManager


class TaxiCounterApplication:
    """
    Main application class that orchestrates all system components.
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the taxi counter application.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.is_running = False

        # Initialize components
        self.passenger_counter = None
        self.anti_fraud_manager = None

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.error(f"Configuration file not found: {self.config_path}")
                # Create default config
                return self._create_default_config()

            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            logger.info(f"Configuration loaded from {self.config_path}")
            return config

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """
        Create default configuration for development/testing.

        Returns:
            Dict[str, Any]: Default configuration
        """
        return {
            "camera": {
                "type": "usb",
                "usb_camera_index": 0,
                "width": 640,
                "height": 480,
                "fps": 15
            },
            "computer_vision": {
                "detection_model": "yolov8n.pt",
                "confidence_threshold": 0.5,
                "nms_threshold": 0.4,
                "roi": [0.0, 0.0, 1.0, 1.0],
                "entry_zone": [0.0, 0.0, 0.5, 1.0],
                "exit_zone": [0.5, 0.0, 1.0, 1.0]
            },
            "face_tracking": {
                "model": "hog",
                "tolerance": 0.6,
                "max_tracking_time": 10,
                "min_face_size": 50
            },
            "trip": {
                "max_capacity": 14,
                "timeout_minutes": 120,
                "min_duration": 60
            },
            "system": {
                "device_id": "taxi_dev_001"
            },
            "development": {
                "debug": True,
                "mock_camera": False
            }
        }

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()

    async def initialize(self) -> bool:
        """
        Initialize all system components.

        Returns:
            bool: True if initialization successful
        """
        try:
            logger.info("Initializing Taxi Counter Application...")

            # Create required directories
            Path("logs").mkdir(exist_ok=True)
            Path("data").mkdir(exist_ok=True)

            # Initialize passenger counter
            logger.info("Initializing passenger counter...")
            self.passenger_counter = PassengerCounter(self.config)

            # Initialize anti-fraud manager
            logger.info("Initializing anti-fraud manager...")
            self.anti_fraud_manager = AntiFraudManager(self.config["face_tracking"])

            # Setup event callbacks
            self.passenger_counter.add_event_callback(self._on_passenger_event)

            logger.info("Application initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            return False

    async def start(self) -> bool:
        """
        Start the application and all components.

        Returns:
            bool: True if started successfully
        """
        try:
            if not await self.initialize():
                return False

            logger.info("Starting Taxi Counter Application...")

            # Start passenger counter
            if not self.passenger_counter.start():
                logger.error("Failed to start passenger counter")
                return False

            self.is_running = True
            logger.info("Application started successfully")

            # Main application loop
            await self._main_loop()

            return True

        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            return False

    async def _main_loop(self):
        """Main application loop."""
        logger.info("Entering main application loop...")

        try:
            while self.is_running:
                # Get current statistics
                stats = self.passenger_counter.get_statistics()

                # Log status periodically
                if stats.get("processing_fps", 0) > 0:
                    logger.debug(f"Status - Count: {stats['current_passengers']}, "
                               f"FPS: {stats['processing_fps']:.1f}")

                # Sleep to prevent busy waiting
                await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            logger.info("Exiting main application loop")

    def _on_passenger_event(self, event):
        """
        Handle passenger events from the counter.

        Args:
            event: Passenger event object
        """
        logger.info(f"Passenger event: {event.event_type} at {event.timestamp}")

        # Here you would typically:
        # 1. Update trip records
        # 2. Send to backend API
        # 3. Log to database
        # 4. Trigger alerts if needed

    def shutdown(self):
        """Shutdown the application gracefully."""
        logger.info("Shutting down application...")
        self.is_running = False

        if self.passenger_counter:
            self.passenger_counter.stop()

        logger.info("Application shutdown complete")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current application status.

        Returns:
            Dict[str, Any]: Status information
        """
        status = {
            "is_running": self.is_running,
            "config_path": self.config_path,
            "device_id": self.config.get("system", {}).get("device_id", "unknown")
        }

        if self.passenger_counter:
            status["passenger_counter"] = self.passenger_counter.get_statistics()

        return status


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Mini Bus Taxi Passenger Counting System"
    )

    parser.add_argument(
        "--config", "-c",
        default="config/config.yaml",
        help="Path to configuration file"
    )

    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug logging"
    )

    parser.add_argument(
        "--mock-camera",
        action="store_true",
        help="Use mock camera for testing"
    )

    return parser.parse_args()


async def main():
    """Main application entry point."""
    args = parse_arguments()

    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug logging enabled")

    # Create application instance
    app = TaxiCounterApplication(config_path=args.config)

    # Override config for mock camera if requested
    if args.mock_camera:
        app.config["development"]["mock_camera"] = True
        logger.info("Mock camera mode enabled")

    try:
        # Start the application
        success = await app.start()

        if not success:
            logger.error("Failed to start application")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        app.shutdown()


if __name__ == "__main__":
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    # Run the application
    asyncio.run(main())
