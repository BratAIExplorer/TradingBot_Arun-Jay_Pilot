# 🚀 Option B Implementation Plan: Headless Core + Mobile Dashboard

**Sprint**: Phase 4 Infrastructure
**Start Date**: January 18, 2026
**Goal**: Enable 24/7 VPS deployment and mobile monitoring
**Status**: IN PROGRESS

---

## 📋 Overview

### What We're Building
**Option B**: Headless Core + Mobile Dashboard for VPS deployment and remote monitoring

**Why This First?**
- ✅ Enables 24/7 trading on VPS (no desktop needed)
- ✅ Mobile monitoring from anywhere
- ✅ Leverages existing kickstart.py (already headless-capable)
- ✅ No conflicts with Google AI's GUI work
- ✅ Fast to implement (1-3 days vs 4-8 weeks for Confluence Engine)

---

## 🎯 Components to Build

### 1. Headless Daemon (`bot_daemon.py`)
**Purpose**: Run trading engine without GUI for VPS deployment

**Features**:
- ✅ Runs `kickstart.py` in background
- ✅ Logs to file (for remote monitoring)
- ✅ Graceful start/stop controls
- ✅ Auto-restart on crash (optional)
- ✅ Signal handling (SIGTERM, SIGINT)
- ✅ PID file for process management

**File Location**: `/bot_daemon.py` (root level)

**Key Functions**:
```python
def start_daemon():
    """Start trading engine in background"""
    # Load settings
    # Initialize kickstart modules
    # Run main_loop() from kickstart
    # Log to daemon.log

def stop_daemon():
    """Gracefully stop trading engine"""
    # Set STOP_REQUESTED flag
    # Wait for cycle completion
    # Save state
    # Exit cleanly

def status_daemon():
    """Check if daemon is running"""
    # Read PID file
    # Check process exists
    # Return status
```

---

### 2. Mobile Dashboard (`mobile_dashboard.py`)
**Purpose**: Streamlit web UI for remote monitoring

**Pages/Tabs**:

#### 🏠 Dashboard (Home)
- **System Status**: Online/Offline, Last Update, Bot Running Time
- **Today's Performance**: Total P&L, Win Rate, Trades Count
- **Portfolio Summary**: Active Positions Count, Total Capital Used
- **Market Sentiment**: Current sentiment (Fear/Neutral/Greed)

#### 📊 Positions (Active)
**Table Columns**:
- Symbol | Exchange | Quantity | Entry Price | Current Price | P&L (₹) | P&L (%)
- **Actions**: View Details (read-only)

#### 📜 Trades History
**Table Columns**:
- Timestamp | Symbol | Action (BUY/SELL) | Quantity | Price | Source (BOT/MANUAL)
- **Filters**: Date range, Symbol, Action type
- **Export**: CSV download

#### ⚙️ System Logs (Read-Only)
- **Live Logs**: Last 100 lines from `daemon.log`
- **Auto-refresh**: Every 5 seconds
- **Search**: Filter by keyword

#### 🔐 Settings (Read-Only View)
- Display current settings from `settings.json`
- **No editing** (must use desktop app for changes)
- Shows: Capital, Risk, Broker, Strategies

**File Location**: `/mobile_dashboard.py` (root level)

**Authentication**:
```python
# Simple password protection
# Password stored in settings.json: mobile.password
# Session-based login (streamlit session_state)
```

---

### 3. VPS Deployment Guide (`Documentation/VPS_DEPLOYMENT.md`)
**Purpose**: Step-by-step guide for deploying to cloud

**Sections**:

#### Prerequisites
- VPS provider (AWS EC2, DigitalOcean, Linode)
- Python 3.8+ installed
- SSH access

#### Setup Steps
1. **Create VPS Instance**
   - Ubuntu 22.04 LTS recommended
   - Minimum: 1GB RAM, 1 CPU, 10GB storage

2. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv git
   ```

3. **Clone Repository**
   ```bash
   git clone https://github.com/BratAIExplorer/TradingBot_Arun-Jay_Pilot.git
   cd TradingBot_Arun-Jay_Pilot
   ```

4. **Setup Virtual Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Configure Settings**
   - Upload `settings.json` (with broker credentials)
   - Set `app_settings.paper_trading_mode: false` for live trading

6. **Create Systemd Service**
   ```ini
   [Unit]
   Description=ARUN Trading Bot Daemon
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/TradingBot_Arun-Jay_Pilot
   ExecStart=/home/ubuntu/TradingBot_Arun-Jay_Pilot/.venv/bin/python bot_daemon.py start
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

7. **Start Services**
   ```bash
   # Start bot daemon
   sudo systemctl enable arun-bot
   sudo systemctl start arun-bot

   # Start mobile dashboard (port 8501)
   streamlit run mobile_dashboard.py --server.port 8501 &
   ```

8. **Security**
   - Setup firewall (allow only SSH + 8501)
   - Use reverse proxy (nginx) for HTTPS
   - Store credentials securely (no git commits)

#### Maintenance
- View logs: `journalctl -u arun-bot -f`
- Restart bot: `sudo systemctl restart arun-bot`
- Update code: `git pull && sudo systemctl restart arun-bot`

---

## 🛠️ Technical Implementation Details

### Architecture Flow

```
┌─────────────────────────────────────────────────────────┐
│                    VPS (Cloud Server)                   │
│                                                         │
│  ┌────────────────────────────────────────────────┐   │
│  │  bot_daemon.py (Background Process)             │   │
│  │  - Runs kickstart.main_loop()                   │   │
│  │  - Logs to daemon.log                           │   │
│  │  - Writes to trades.db                          │   │
│  └────────────┬────────────────────────────────────┘   │
│               │                                         │
│               ▼                                         │
│  ┌────────────────────────────────────────────────┐   │
│  │  SQLite Database (trades.db)                    │   │
│  │  - Trades history                               │   │
│  │  - Positions                                    │   │
│  └────────────┬────────────────────────────────────┘   │
│               │                                         │
│               ▼                                         │
│  ┌────────────────────────────────────────────────┐   │
│  │  mobile_dashboard.py (Streamlit Web Server)     │   │
│  │  - Port 8501                                    │   │
│  │  - Reads from trades.db (read-only)             │   │
│  │  - Displays live data                           │   │
│  └────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │ HTTPS (8501)
                         │
                    ┌────┴────┐
                    │  User   │
                    │ (Phone/ │
                    │ Tablet) │
                    └─────────┘
```

### Data Flow

1. **Bot Daemon** → Places orders → Updates `trades.db`
2. **Mobile Dashboard** → Queries `trades.db` → Displays to user
3. **User** → Views dashboard → No write access (safe)

---

## 📦 File Structure (After Implementation)

```
TradingBot_Arun-Jay_Pilot/
├── bot_daemon.py              # NEW: Headless runner
├── mobile_dashboard.py        # NEW: Streamlit mobile UI
├── daemon.log                 # NEW: Daemon logs
├── bot_daemon.pid             # NEW: Process ID file
├── kickstart.py               # EXISTING: Core trading engine
├── dashboard_v2.py            # EXISTING: Desktop GUI
├── settings.json              # EXISTING: Configuration
├── database/
│   └── trades_db.py           # EXISTING: SQLite interface
├── Documentation/
│   ├── VPS_DEPLOYMENT.md      # NEW: Deployment guide
│   ├── Technical/
│   │   └── AI_HANDOVER.md     # UPDATED: Mention new files
│   └── Product/
│       └── BACKLOG.md         # UPDATED: Mark items in-progress
└── requirements.txt           # UPDATED: Add streamlit
```

---

## 🧪 Testing Plan

### 1. Headless Daemon Testing
**Test Cases**:
- [ ] Start daemon → Check PID file created
- [ ] Daemon runs trading cycle → Verify logs updated
- [ ] Stop daemon → Check graceful shutdown
- [ ] Restart daemon → Check state persists
- [ ] Crash simulation → Check auto-restart (if enabled)
- [ ] Paper trading mode → Verify no real orders

**Commands**:
```bash
# Start
python bot_daemon.py start

# Check status
python bot_daemon.py status

# View logs
tail -f daemon.log

# Stop
python bot_daemon.py stop
```

