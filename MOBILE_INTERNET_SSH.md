# 📱 SSH Access via Mobile Internet - Setup Guide

## 🎯 The Challenge
Mobile networks use NAT and dynamic IPs, making direct SSH impossible. Here are proven solutions:

## 🏆 **Option 1: Tailscale VPN (Recommended - FREE)**

### Benefits:
- ✅ **FREE** for personal use (up to 20 devices)
- ✅ **Secure** - encrypted peer-to-peer connections
- ✅ **Simple** - works from anywhere
- ✅ **Reliable** - auto-reconnects
- ✅ **Cross-platform** - works on all devices

### Setup Steps:

#### 1. On Raspberry Pi (via keyboard/monitor initially):
```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale and authenticate
sudo tailscale up

# Get Pi's VPN IP address
tailscale ip -4
# Example output: 100.89.123.45
```

#### 2. On Your Development Machine:
```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Connect to same network
sudo tailscale up
```

#### 3. SSH to Pi from Anywhere:
```bash
# Use the Tailscale IP from step 1
ssh pi@100.89.123.45

# Deploy your system
./deploy_to_pi.sh 100.89.123.45
```

---

## 🔧 **Option 2: Mobile Router Port Forwarding**

If using a 4G/5G router (not phone hotspot):

### Setup Steps:

#### 1. Access Router Admin:
```bash
# Find router IP (usually one of these)
# 192.168.1.1, 192.168.0.1, or 10.0.0.1

# Open in browser
open http://192.168.1.1
```

#### 2. Configure Port Forwarding:
- **External Port**: 2222
- **Internal IP**: 192.168.1.100 (your Pi's local IP)
- **Internal Port**: 22
- **Protocol**: TCP

#### 3. Find Public IP:
```bash
# On Pi, check public IP
curl ifconfig.me
# Example: 41.185.34.122
```

#### 4. SSH from Outside:
```bash
ssh -p 2222 pi@41.185.34.122
```

---

## ⚡ **Option 3: Reverse SSH Tunnel**

If you have a VPS/cloud server:

### Setup Steps:

#### 1. On Raspberry Pi:
```bash
# Create reverse tunnel to your VPS
ssh -R 2222:localhost:22 user@your-vps.com -N -f

# Keep tunnel alive
autossh -R 2222:localhost:22 user@your-vps.com -N
```

#### 2. From Your Machine:
```bash
# SSH via the VPS
ssh user@your-vps.com
ssh -p 2222 pi@localhost
```

---

## 💰 **Option 4: ngrok (Simple but Paid)**

### Setup Steps:

#### 1. On Raspberry Pi:
```bash
# Download ngrok
wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-arm64.zip
unzip ngrok-stable-linux-arm64.zip
sudo mv ngrok /usr/local/bin/

# Get free account and auth token from ngrok.com
./ngrok authtoken YOUR_AUTH_TOKEN

# Create tunnel
./ngrok tcp 22
```

#### 2. Use Provided URL:
```bash
# ngrok will show something like:
# tcp://0.tcp.ngrok.io:12345

ssh -p 12345 pi@0.tcp.ngrok.io
```

---

## 🎯 **Recommended Workflow for Taxi System**

### 1. Initial Setup (with keyboard/monitor):
```bash
# Connect Pi to internet via mobile
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Note down the Tailscale IP
tailscale ip -4
```

### 2. Remote Development:
```bash
# SSH via Tailscale
ssh pi@100.x.x.x

# Deploy your system
./deploy_to_pi.sh 100.x.x.x

# Update remotely
./remote_update.sh 100.x.x.x update
```

### 3. Ongoing Management:
```bash
# Check system status
./remote_update.sh 100.x.x.x status

# View logs
./remote_update.sh 100.x.x.x logs

# Restart if needed
./remote_update.sh 100.x.x.x restart
```

---

## 🔒 **Security Best Practices**

### 1. Change Default SSH Settings:
```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Recommended changes:
Port 2222                    # Change default port
PermitRootLogin no          # Disable root login
PasswordAuthentication no   # Use keys only
PubkeyAuthentication yes    # Enable key auth

# Restart SSH
sudo systemctl restart sshd
```

### 2. Set Up SSH Key Authentication:
```bash
# Generate key pair on your machine
ssh-keygen -t rsa -b 4096

# Copy public key to Pi
ssh-copy-id pi@100.x.x.x
```

### 3. Firewall Configuration:
```bash
# On Pi, configure firewall
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 8000/tcp   # Your API
sudo ufw enable
```

---

## 🎉 **Success! You Can Now:**

- ✅ SSH to your Pi from anywhere with internet
- ✅ Deploy and update your taxi system remotely
- ✅ Monitor system health from your development machine
- ✅ Manage multiple vehicles across different locations
- ✅ Troubleshoot issues without physical access

**Next Steps:**
1. Set up Tailscale on both devices
2. Test SSH connection: `ssh pi@100.x.x.x`
3. Deploy your system: `./deploy_to_pi.sh 100.x.x.x`
4. Start managing your taxi fleet remotely! 🚖
