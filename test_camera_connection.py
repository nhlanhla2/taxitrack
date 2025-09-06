#!/usr/bin/env python3
"""
Camera Connection Test Script
Tests connectivity to your IP camera
"""

import requests
import subprocess
import sys
from urllib.parse import quote

def test_camera_connection(camera_ip, username, password):
    """Test if we can connect to the camera"""
    
    print(f"🎥 Testing Camera Connection")
    print(f"📍 Camera IP: {camera_ip}")
    print(f"👤 Username: {username}")
    print(f"🔑 Password: {'*' * len(password)}")
    print("-" * 50)
    
    # Test 1: HTTP connection (camera web interface)
    print("\n1️⃣ Testing HTTP connection...")
    try:
        response = requests.get(f"http://{camera_ip}", timeout=10, auth=(username, password))
        print(f"✅ HTTP connection successful (Status: {response.status_code})")
        
        # Try HTTPS as well
        try:
            response_https = requests.get(f"https://{camera_ip}", timeout=10, auth=(username, password), verify=False)
            print(f"✅ HTTPS connection also available (Status: {response_https.status_code})")
        except:
            print("ℹ️ HTTPS not available (normal for many cameras)")
            
    except requests.exceptions.Timeout:
        print("❌ HTTP connection timed out")
    except requests.exceptions.ConnectionError:
        print("❌ HTTP connection failed - camera not reachable")
    except Exception as e:
        print(f"❌ HTTP connection failed: {e}")
    
    # Test 2: Ping test
    print("\n2️⃣ Testing network connectivity...")
    try:
        result = subprocess.run(['ping', '-c', '3', camera_ip], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Camera is reachable (ping successful)")
        else:
            print("❌ Camera is not reachable (ping failed)")
    except Exception as e:
        print(f"❌ Ping test failed: {e}")
    
    # Test 3: RTSP stream URL format
    print("\n3️⃣ Testing RTSP stream URL...")
    password_encoded = quote(password)
    rtsp_url = f"rtsp://{username}:{password_encoded}@{camera_ip}:554/stream1"
    print(f"📺 RTSP URL: {rtsp_url}")
    
    # Common alternative RTSP paths to try
    alternative_paths = [
        "/stream1",
        "/live/main",
        "/cam/realmonitor?channel=1&subtype=0",
        "/h264Preview_01_main",
        "/axis-media/media.amp",
        "/onvif1",
        "/video1",
        "/ch0_0.h264"
    ]
    
    print("🔍 Common RTSP paths to try:")
    for path in alternative_paths:
        alt_url = f"rtsp://{username}:{password_encoded}@{camera_ip}:554{path}"
        print(f"   • {alt_url}")
    
    # Test 4: Port connectivity
    print("\n4️⃣ Testing common camera ports...")
    common_ports = [80, 443, 554, 8080, 8081, 8888, 9000]
    
    for port in common_ports:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((camera_ip, port))
            sock.close()
            
            if result == 0:
                print(f"✅ Port {port} is open")
            else:
                print(f"❌ Port {port} is closed")
        except Exception as e:
            print(f"❌ Port {port} test failed: {e}")

def test_with_ffmpeg(camera_ip, username, password):
    """Test RTSP stream with ffmpeg if available"""
    print("\n5️⃣ Testing RTSP stream with ffmpeg...")
    
    password_encoded = quote(password)
    rtsp_url = f"rtsp://{username}:{password_encoded}@{camera_ip}:554/stream1"
    
    try:
        # Test if ffmpeg is available
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        
        print("📹 Testing RTSP stream (5 second test)...")
        result = subprocess.run([
            'ffmpeg', '-i', rtsp_url, '-t', '5', '-f', 'null', '-'
        ], capture_output=True, text=True, timeout=20)
        
        if result.returncode == 0:
            print("✅ RTSP stream test successful!")
        else:
            print(f"❌ RTSP stream test failed:")
            print(f"Error: {result.stderr}")
            
    except subprocess.CalledProcessError:
        print("❌ ffmpeg not available - install with: apt install ffmpeg")
    except subprocess.TimeoutExpired:
        print("⏳ RTSP stream test timed out (stream might be working but slow)")
    except Exception as e:
        print(f"❌ RTSP stream test error: {e}")

def main():
    # Camera configuration
    CAMERA_IP = "192.168.8.200"
    USERNAME = "admin"
    PASSWORD = "Random336#"
    
    print("🎯 Taxi Camera Connection Test")
    print("=" * 50)
    
    test_camera_connection(CAMERA_IP, USERNAME, PASSWORD)
    test_with_ffmpeg(CAMERA_IP, USERNAME, PASSWORD)
    
    print("\n" + "=" * 50)
    print("📋 Next Steps:")
    print("1. If HTTP connection failed:")
    print("   • Check camera is powered on")
    print("   • Verify camera IP address in router")
    print("   • Check network cable connection")
    print()
    print("2. If RTSP stream failed:")
    print("   • Try different RTSP paths shown above")
    print("   • Check camera's RTSP settings")
    print("   • Verify username/password")
    print()
    print("3. If all tests pass:")
    print("   • Your camera is ready!")
    print("   • Test the full system with: curl http://100.69.8.80:8000/mobile/vehicles")

if __name__ == "__main__":
    main()