### 2. Mobile Dashboard Testing
**Test Cases**:
- [ ] Login page → Verify password protection
- [ ] Dashboard view → Check P&L calculation
- [ ] Positions table → Verify live data
- [ ] Trades history → Check filters work
- [ ] Export CSV → Verify download
- [ ] Logs view → Check auto-refresh
- [ ] Mobile responsive → Test on phone/tablet

**Commands**:
```bash
streamlit run mobile_dashboard.py
# Open http://localhost:8501
```

### 3. Integration Testing
**Test Cases**:
- [ ] Daemon running + Dashboard → Data syncs correctly
- [ ] Place trade via daemon → Shows in dashboard instantly
- [ ] Multiple users accessing dashboard → No conflicts
- [ ] Dashboard read-only → Cannot modify trades

---

## 🚨 Critical Requirements (Must-Haves)

### Security
- ✅ Password-protected dashboard (no public access)
- ✅ Read-only operations (no trade modification via mobile)
- ✅ Secure credential storage (settings.json not in git)
- ✅ HTTPS recommended for production (nginx reverse proxy)

### Reliability
- ✅ Daemon survives VPS restart (systemd service)
- ✅ Graceful shutdown (no orphaned orders)
- ✅ State persistence (resume after crash)
- ✅ Error logging (debug issues remotely)

### User Experience
- ✅ Fast load times (< 2 seconds)
- ✅ Mobile-responsive design
- ✅ Auto-refresh data (no manual reload)
- ✅ Clear error messages

---

## 📅 Implementation Timeline

### Day 1: Headless Core
- ✅ Build `bot_daemon.py` (4-6 hours)
- ✅ Add logging and PID management (2 hours)
- ✅ Test start/stop/restart (1 hour)
- ✅ Commit & push to git

### Day 2: Mobile Dashboard
- ✅ Build Streamlit login page (1 hour)
- ✅ Build dashboard view (2 hours)
- ✅ Build positions/trades tables (2 hours)
- ✅ Build logs viewer (1 hour)
- ✅ Add styling/responsiveness (1 hour)
- ✅ Test on mobile device (1 hour)
- ✅ Commit & push to git

### Day 3: Deployment Guide
- ✅ Write VPS_DEPLOYMENT.md (2-3 hours)
- ✅ Test deployment on DigitalOcean (2 hours)
- ✅ Add systemd service config (1 hour)
- ✅ Update AI_HANDOVER.md (1 hour)
- ✅ Final commit & push to git

---

## ✅ Definition of Done

This sprint is **COMPLETE** when:
- [ ] `bot_daemon.py` runs trading engine headlessly
- [ ] `mobile_dashboard.py` displays live data from VPS
- [ ] `VPS_DEPLOYMENT.md` guide successfully tested on cloud VPS
- [ ] All code committed to git with proper documentation
- [ ] AI_HANDOVER.md updated with new architecture
- [ ] BACKLOG.md marked items as complete
- [ ] Tested in paper trading mode (no real trades)
- [ ] User can monitor bot from phone/tablet

---

## 🔮 Future Enhancements (Post-Sprint)

**Phase 4.1** (After Option B is live):
- [ ] Mobile push notifications (trade alerts)
- [ ] Advanced charts (RSI/Price graphs)
- [ ] Multi-bot management (run multiple strategies)
- [ ] Telegram bot integration
- [ ] Desktop app remote control (start/stop from mobile)

**Phase 5** (Confluence Engine):
- [ ] Stock scoring integration (0-100 confluence score)
- [ ] Recommendation engine
- [ ] Watchlist management

---

## 📞 Dependencies & Requirements

### Python Packages (Add to requirements.txt)
```
streamlit>=1.30.0
watchdog>=3.0.0  # For file monitoring
psutil>=5.9.0    # For process management
```

### External Services
- None (fully self-contained, uses existing database)

### Compatibility
- ✅ Works alongside existing desktop app (no conflicts)
- ✅ Uses same `settings.json` and `trades.db`
- ✅ No changes to core trading logic (kickstart.py)

---

**Document Version**: 1.0
**Last Updated**: January 18, 2026
**Status**: Implementation in progress
