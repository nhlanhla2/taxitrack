#!/usr/bin/env python3
"""
Live Streaming API Server

FastAPI server for taxi live streaming with your camera at 192.168.8.200
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import cv2
import json
import logging
from datetime import datetime
from typing import Dict, Any
import asyncio
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Taxi Live Streaming API",
    description="Live streaming API for HDJ864L taxi camera",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
CAMERA_URL = "rtsp://admin:Random336%23@192.168.8.200:554/stream1"
active_streams = {}
stream_stats = {
    "total_connections": 0,
    "current_viewers": 0,
    "uptime_seconds": 0,
    "frames_served": 0,
    "start_time": datetime.now()
}


class CameraStream:
    """Camera stream handler."""
    
    def __init__(self, camera_url: str):
        self.camera_url = camera_url
        self.cap = None
        self.running = False
        self.frame = None
        self.frame_count = 0
        
    def start(self):
        """Start camera stream."""
        try:
            self.cap = cv2.VideoCapture(self.camera_url)
            if not self.cap.isOpened():
                logger.error("Failed to open camera")
                return False
            
            self.running = True
            self.thread = threading.Thread(target=self._capture_frames)
            self.thread.daemon = True
            self.thread.start()
            
            logger.info("Camera stream started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start camera: {e}")
            return False
    
    def _capture_frames(self):
        """Capture frames in background thread."""
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.frame = frame
                self.frame_count += 1
                stream_stats["frames_served"] = self.frame_count
            time.sleep(1/30)  # 30 FPS
    
    def get_frame(self):
        """Get current frame."""
        return self.frame
    
    def stop(self):
        """Stop camera stream."""
        self.running = False
        if self.cap:
            self.cap.release()
        logger.info("Camera stream stopped")


# Initialize camera stream
camera_stream = CameraStream(CAMERA_URL)


@app.on_event("startup")
async def startup_event():
    """Start camera on server startup."""
    logger.info("Starting taxi live streaming server...")
    logger.info(f"Camera URL: {CAMERA_URL}")
    
    if camera_stream.start():
        logger.info("✅ Camera stream initialized")
    else:
        logger.error("❌ Failed to initialize camera stream")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop camera on server shutdown."""
    camera_stream.stop()
    logger.info("Server shutdown complete")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Taxi Live Streaming API",
        "vehicle": "HDJ864L",
        "camera": "192.168.8.200",
        "status": "active" if camera_stream.running else "inactive",
        "endpoints": {
            "stream_info": "/api/v1/footage/HDJ864L/live",
            "start_stream": "/api/v1/footage/HDJ864L/live/start",
            "stop_stream": "/api/v1/footage/HDJ864L/live/stop",
            "active_streams": "/api/v1/footage/live/active",
            "health": "/health",
            "stats": "/stats"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "camera_connected": camera_stream.running,
        "uptime_seconds": (datetime.now() - stream_stats["start_time"]).total_seconds(),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/stats")
async def get_stats():
    """Get streaming statistics."""
    uptime = (datetime.now() - stream_stats["start_time"]).total_seconds()
    
    return {
        "vehicle_id": "HDJ864L_001",
        "registration_number": "HDJ864L",
        "camera_ip": "192.168.8.200",
        "stream_status": "active" if camera_stream.running else "inactive",
        "uptime_seconds": uptime,
        "frames_captured": camera_stream.frame_count,
        "current_viewers": stream_stats["current_viewers"],
        "total_connections": stream_stats["total_connections"],
        "start_time": stream_stats["start_time"].isoformat(),
        "last_updated": datetime.now().isoformat()
    }


@app.get("/api/v1/footage/HDJ864L/live")
async def get_live_stream_info():
    """Get live stream information for HDJ864L."""
    if not camera_stream.running:
        raise HTTPException(status_code=404, detail="Camera stream not active")
    
    stream_stats["total_connections"] += 1
    
    return {
        "vehicle_id": "HDJ864L_001",
        "registration_number": "HDJ864L",
        "stream_id": "HDJ864L_live_stream",
        "stream_status": "active",
        "camera_ip": "192.168.8.200",
        "stream_urls": {
            "high": "http://localhost:8000/stream/high.m3u8",
            "medium": "http://localhost:8000/stream/medium.m3u8",
            "low": "http://localhost:8000/stream/low.m3u8",
            "websocket": "ws://localhost:8000/ws/stream/HDJ864L"
        },
        "quality_options": [
            {
                "quality": "high",
                "resolution": "1920x1080",
                "bitrate": "2000kbps",
                "url": "http://localhost:8000/stream/high.m3u8"
            },
            {
                "quality": "medium",
                "resolution": "1280x720",
                "bitrate": "1000kbps",
                "url": "http://localhost:8000/stream/medium.m3u8"
            },
            {
                "quality": "low",
                "resolution": "640x480",
                "bitrate": "500kbps",
                "url": "http://localhost:8000/stream/low.m3u8"
            }
        ],
        "metadata": {
            "current_viewers": stream_stats["current_viewers"],
            "start_time": stream_stats["start_time"].isoformat(),
            "uptime_seconds": (datetime.now() - stream_stats["start_time"]).total_seconds(),
            "frames_captured": camera_stream.frame_count,
            "camera_status": "connected" if camera_stream.running else "disconnected"
        }
    }


@app.post("/api/v1/footage/HDJ864L/live/start")
async def start_live_stream():
    """Start live streaming for HDJ864L."""
    if camera_stream.running:
        return {
            "message": "Stream already active",
            "stream_id": "HDJ864L_live_stream",
            "status": "active"
        }
    
    if camera_stream.start():
        return {
            "stream_id": "HDJ864L_live_stream",
            "vehicle_id": "HDJ864L_001",
            "status": "active",
            "started_at": datetime.now().isoformat(),
            "message": "Live stream started successfully"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to start camera stream")


@app.post("/api/v1/footage/HDJ864L/live/stop")
async def stop_live_stream():
    """Stop live streaming for HDJ864L."""
    camera_stream.stop()
    
    return {
        "stream_id": "HDJ864L_live_stream",
        "vehicle_id": "HDJ864L_001",
        "status": "stopped",
        "stopped_at": datetime.now().isoformat(),
        "message": "Live stream stopped successfully"
    }


@app.get("/api/v1/footage/live/active")
async def get_active_streams():
    """Get all active live streams."""
    active_streams_list = []

    if camera_stream.running:
        active_streams_list.append({
            "vehicle_id": "HDJ864L_001",
            "registration_number": "HDJ864L",
            "stream_id": "HDJ864L_live_stream",
            "status": "active",
            "viewers": stream_stats["current_viewers"],
            "started_at": stream_stats["start_time"].isoformat(),
            "uptime_seconds": (datetime.now() - stream_stats["start_time"]).total_seconds(),
            "camera_ip": "192.168.8.200"
        })

    return {
        "active_streams": active_streams_list,
        "total_active": len(active_streams_list),
        "timestamp": datetime.now().isoformat()
    }


def generate_video_stream():
    """Generate video stream from camera."""
    import numpy as np

    while True:
        frame = camera_stream.get_frame()
        if frame is not None:
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            # Send a placeholder frame if camera is not available
            placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(placeholder, 'Camera Connecting...', (150, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', placeholder)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        time.sleep(1/30)  # 30 FPS


@app.get("/video_feed")
async def video_feed():
    """Live video feed endpoint."""
    if not camera_stream.running:
        raise HTTPException(status_code=404, detail="Camera stream not active")

    stream_stats["current_viewers"] += 1

    return StreamingResponse(
        generate_video_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/viewer")
async def get_viewer_page():
    """Simple HTML viewer page."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>HDJ864L Live Camera Feed</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f0f0f0;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .header {
                text-align: center;
                margin-bottom: 20px;
                padding-bottom: 20px;
                border-bottom: 2px solid #007bff;
            }
            .video-container {
                text-align: center;
                margin: 20px 0;
            }
            .video-stream {
                max-width: 100%;
                height: auto;
                border: 3px solid #007bff;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            .info-panel {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .info-card {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #007bff;
            }
            .info-card h3 {
                margin: 0 0 10px 0;
                color: #007bff;
            }
            .status-active { color: #28a745; font-weight: bold; }
            .refresh-btn {
                background: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                margin: 10px;
            }
            .refresh-btn:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚖 HDJ864L Live Camera Feed</h1>
                <p><strong>Camera IP:</strong> 192.168.8.200 | <strong>Status:</strong> <span class="status-active">LIVE</span></p>
            </div>

            <div class="video-container">
                <img src="/video_feed" alt="Live Camera Feed" class="video-stream" id="videoStream">
                <br>
                <button class="refresh-btn" onclick="refreshStream()">🔄 Refresh Stream</button>
                <button class="refresh-btn" onclick="toggleFullscreen()">🖥️ Fullscreen</button>
            </div>

            <div class="info-panel">
                <div class="info-card">
                    <h3>🚐 Vehicle Info</h3>
                    <p><strong>Registration:</strong> HDJ864L</p>
                    <p><strong>Make/Model:</strong> Toyota Quantum</p>
                    <p><strong>Capacity:</strong> 14 passengers</p>
                    <p><strong>Fleet:</strong> Cape Town</p>
                </div>

                <div class="info-card">
                    <h3>📹 Stream Info</h3>
                    <p><strong>Resolution:</strong> 1920x1080</p>
                    <p><strong>FPS:</strong> 30</p>
                    <p><strong>Protocol:</strong> RTSP</p>
                    <p><strong>Quality:</strong> High</p>
                </div>

                <div class="info-card">
                    <h3>🌐 API Endpoints</h3>
                    <p><a href="/stats" target="_blank">📊 Statistics</a></p>
                    <p><a href="/health" target="_blank">❤️ Health Check</a></p>
                    <p><a href="/api/v1/footage/HDJ864L/live" target="_blank">📡 Stream Info</a></p>
                    <p><a href="/api/v1/footage/live/active" target="_blank">🎥 Active Streams</a></p>
                </div>

                <div class="info-card">
                    <h3>⚡ Quick Actions</h3>
                    <p><button class="refresh-btn" onclick="startStream()">▶️ Start Stream</button></p>
                    <p><button class="refresh-btn" onclick="stopStream()">⏹️ Stop Stream</button></p>
                    <p><button class="refresh-btn" onclick="getStats()">📈 View Stats</button></p>
                </div>
            </div>
        </div>

        <script>
            function refreshStream() {
                const img = document.getElementById('videoStream');
                img.src = '/video_feed?' + new Date().getTime();
            }

            function toggleFullscreen() {
                const img = document.getElementById('videoStream');
                if (img.requestFullscreen) {
                    img.requestFullscreen();
                }
            }

            function startStream() {
                fetch('/api/v1/footage/HDJ864L/live/start', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => alert('Stream started: ' + data.message))
                    .catch(error => alert('Error: ' + error));
            }

            function stopStream() {
                fetch('/api/v1/footage/HDJ864L/live/stop', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => alert('Stream stopped: ' + data.message))
                    .catch(error => alert('Error: ' + error));
            }

            function getStats() {
                window.open('/stats', '_blank');
            }

            // Auto-refresh stream every 30 seconds to prevent stale connections
            setInterval(refreshStream, 30000);
        </script>
    </body>
    </html>
    """

    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)


# Mobile App Endpoints
@app.get("/mobile/vehicles")
async def get_vehicles_list():
    """Get list of all vehicles for mobile app."""
    vehicles = []

    if camera_stream.running:
        vehicles.append({
            "vehicle_id": "HDJ864L_001",
            "registration_number": "HDJ864L",
            "make": "Toyota",
            "model": "Quantum",
            "capacity": 14,
            "fleet_id": "cape_town_fleet_001",
            "camera_ip": "192.168.8.200",
            "status": "active",
            "location": {
                "city": "Cape Town",
                "route": "Main Route"
            },
            "stream_available": True,
            "last_seen": datetime.now().isoformat()
        })

    return {
        "vehicles": vehicles,
        "total_count": len(vehicles),
        "active_count": len([v for v in vehicles if v["status"] == "active"]),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/mobile/vehicle/{registration_number}")
async def get_vehicle_details(registration_number: str):
    """Get specific vehicle details for mobile app."""
    if registration_number.upper() != "HDJ864L":
        raise HTTPException(status_code=404, detail="Vehicle not found")

    uptime = (datetime.now() - stream_stats["start_time"]).total_seconds()

    return {
        "vehicle_id": "HDJ864L_001",
        "registration_number": "HDJ864L",
        "make": "Toyota",
        "model": "Quantum",
        "year": 2020,
        "color": "White",
        "capacity": 14,
        "fleet_id": "cape_town_fleet_001",
        "camera": {
            "ip": "192.168.8.200",
            "status": "connected" if camera_stream.running else "disconnected",
            "resolution": "1920x1080",
            "fps": 30
        },
        "location": {
            "city": "Cape Town",
            "route": "Main Route",
            "coordinates": {
                "latitude": -33.9249,
                "longitude": 18.4241
            }
        },
        "stream": {
            "available": camera_stream.running,
            "uptime_seconds": uptime,
            "frames_captured": camera_stream.frame_count,
            "current_viewers": stream_stats["current_viewers"]
        },
        "mobile_endpoints": {
            "live_stream": f"/mobile/vehicle/{registration_number}/stream",
            "thumbnail": f"/mobile/vehicle/{registration_number}/thumbnail",
            "stream_info": f"/mobile/vehicle/{registration_number}/stream/info"
        },
        "last_updated": datetime.now().isoformat()
    }


@app.api_route("/mobile/vehicle/{registration_number}/stream", methods=["GET", "HEAD"])
async def get_mobile_video_stream(registration_number: str, quality: str = "medium", request: Request = None):
    """Mobile-optimized video stream for specific vehicle."""
    # Support multiple vehicles - add your vehicle registrations here
    supported_vehicles = ["HDJ864L", "HFT279L"]  # Add more as needed
    if registration_number.upper() not in supported_vehicles:
        raise HTTPException(status_code=404, detail=f"Vehicle {registration_number} not found. Supported: {supported_vehicles}")

    if not camera_stream.running:
        raise HTTPException(status_code=503, detail="Camera stream not available")

    # Handle HEAD requests - just return headers without body
    if request and request.method == "HEAD":
        return Response(
            status_code=200,
            headers={
                "Content-Type": "multipart/x-mixed-replace; boundary=frame",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "Access-Control-Allow-Origin": "*"
            }
        )

    stream_stats["current_viewers"] += 1

    def generate_mobile_stream():
        """Generate mobile-optimized video stream."""
        import numpy as np

        while True:
            frame = camera_stream.get_frame()
            if frame is not None:
                # Resize based on quality for mobile
                if quality == "low":
                    frame = cv2.resize(frame, (480, 360))
                    jpeg_quality = 60
                elif quality == "medium":
                    frame = cv2.resize(frame, (720, 540))
                    jpeg_quality = 75
                else:  # high
                    jpeg_quality = 85

                # Add vehicle info overlay
                cv2.putText(frame, f"HDJ864L - {datetime.now().strftime('%H:%M:%S')}",
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Viewers: {stream_stats['current_viewers']}",
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # Send placeholder frame
                placeholder = np.zeros((360, 480, 3), dtype=np.uint8)
                cv2.putText(placeholder, 'HDJ864L - Connecting...', (100, 180),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                ret, buffer = cv2.imencode('.jpg', placeholder)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            time.sleep(1/15)  # 15 FPS for mobile to save bandwidth

    return StreamingResponse(
        generate_mobile_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.get("/mobile/vehicle/{registration_number}/thumbnail")
async def get_vehicle_thumbnail(registration_number: str):
    """Get current thumbnail image for vehicle."""
    if registration_number.upper() != "HDJ864L":
        raise HTTPException(status_code=404, detail="Vehicle not found")

    if not camera_stream.running:
        raise HTTPException(status_code=503, detail="Camera stream not available")

    frame = camera_stream.get_frame()
    if frame is not None:
        # Resize to thumbnail size
        thumbnail = cv2.resize(frame, (320, 240))

        # Add vehicle overlay
        cv2.putText(thumbnail, "HDJ864L", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(thumbnail, datetime.now().strftime('%H:%M:%S'), (10, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Encode as JPEG
        ret, buffer = cv2.imencode('.jpg', thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ret:
            from fastapi.responses import Response
            return Response(content=buffer.tobytes(), media_type="image/jpeg")

    raise HTTPException(status_code=503, detail="Unable to capture thumbnail")


@app.api_route("/mobile/vehicle/{registration_number}/stream/info", methods=["GET", "HEAD"])
async def get_mobile_stream_info(registration_number: str, request: Request = None):
    """Get stream information for mobile app."""
    # Support multiple vehicles
    supported_vehicles = ["HDJ864L", "HFT279L"]  # Add more as needed
    if registration_number.upper() not in supported_vehicles:
        raise HTTPException(status_code=404, detail=f"Vehicle {registration_number} not found. Supported: {supported_vehicles}")

    # Handle HEAD requests
    if request and request.method == "HEAD":
        return Response(status_code=200, headers={"Content-Type": "application/json"})

    base_url = "http://localhost:8000"  # In production, use your actual domain

    return {
        "vehicle_id": f"{registration_number.upper()}_001",
        "registration_number": registration_number.upper(),
        "stream_status": "active" if camera_stream.running else "inactive",
        "mobile_streams": {
            "low": {
                "url": f"{base_url}/mobile/vehicle/{registration_number}/stream?quality=low",
                "resolution": "480x360",
                "fps": 15,
                "bandwidth": "~200KB/s"
            },
            "medium": {
                "url": f"{base_url}/mobile/vehicle/{registration_number}/stream?quality=medium",
                "resolution": "720x540",
                "fps": 15,
                "bandwidth": "~400KB/s"
            },
            "high": {
                "url": f"{base_url}/mobile/vehicle/{registration_number}/stream?quality=high",
                "resolution": "1920x1080",
                "fps": 15,
                "bandwidth": "~800KB/s"
            }
        },
        "thumbnail_url": f"{base_url}/mobile/vehicle/{registration_number}/thumbnail",
        "websocket_url": f"ws://localhost:8000/ws/vehicle/{registration_number}",
        "current_viewers": stream_stats["current_viewers"],
        "uptime_seconds": (datetime.now() - stream_stats["start_time"]).total_seconds(),
        "last_updated": datetime.now().isoformat()
    }


if __name__ == "__main__":
    logger.info("🚖 Starting Taxi Live Streaming Server")
    logger.info("🎥 Camera: 192.168.8.200 (HDJ864L)")
    logger.info("🌐 Server: http://localhost:8000")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
