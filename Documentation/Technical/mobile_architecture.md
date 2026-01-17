# 📱 Mobile Companion App - Architecture Plan

## The Problem
ARUN Titan V2 is a **desktop GUI application** built with `customtkinter` (Python). It runs locally on Windows and **cannot** be accessed from a phone browser directly.

## The Solution: Headless + Web Dashboard

### Architecture Overview
```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────┐
│   Desktop GUI   │         │  Headless Bot    │  HTTP   │   Mobile    │
│  (Windows PC)   │    OR   │  (VPS/Cloud)     │ ◄─────► │   Browser   │
│  CustomTkinter  │         │  + Streamlit     │         │  (Phone)    │
└─────────────────┘         └──────────────────┘         └─────────────┘
```

### Two Deployment Modes

#### Mode 1: Local Desktop Only (Current)
- Bot runs on your PC with full GUI
- **Cannot** access from phone
- Best for manual monitoring at desk

#### Mode 2: VPS + Streamlit (Phase 4 - Deferred)
- Bot runs **headless** on a VPS (e.g., AWS, DigitalOcean)
- Streamlit web dashboard runs alongside
- Access dashboard via phone browser: `https://your-vps-ip:8501`
- **Trade logic** runs 24/7 on VPS
- **Monitoring only** from phone

## Technical Implementation (When Ready)

### Step 1: Separate Core Logic from GUI
```python
# kickstart.py already handles this:
run_cycle()          # Trading logic (GUI-independent)
fetch_market_data()  # API calls (GUI-independent)
```

### Step 2: Create Streamlit Dashboard
```python
# streamlit_app.py (NEW FILE - not built yet)
import streamlit as st
from database.trades_db import TradesDatabase

st.title("ARUN Mobile Companion")
db = TradesDatabase()
positions = db.get_open_positions()
st.dataframe(positions)  # Shows positions in browser
```

### Step 3: Run Both in Parallel
```bash
# On VPS:
python kickstart.py &          # Bot runs headless
streamlit run streamlit_app.py # Web dashboard on port 8501
```

### Step 4: Secure with Password
```python
# Add basic auth to Streamlit
if st.text_input("Password") != "your_secure_pass":
    st.stop()
```

## Why Streamlit?
- ✅ Python-based (matches our stack)
- ✅ Auto-refreshes data
- ✅ Mobile-responsive by default
- ✅ Can reuse `kickstart.py` logic
- ✅ Easy to deploy on cloud

## Limitations
- **Read-only**: Mobile view is for monitoring only
- Settings changes still require desktop GUI
- No real-time push notifications (refresh manually)

## Next Steps (Phase 4)
1. Extract `kickstart.py` to run headless (skip GUI)
2. Build `streamlit_app.py` with core metrics
3. Deploy to VPS with reverse proxy (nginx)
4. Add authentication layer

**Status**: Deferred until core trading features are stable.
