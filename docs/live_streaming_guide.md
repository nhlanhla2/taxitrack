# Live Streaming Guide for Taxi Passenger Counting System

## Overview

The live streaming feature allows real-time monitoring of taxi vehicles through web browsers and mobile applications. Fleet managers, dispatchers, and authorized personnel can view live footage from any vehicle in the fleet for security, monitoring, and operational purposes.

## Features

### Core Capabilities
- **Real-time Video Streaming**: Live video feed from vehicle cameras
- **Multiple Quality Levels**: Adaptive streaming with low, medium, and high quality options
- **Multi-viewer Support**: Up to 10 concurrent viewers per stream
- **WebSocket Integration**: Real-time metadata and viewer count updates
- **Authentication & Authorization**: Secure access control for authorized users
- **Recording Integration**: Automatic recording of live streams
- **Mobile Responsive**: Works on desktop, tablet, and mobile devices

### Technical Features
- **HLS Streaming**: HTTP Live Streaming for broad compatibility
- **RTMP Support**: Real-Time Messaging Protocol for low latency
- **Adaptive Bitrate**: Automatic quality adjustment based on network conditions
- **Stream Analytics**: Viewer statistics and performance metrics
- **Error Recovery**: Automatic reconnection and error handling

## API Endpoints

### 1. Get Live Stream Information

**GET** `/api/v1/footage/{vehicle_id}/live`

Get live stream information for a specific vehicle.

**Example Request:**
```bash
curl -X GET "https://api.taxitrack.com/api/v1/footage/HDJ864L/live" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

**Example Response:**
```json
{
  "vehicle_id": "uuid",
  "registration_number": "HDJ864L",
  "stream_id": "stream_uuid",
  "stream_status": "active",
  "stream_urls": {
    "high": "https://stream.taxitrack.com/HDJ864L/high.m3u8",
    "medium": "https://stream.taxitrack.com/HDJ864L/medium.m3u8",
    "low": "https://stream.taxitrack.com/HDJ864L/low.m3u8",
    "websocket": "wss://stream.taxitrack.com/ws/stream/stream_uuid"
  },
  "quality_options": [
    {
      "quality": "high",
      "resolution": "1920x1080",
      "bitrate": "2000kbps",
      "url": "https://stream.taxitrack.com/HDJ864L/high.m3u8"
    },
    {
      "quality": "medium",
      "resolution": "1280x720",
      "bitrate": "1000kbps",
      "url": "https://stream.taxitrack.com/HDJ864L/medium.m3u8"
    },
    {
      "quality": "low",
      "resolution": "640x480",
      "bitrate": "500kbps",
      "url": "https://stream.taxitrack.com/HDJ864L/low.m3u8"
    }
  ],
  "metadata": {
    "current_viewers": 3,
    "start_time": "2024-01-01T12:00:00Z",
    "duration_seconds": 1800,
    "frames_streamed": 54000
  }
}
```

### 2. Start Live Stream

**POST** `/api/v1/footage/{vehicle_id}/live/start`

Start live streaming for a specific vehicle.

**Example Request:**
```bash
curl -X POST "https://api.taxitrack.com/api/v1/footage/HDJ864L/live/start" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quality": "high",
    "duration_minutes": 60,
    "max_viewers": 5,
    "auto_record": true,
    "authorized_viewers": ["fleet_admin", "dispatcher"]
  }'
```

### 3. Stop Live Stream

**POST** `/api/v1/footage/{vehicle_id}/live/stop`

Stop live streaming for a specific vehicle.

### 4. Get Active Streams

**GET** `/api/v1/footage/live/active`

Get list of all currently active live streams.

## WebSocket Integration

### Real-time Updates

Connect to the WebSocket endpoint for real-time stream metadata:

**WebSocket URL:** `wss://api.taxitrack.com/ws/stream/{stream_id}`

**Example Messages:**
```json
{
  "type": "stream_update",
  "stream_id": "stream_uuid",
  "timestamp": "2024-01-01T12:30:00Z",
  "data": {
    "status": "active",
    "viewers": 3,
    "uptime_seconds": 1800,
    "current_trip_id": "trip_uuid",
    "passenger_count": 8,
    "camera_status": "connected"
  }
}
```

## Frontend Integration

### HTML5 Video Player

