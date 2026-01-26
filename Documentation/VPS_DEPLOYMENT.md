# 🚀 ARUN Trading Bot - VPS Deployment Guide

**Version**: 1.0
**Last Updated**: January 18, 2026
**For**: Phase 4 Infrastructure Sprint (Option B)

---

## 📋 Overview

This guide will help you deploy the ARUN Trading Bot to a cloud VPS (Virtual Private Server) for **24/7 automated trading**. Once deployed, the bot runs continuously in the background, and you can monitor it from anywhere using the mobile dashboard.

### Why VPS?
- ✅ **24/7 Operation**: Bot runs even when your computer is off
- ✅ **High Uptime**: Cloud providers offer 99.9% uptime SLAs
- ✅ **Remote Access**: Monitor from phone/tablet/laptop
- ✅ **Low Latency**: Faster order execution (VPS closer to broker servers)
- ✅ **Reliable**: Auto-restart on crashes, systemd service management

---

## 🎯 Prerequisites

Before starting, ensure you have:
- [x] ARUN Bot working locally (tested in paper trading mode)
- [x] Valid mStock broker credentials (API key, TOTP secret)
- [x] SSH client (Terminal on Mac/Linux, PuTTY on Windows)
- [x] VPS account (AWS, DigitalOcean, Linode, etc.)
- [x] Basic Linux command-line knowledge

---

## 🌍 Step 1: Choose a VPS Provider

### Recommended Providers

