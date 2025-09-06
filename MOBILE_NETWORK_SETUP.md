# 📡 Mobile Network Setup Guide for HDJ864L

This guide explains how to set up your taxi passenger counting system with mobile networks and dynamic IPs.

## 🚨 **The Static IP Problem**

**Issue**: Mobile networks (4G/5G) assign dynamic public IPs that change frequently, breaking static IP camera connections.

**Current Config Problem**:
```yaml
camera:
  ip: "192.168.3.200"  # This won't work on mobile networks!
```

## ✅ **Solutions**

### **Solution 1: Use Local Network IPs (Recommended)**

#### **Step 1: Configure Your Mobile Router**
1. **Access router admin panel** (usually `192.168.1.1` or `192.168.0.1`)
2. **Set up DHCP reservation** for your camera:
   - Find camera's MAC address
   - Assign static local IP: `192.168.1.100`
3. **Configure port forwarding** (if needed):
   - External Port: 554 → Internal IP: 192.168.1.100, Port: 554

#### **Step 2: Update Camera Configuration**
```yaml
# Use config/HDJ864L_mobile.yaml instead of HDJ864L_live.yaml
camera:
  ip: "192.168.1.100"  # Router's local IP for camera
  stream_url: "rtsp://admin:Random336%23@192.168.1.100:554/stream1"
```

#### **Step 3: Network Topology**
```
Internet ←→ Mobile ISP ←→ 4G Router ←→ Local Network
                         (Dynamic IP)    (192.168.1.x)
                                              ↓
                                    ┌─────────────────┐
                                    │  Camera         │
                                    │  192.168.1.100  │
                                    └─────────────────┘
                                              ↓
                                    ┌─────────────────┐
                                    │  Raspberry Pi   │
                                    │  192.168.1.10   │
                                    └─────────────────┘
```

### **Solution 2: Dynamic DNS (Advanced)**

#### **Step 1: Set up Dynamic DNS**
```bash
# Install ddclient on router or Pi
sudo apt install ddclient -y

# Configure with your DNS provider (e.g., No-IP, DynDNS)
sudo nano /etc/ddclient.conf
```

#### **Step 2: Use Domain Name**
```yaml
camera:
  ip: "camera.yourdomain.com"  # Instead of IP address
  stream_url: "rtsp://admin:Random336%23@camera.yourdomain.com:554/stream1"
```

### **Solution 3: VPN Tunnel (Enterprise)**

#### **Step 1: Set up VPN Server**
```bash
# Install WireGuard on a cloud server
sudo apt install wireguard -y
```

#### **Step 2: Connect devices through VPN**
- Camera connects to VPN: `10.0.0.100`
- Pi connects to VPN: `10.0.0.10`
- Use VPN IPs in configuration

## 🔧 **Router Configuration Steps**

### **Popular Router Brands**

#### **Huawei 4G Routers**
1. Access: `http://192.168.8.1`
2. Login with admin credentials
3. Go to **Advanced** → **DHCP** → **Static Address Allocation**
4. Add camera MAC address with IP `192.168.8.100`

#### **TP-Link 4G Routers**
1. Access: `http://192.168.1.1`
2. Go to **Advanced** → **Network** → **DHCP Server**
3. Add **Address Reservation** for camera

#### **Netgear 4G Routers**
1. Access: `http://192.168.1.1`
2. Go to **LAN Setup** → **Address Reservation**
3. Add camera with static IP

### **Generic Steps for Any Router**
1. **Find camera's MAC address**:
   ```bash
   # From camera web interface or network scan
   nmap -sn 192.168.1.0/24
   ```

2. **Set DHCP reservation**:
   - MAC: `AA:BB:CC:DD:EE:FF`
   - IP: `192.168.1.100`
   - Name: `HDJ864L-Camera`

3. **Configure port forwarding** (if external access needed):
   - Service: RTSP
   - External Port: 554
   - Internal IP: 192.168.1.100
   - Internal Port: 554

## 🚀 **Deployment Commands**

### **Deploy to Raspberry Pi**
```bash
# 1. Deploy system to Pi
./deploy_to_pi.sh 192.168.1.10

# 2. Use mobile network config
scp config/HDJ864L_mobile.yaml pi@192.168.1.10:~/taxi-streaming/config/

# 3. Update docker-compose to use mobile config
ssh pi@192.168.1.10
cd taxi-streaming
# Edit docker-compose.simple.yml to use HDJ864L_mobile.yaml
```

### **Remote Management**
```bash
# Update system remotely
./remote_update.sh 192.168.1.10 update

# Check system status
./remote_update.sh 192.168.1.10 status

# View logs
./remote_update.sh 192.168.1.10 logs

# Restart system
./remote_update.sh 192.168.1.10 restart
```

## 📱 **Mobile Network Best Practices**

### **1. Data Usage Optimization**
- Use lower resolution for processing: `resize_factor: 0.5`
- Limit FPS: `max_fps: 10`
- Skip frames: `frame_skip: 2`
- Compress logs: `compress_logs: true`

### **2. Connection Stability**
- Increase timeouts: `timeout: 30`
- More retry attempts: `retry_attempts: 5`
- Health monitoring: Check every 30 seconds
- Auto-restart on failures

### **3. Offline Capability**
- Store data locally when offline
- Sync when connection returns
- Queue API calls for batch processing

### **4. Power Management**
- Monitor Pi temperature in vehicle
- Auto-shutdown on overheating
- UPS/battery backup for clean shutdowns

## 🔍 **Troubleshooting**

### **Camera Not Connecting**
```bash
# Test camera connection from Pi
ssh pi@192.168.1.10
ping 192.168.1.100

# Test RTSP stream
ffmpeg -i rtsp://admin:Random336%23@192.168.1.100:554/stream1 -t 10 -f null -
```

### **Dynamic IP Changes**
```bash
# Check current public IP
curl ifconfig.me

# Monitor IP changes
watch -n 60 'curl -s ifconfig.me'
```

### **Connection Issues**
```bash
# Check system status
./remote_update.sh 192.168.1.10 health

# View detailed logs
./remote_update.sh 192.168.1.10 logs

# Restart if needed
./remote_update.sh 192.168.1.10 restart
```

## 📊 **Monitoring Dashboard**

### **Key Metrics to Monitor**
- Camera connection status
- API response times
- Data usage
- System temperature
- Network connectivity
- Passenger count accuracy

### **Alerts to Set Up**
- Camera disconnection
- High data usage
- System overheating
- API failures
- Low disk space

## 🔐 **Security Considerations**

### **Network Security**
- Change default router passwords
- Use WPA3 encryption
- Disable WPS
- Enable firewall
- Regular firmware updates

### **Camera Security**
- Change default camera passwords
- Use strong RTSP credentials
- Limit camera access to local network
- Regular security updates

### **Pi Security**
- Change default SSH password
- Use SSH keys instead of passwords
- Enable firewall (ufw)
- Regular system updates
- Monitor for unauthorized access

## 📞 **Support Contacts**

- **Technical Issues**: Create GitHub issue
- **Network Setup**: Contact your mobile ISP
- **Camera Issues**: Check camera manufacturer support
- **Emergency**: Use remote restart commands