```html
<!DOCTYPE html>
<html>
<head>
    <title>Live Stream - HDJ864L</title>
    <script src="https://vjs.zencdn.net/8.0.4/video.min.js"></script>
    <link href="https://vjs.zencdn.net/8.0.4/video-js.css" rel="stylesheet">
</head>
<body>
    <div class="stream-container">
        <h2>Live Stream - Vehicle HDJ864L</h2>

        <video
            id="live-stream"
            class="video-js vjs-default-skin"
            controls
            preload="auto"
            width="1280"
            height="720"
            data-setup="{}">
            <source src="https://stream.taxitrack.com/HDJ864L/medium.m3u8" type="application/x-mpegURL">
        </video>

        <div class="stream-info">
            <p>Viewers: <span id="viewer-count">0</span></p>
            <p>Passengers: <span id="passenger-count">0</span></p>
            <p>Status: <span id="stream-status">Loading...</span></p>
        </div>

        <div class="quality-selector">
            <button onclick="changeQuality('low')">Low (480p)</button>
            <button onclick="changeQuality('medium')">Medium (720p)</button>
            <button onclick="changeQuality('high')">High (1080p)</button>
        </div>
    </div>

    <script>
        const player = videojs('live-stream');

        function changeQuality(quality) {
            const baseUrl = 'https://stream.taxitrack.com/HDJ864L';
            const newSrc = `${baseUrl}/${quality}.m3u8`;

            player.src({
                src: newSrc,
                type: 'application/x-mpegURL'
            });
        }

        // Initialize WebSocket connection
        const streamId = 'your-stream-id';
        const ws = new WebSocket(`wss://api.taxitrack.com/ws/stream/${streamId}`);

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            document.getElementById('viewer-count').textContent = data.data.viewers;
            document.getElementById('passenger-count').textContent = data.data.passenger_count || 0;
            document.getElementById('stream-status').textContent = data.data.status;
        };
    </script>
</body>
</html>
```

## Mobile App Integration

### React Native Example

```javascript
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Video from 'react-native-video';

const LiveStreamScreen = ({ vehicleId }) => {
  const [streamInfo, setStreamInfo] = useState(null);
  const [quality, setQuality] = useState('medium');

  useEffect(() => {
    fetchStreamInfo();
  }, [vehicleId]);

  const fetchStreamInfo = async () => {
    try {
      const response = await fetch(`https://api.taxitrack.com/api/v1/footage/${vehicleId}/live`, {
        headers: {
          'Authorization': 'Bearer YOUR_API_TOKEN'
        }
      });
      const data = await response.json();
      setStreamInfo(data);
    } catch (error) {
      console.error('Error fetching stream info:', error);
    }
  };

  if (!streamInfo) {
    return <Text>Loading stream...</Text>;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Live Stream - {streamInfo.registration_number}</Text>

      <Video
        source={{ uri: streamInfo.stream_urls[quality] }}
        style={styles.video}
        controls={true}
        resizeMode="contain"
      />

      <View style={styles.info}>
        <Text>Viewers: {streamInfo.metadata.current_viewers}</Text>
        <Text>Duration: {Math.floor(streamInfo.metadata.duration_seconds / 60)} minutes</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  video: {
    width: '100%',
    height: 200,
    backgroundColor: 'black',
  },
  info: {
    marginTop: 16,
    padding: 16,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
  },
});

export default LiveStreamScreen;
```

## Security & Access Control

### Authentication

All live streaming endpoints require authentication via Bearer token:

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  "https://api.taxitrack.com/api/v1/footage/HDJ864L/live"
```

### Authorization Levels

- **Fleet Admin**: Can start/stop streams for all vehicles in fleet
- **Dispatcher**: Can view active streams and start emergency streams
- **Driver**: Can view their own vehicle's stream (if enabled)
- **Viewer**: Can only view streams they're explicitly authorized for

### Stream Encryption

All streams are encrypted using:
- **HTTPS/WSS**: Encrypted transport layer
- **HLS Encryption**: AES-128 encryption for video segments
- **Token-based Access**: Time-limited access tokens for stream URLs

## Performance Considerations

### Bandwidth Requirements

| Quality | Resolution | Bitrate | Bandwidth (per viewer) |
|---------|------------|---------|----------------------|
| Low     | 640x480    | 500kbps | 0.5 Mbps            |
| Medium  | 1280x720   | 1000kbps| 1.0 Mbps            |
| High    | 1920x1080  | 2000kbps| 2.0 Mbps            |

### Scaling Recommendations

- **CDN Integration**: Use CDN for global stream distribution
- **Load Balancing**: Distribute streams across multiple servers
- **Adaptive Bitrate**: Implement automatic quality switching
- **Caching**: Cache stream segments for improved performance

## Troubleshooting

### Common Issues

1. **Stream Not Starting**
   - Check camera connectivity
   - Verify network bandwidth
   - Confirm authentication tokens

2. **Poor Video Quality**
   - Check network conditions
   - Try lower quality setting
   - Verify camera settings

3. **High Latency**
   - Use RTMP for lower latency
   - Reduce HLS segment duration
   - Check network routing

### Monitoring

Monitor stream health using:
- Stream analytics dashboard
- WebSocket connection status
- Viewer count and engagement metrics
- Error logs and performance metrics

This comprehensive live streaming system provides real-time monitoring capabilities for your taxi fleet with professional-grade features and security.