| Provider | Specs | Price | Location | Link |
|----------|-------|-------|----------|------|
| **DigitalOcean** | 1GB RAM, 1 CPU, 25GB SSD | $6/month | Bangalore, India | [digitalocean.com](https://www.digitalocean.com) |
| **AWS EC2** | t2.micro (1GB RAM) | ~$10/month | Mumbai, India | [aws.amazon.com](https://aws.amazon.com) |
| **Linode** | Nanode 1GB | $5/month | Mumbai, India | [linode.com](https://www.linode.com) |
| **Vultr** | 1GB RAM, 1 CPU | $6/month | Mumbai, India | [vultr.com](https://www.vultr.com) |

**Recommendation**: **DigitalOcean Bangalore** (closest to NSE/BSE, low latency)

### Minimum Specifications
- **RAM**: 1GB (2GB recommended for smoother operation)
- **CPU**: 1 core
- **Storage**: 10GB SSD
- **OS**: Ubuntu 22.04 LTS (or 20.04 LTS)
- **Network**: 1Gbps

---

## 🖥️ Step 2: Create Your VPS Instance

### Option A: DigitalOcean (Recommended)

1. **Sign Up**: Go to [digitalocean.com](https://www.digitalocean.com) and create an account
2. **Create Droplet**:
   - Click "Create" → "Droplets"
   - **Choose Image**: Ubuntu 22.04 LTS
   - **Choose Plan**: Basic ($6/month - 1GB RAM, 25GB SSD)
   - **Choose Region**: Bangalore, India
   - **Authentication**: SSH Key (recommended) or Password
   - **Hostname**: `arun-trading-bot`
   - Click "Create Droplet"

3. **Note Your IP Address**: Example: `143.110.245.123`

### Option B: AWS EC2

1. **Sign Up**: Go to [aws.amazon.com](https://aws.amazon.com) and create an account
2. **Launch Instance**:
   - Go to EC2 Dashboard → Launch Instance
   - **Name**: `arun-trading-bot`
   - **AMI**: Ubuntu Server 22.04 LTS
   - **Instance Type**: t2.micro (1GB RAM)
   - **Key Pair**: Create new or use existing SSH key
   - **Network**: Allow SSH (port 22), HTTP (port 8501)
   - **Storage**: 10GB gp3
   - Click "Launch Instance"

3. **Elastic IP**: Assign a static IP to your instance (optional but recommended)

---

## 🔐 Step 3: Connect to Your VPS

### From Linux/Mac:
```bash
# Replace YOUR_VPS_IP with your actual VPS IP
ssh root@YOUR_VPS_IP

# If using SSH key:
ssh -i /path/to/your-key.pem ubuntu@YOUR_VPS_IP
```

### From Windows (PuTTY):
1. Download PuTTY from [putty.org](https://www.putty.org/)
2. Enter your VPS IP in "Host Name"
3. Port: `22`
4. Connection Type: `SSH`
5. Click "Open"

### First Login:
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Create a non-root user (recommended for security)
sudo adduser arun
sudo usermod -aG sudo arun

# Switch to new user
su - arun
```

---

## 📦 Step 4: Install Dependencies

### Install Python 3 and Essential Tools
```bash
# Install Python 3.10+ and pip
sudo apt install -y python3 python3-pip python3-venv git

# Install build tools
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev

# Verify installation
python3 --version  # Should be 3.10 or higher
pip3 --version
```

### Install Additional System Packages
```bash
# For TA-Lib (if you use it for RSI calculations)
sudo apt install -y ta-lib

# For SQLite (usually pre-installed)
sudo apt install -y sqlite3
```

---

## 📥 Step 5: Clone the Repository

### Option A: Clone from GitHub (Recommended)
```bash
# Navigate to home directory
cd ~

# Clone the repository
git clone https://github.com/BratAIExplorer/TradingBot_Arun-Jay_Pilot.git

# Navigate to project directory
cd TradingBot_Arun-Jay_Pilot

# Switch to the correct branch (if not main)
git checkout claude/sync-github-remote-3461O
```

### Option B: Upload from Local Machine (via SCP)
```bash
# On your local machine:
scp -r /path/to/TradingBot_Arun-Jay_Pilot root@YOUR_VPS_IP:/home/arun/

# Then on VPS:
cd ~/TradingBot_Arun-Jay_Pilot
```

---

## 🐍 Step 6: Setup Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Verify installation
python -c "import customtkinter, pandas, requests; print('✅ Dependencies installed')"
```

---

## ⚙️ Step 7: Configure Settings

### Upload Your settings.json
You need to transfer your local `settings.json` (with broker credentials) to the VPS.

**Method 1: SCP Upload (Recommended)**
```bash
# On your local machine:
scp /path/to/TradingBot_Arun-Jay_Pilot/settings.json root@YOUR_VPS_IP:/home/arun/TradingBot_Arun-Jay_Pilot/
```

**Method 2: Manual Edit on VPS**
```bash
# On VPS:
nano ~/TradingBot_Arun-Jay_Pilot/settings.json

# Paste your settings.json content
# Save: Ctrl+O, Enter
# Exit: Ctrl+X
```

### Critical Settings for VPS:
```json
{
  "app_settings": {
    "paper_trading_mode": false,  // Set to false for LIVE trading
    "nifty_50_only": false
  },
  "broker": {
    "api_key": "YOUR_API_KEY",
    "totp_secret": "YOUR_TOTP_SECRET",
    "client_code": "YOUR_CLIENT_CODE",
    "password": "YOUR_PASSWORD"
  },
  "mobile": {
    "password": "arun2026"  // Change this for security!
  }
}
```

**⚠️ Security Warning**:
- ✅ **DO NOT** commit `settings.json` to GitHub (contains sensitive credentials)
- ✅ Use strong password for mobile dashboard
- ✅ Restrict firewall rules (only allow your IP for port 8501)

---

## 🧪 Step 8: Test the Bot in Paper Mode

Before going live, test the bot on VPS in paper trading mode:

```bash
# Activate virtual environment (if not already)
source .venv/bin/activate

# Edit settings to enable paper mode
nano settings.json
# Set "paper_trading_mode": true

# Test bot_daemon.py
python bot_daemon.py status     # Should show "NOT running"
python bot_daemon.py start      # Start daemon
tail -f daemon.log              # View live logs (Ctrl+C to exit)
python bot_daemon.py status     # Should show "RUNNING"
python bot_daemon.py stop       # Stop daemon
```

### Verify Logs:
```bash
tail -50 daemon.log

# Look for:
# ✅ "Trading engine started"
# ✅ "Paper Trading Mode: True"
# ✅ No errors or crashes
```

---

## 🔧 Step 9: Create Systemd Service (Auto-Restart)

To ensure the bot automatically starts on VPS reboot and restarts on crashes, create a systemd service:

### Create Service File:
```bash
sudo nano /etc/systemd/system/arun-bot.service
```

### Paste This Configuration:
```ini
[Unit]
Description=ARUN Trading Bot Daemon
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=arun
WorkingDirectory=/home/arun/TradingBot_Arun-Jay_Pilot
ExecStart=/home/arun/TradingBot_Arun-Jay_Pilot/.venv/bin/python /home/arun/TradingBot_Arun-Jay_Pilot/bot_daemon.py run
Restart=on-failure
RestartSec=10
StandardOutput=append:/home/arun/TradingBot_Arun-Jay_Pilot/daemon.log
StandardError=append:/home/arun/TradingBot_Arun-Jay_Pilot/daemon.log

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service:
```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable arun-bot

# Start the service
sudo systemctl start arun-bot

# Check status
sudo systemctl status arun-bot

# View logs
journalctl -u arun-bot -f
```

### Service Management Commands:
```bash
# Start bot
sudo systemctl start arun-bot

# Stop bot
sudo systemctl stop arun-bot

# Restart bot
sudo systemctl restart arun-bot

# Check status
sudo systemctl status arun-bot

# View logs (live)
journalctl -u arun-bot -f

# View last 100 lines
journalctl -u arun-bot -n 100
```

---

## 📱 Step 10: Setup Mobile Dashboard

### Start Streamlit Dashboard:

**Option A: Manual Start (Testing)**
```bash
# Activate virtual environment
source .venv/bin/activate

# Start dashboard
streamlit run mobile_dashboard.py --server.port 8501 --server.address 0.0.0.0

# Access from browser:
# http://YOUR_VPS_IP:8501
```

**Option B: Background Process (tmux/screen)**
```bash
# Install tmux
sudo apt install -y tmux

# Start tmux session
tmux new -s dashboard

# Activate venv and run dashboard
source .venv/bin/activate
streamlit run mobile_dashboard.py --server.port 8501 --server.address 0.0.0.0

# Detach from tmux: Ctrl+B, then D
# Reattach later: tmux attach -t dashboard
```

**Option C: Systemd Service (Recommended)**
```bash
sudo nano /etc/systemd/system/arun-dashboard.service
```

Paste:
```ini
[Unit]
Description=ARUN Bot Mobile Dashboard
After=network.target

[Service]
Type=simple
User=arun
WorkingDirectory=/home/arun/TradingBot_Arun-Jay_Pilot
ExecStart=/home/arun/TradingBot_Arun-Jay_Pilot/.venv/bin/streamlit run mobile_dashboard.py --server.port 8501 --server.address 0.0.0.0
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable arun-dashboard
sudo systemctl start arun-dashboard
sudo systemctl status arun-dashboard
```

---

## 🔒 Step 11: Configure Firewall & Security

### Setup UFW Firewall:
```bash
# Install UFW
sudo apt install -y ufw

# Allow SSH (IMPORTANT: Don't lock yourself out!)
sudo ufw allow 22/tcp

# Allow Streamlit dashboard (restrict to your IP for security)
sudo ufw allow from YOUR_HOME_IP to any port 8501

# OR allow from anywhere (less secure):
sudo ufw allow 8501/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Change Default Passwords:
```bash
# Edit settings.json
nano settings.json

# Change mobile.password to a strong password
# Example: "mobile": { "password": "MyStr0ng!Pass2026" }
```

### Secure SSH (Optional but Recommended):
```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Disable root login:
PermitRootLogin no

# Use only key-based authentication:
PasswordAuthentication no

# Restart SSH service
sudo systemctl restart sshd
```

---

## 🚀 Step 12: Go Live!

Once you've tested everything in paper mode:

### 1. Update Settings for Live Trading:
```bash
nano settings.json

# Set:
"paper_trading_mode": false
```

### 2. Restart Bot:
```bash
sudo systemctl restart arun-bot

# Verify it's running
sudo systemctl status arun-bot
```

### 3. Monitor via Dashboard:
```
Open browser: http://YOUR_VPS_IP:8501
Login with password
Check Dashboard → Should show "LIVE TRADING"
```

### 4. Monitor Logs:
```bash
# Watch live logs
tail -f daemon.log

# Or via systemd
journalctl -u arun-bot -f
```

---

## 📊 Step 13: Monitoring & Maintenance

### Daily Checks:
```bash
# Check bot status
sudo systemctl status arun-bot

# Check recent logs
tail -50 daemon.log

# Check trades
sqlite3 database/trades.db "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;"
```

### Weekly Maintenance:
```bash
# Update bot code (if new updates available)
cd ~/TradingBot_Arun-Jay_Pilot
git pull origin main

# Restart services
sudo systemctl restart arun-bot
sudo systemctl restart arun-dashboard
```

### Log Rotation:
Logs automatically rotate at 10MB (configured in `bot_daemon.py`). Old logs are saved to `daemon.log.old`.

---

## 🆘 Troubleshooting

### Bot Not Starting:
```bash
# Check systemd logs
journalctl -u arun-bot -n 50

# Check daemon.log for errors
tail -100 daemon.log

# Verify settings.json is valid
python -c "import json; json.load(open('settings.json'))"

# Test manually
source .venv/bin/activate
python bot_daemon.py run
```

### Dashboard Not Accessible:
```bash
# Check if Streamlit is running
sudo systemctl status arun-dashboard

# Check firewall rules
sudo ufw status

# Test locally on VPS
curl http://localhost:8501
```

### Orders Not Executing:
```bash
# Check broker credentials
# Verify TOTP secret is correct
# Check daemon.log for API errors
grep -i "error\|fail\|403" daemon.log

# Test mStock API manually
python -c "import kickstart; kickstart.perform_auto_login()"
```

### High CPU/RAM Usage:
```bash
# Check resource usage
htop  # Install: sudo apt install htop

# Reduce update frequency in dashboard
# Edit mobile_dashboard.py, increase cache TTL
```

---

## 🔄 Updating the Bot

### Pull Latest Changes:
```bash
cd ~/TradingBot_Arun-Jay_Pilot
git pull origin main  # Or your branch name

# Reinstall dependencies (if requirements.txt changed)
source .venv/bin/activate
pip install -r requirements.txt

# Restart services
sudo systemctl restart arun-bot
sudo systemctl restart arun-dashboard
```

---

## 💰 Cost Estimate

| Item | Monthly Cost |
|------|--------------|
| VPS (1GB RAM, 25GB SSD) | $5-10 |
| Static IP (optional) | $3 |
| **Total** | **~$8-13/month** |

**Note**: This is significantly cheaper than maintaining a dedicated desktop 24/7 (electricity + hardware costs).

---

## 📚 Additional Resources

- [DigitalOcean Tutorials](https://www.digitalocean.com/community/tutorials)
- [Ubuntu Server Guide](https://ubuntu.com/server/docs)
- [Systemd Service Guide](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Streamlit Deployment](https://docs.streamlit.io/deploy)

---

## ✅ Deployment Checklist

Before going live, ensure:
- [ ] VPS created with Ubuntu 22.04
- [ ] Python 3.10+ installed
- [ ] Repository cloned and dependencies installed
- [ ] settings.json uploaded with valid credentials
- [ ] Paper trading mode tested successfully
- [ ] Systemd service created and enabled
- [ ] Firewall configured and enabled
- [ ] Dashboard accessible from browser
- [ ] Logs show no errors
- [ ] Mobile dashboard password changed
- [ ] Backup of settings.json saved locally

---

**Version**: 1.0
**Last Updated**: January 18, 2026
**Status**: Phase 4 Infrastructure Sprint Complete

For support, see `Documentation/Technical/AI_HANDOVER.md`
