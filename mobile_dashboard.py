#!/usr/bin/env python3
"""
ARUN Trading Bot - Mobile Dashboard
====================================
Streamlit-based web UI for remote monitoring.

Features:
    - Real-time P&L and performance metrics
    - Active positions table
    - Trades history with filters
    - System logs viewer
    - Password-protected access
    - Read-only (no trade modifications)
    - Mobile-responsive design

Usage:
    streamlit run mobile_dashboard.py --server.port 8501

Access:
    http://your-vps-ip:8501
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import time

# Page config (must be first Streamlit command)
st.set_page_config(
    page_title="ARUN Bot Monitor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paths
PROJECT_ROOT = Path(__file__).parent
SETTINGS_FILE = PROJECT_ROOT / "settings.json"
DATABASE_FILE = PROJECT_ROOT / "database" / "trades.db"
DAEMON_LOG_FILE = PROJECT_ROOT / "daemon.log"
DAEMON_PID_FILE = PROJECT_ROOT / "bot_daemon.pid"

# Theme colors (Titan dark theme)
COLOR_BG = "#050505"
COLOR_CARD = "#121212"
COLOR_ACCENT = "#00F0FF"
COLOR_DANGER = "#FF003C"
COLOR_SUCCESS = "#00E676"
COLOR_TEXT = "#E0E0E0"

# Custom CSS for dark theme
CUSTOM_CSS = f"""
<style>
    .stApp {{
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
    }}
    .metric-card {{
        background-color: {COLOR_CARD};
        padding: 20px;
        border-radius: 10px;
        border: 1px solid {COLOR_ACCENT};
        margin: 10px 0;
    }}
    .success-text {{
        color: {COLOR_SUCCESS};
        font-weight: bold;
    }}
    .danger-text {{
        color: {COLOR_DANGER};
        font-weight: bold;
    }}
    .accent-text {{
        color: {COLOR_ACCENT};
        font-weight: bold;
    }}
    h1, h2, h3 {{
        color: {COLOR_ACCENT};
    }}
</style>
"""


# ====================== Authentication ======================

def check_password():
    """Password protection for dashboard"""

    def password_entered():
        """Verify entered password"""
        # Load password from settings.json
        password = get_dashboard_password()

        if st.session_state["password"] == password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    # First run, show login
    if "password_correct" not in st.session_state:
        st.markdown("# 🔐 ARUN Bot Monitor - Login")
        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password"
        )
        st.info("💡 Default password: 'arun2026' (change in settings.json → mobile.password)")
        return False

    # Password incorrect
    elif not st.session_state["password_correct"]:
        st.markdown("# 🔐 ARUN Bot Monitor - Login")
        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password"
        )
        st.error("❌ Incorrect password. Please try again.")
        return False

    # Password correct
    return True


def get_dashboard_password():
    """Get dashboard password from settings.json"""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
            return settings.get("mobile", {}).get("password", "arun2026")
    except Exception:
        pass
    return "arun2026"  # Default password


# ====================== Data Loading ======================

@st.cache_data(ttl=5)  # Cache for 5 seconds
def load_settings():
    """Load bot settings"""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading settings: {e}")
    return {}


@st.cache_data(ttl=2)  # Cache for 2 seconds
def load_trades_from_db():
    """Load trades from database"""
    try:
        if DATABASE_FILE.exists():
            import sqlite3
            conn = sqlite3.connect(str(DATABASE_FILE))
            query = "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 1000"
            df = pd.read_sql_query(query, conn)
            conn.close()

            if not df.empty:
                # Parse timestamp
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df
    except Exception as e:
        st.error(f"Error loading trades: {e}")

    return pd.DataFrame()


@st.cache_data(ttl=2)
def get_active_positions():
    """Get active positions from database"""
    df_trades = load_trades_from_db()

    if df_trades.empty:
        return pd.DataFrame()

    # Calculate positions (simple logic: BUY adds, SELL subtracts)
    positions = {}

    for _, trade in df_trades.iterrows():
        symbol = trade['symbol']
        action = trade['action']
        qty = trade['quantity']
        price = trade['price']

        if symbol not in positions:
            positions[symbol] = {
                'symbol': symbol,
                'quantity': 0,
                'total_cost': 0,
                'trades': []
            }

        if action == 'BUY':
            positions[symbol]['quantity'] += qty
            positions[symbol]['total_cost'] += qty * price
        elif action == 'SELL':
            positions[symbol]['quantity'] -= qty
            positions[symbol]['total_cost'] -= qty * price

        positions[symbol]['trades'].append({
            'action': action,
            'qty': qty,
            'price': price,
            'timestamp': trade['timestamp']
        })

    # Filter only active positions (quantity > 0)
    active_positions = [
        {
            'Symbol': p['symbol'],
            'Quantity': p['quantity'],
            'Avg Entry Price': p['total_cost'] / p['quantity'] if p['quantity'] > 0 else 0,
            'Total Cost': p['total_cost']
        }
        for p in positions.values()
        if p['quantity'] > 0
    ]

    return pd.DataFrame(active_positions)


@st.cache_data(ttl=10)
def get_performance_summary():
    """Calculate performance summary"""
    df_trades = load_trades_from_db()

    if df_trades.empty:
        return {
            'total_trades': 0,
            'today_trades': 0,
            'total_pnl': 0,
            'today_pnl': 0,
            'win_rate': 0,
            'total_buy_value': 0,
            'total_sell_value': 0
        }

    today = datetime.now().date()
    df_today = df_trades[df_trades['timestamp'].dt.date == today]

    # Calculate P&L (simplified: sell_value - buy_value)
    buy_value = df_trades[df_trades['action'] == 'BUY']['price'].sum() * df_trades[df_trades['action'] == 'BUY']['quantity'].sum()
    sell_value = df_trades[df_trades['action'] == 'SELL']['price'].sum() * df_trades[df_trades['action'] == 'SELL']['quantity'].sum()
    total_pnl = sell_value - buy_value

    buy_value_today = df_today[df_today['action'] == 'BUY']['price'].sum() * df_today[df_today['action'] == 'BUY']['quantity'].sum()
    sell_value_today = df_today[df_today['action'] == 'SELL']['price'].sum() * df_today[df_today['action'] == 'SELL']['quantity'].sum()
    today_pnl = sell_value_today - buy_value_today

    return {
        'total_trades': len(df_trades),
        'today_trades': len(df_today),
        'total_pnl': total_pnl,
        'today_pnl': today_pnl,
        'win_rate': 0,  # TODO: Calculate proper win rate
        'total_buy_value': buy_value,
        'total_sell_value': sell_value
    }


def is_daemon_running():
    """Check if bot daemon is running"""
    try:
        if DAEMON_PID_FILE.exists():
            with open(DAEMON_PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Check if process exists
            os.kill(pid, 0)
            return True, pid
    except (OSError, ValueError):
        pass
    return False, None


def read_daemon_logs(num_lines=50):
    """Read last N lines from daemon.log"""
    try:
        if DAEMON_LOG_FILE.exists():
            with open(DAEMON_LOG_FILE, 'r') as f:
                lines = f.readlines()
            return lines[-num_lines:]
    except Exception as e:
        return [f"Error reading logs: {e}"]
    return []


# ====================== UI Components ======================

def render_header():
    """Render header with bot status"""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("# 🤖 ARUN Bot Monitor")
        st.markdown("*Remote monitoring dashboard*")

    with col2:
        running, pid = is_daemon_running()
        if running:
            st.markdown(f'<p class="success-text">🟢 Bot RUNNING (PID: {pid})</p>', unsafe_allow_html=True)
        else:
            st.markdown(f'<p class="danger-text">🔴 Bot STOPPED</p>', unsafe_allow_html=True)

    with col3:
        settings = load_settings()
        paper_mode = settings.get("app_settings", {}).get("paper_trading_mode", False)
        if paper_mode:
            st.markdown(f'<p class="accent-text">📄 PAPER TRADING</p>', unsafe_allow_html=True)
        else:
            st.markdown(f'<p class="success-text">💰 LIVE TRADING</p>', unsafe_allow_html=True)

    st.markdown("---")


def render_dashboard():
    """Render main dashboard view"""
    st.markdown("## 📊 Dashboard")

    # Performance metrics
    perf = get_performance_summary()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Trades",
            value=perf['total_trades'],
            delta=f"+{perf['today_trades']} today"
        )

    with col2:
        pnl_color = "normal" if perf['total_pnl'] >= 0 else "inverse"
        st.metric(
            label="Total P&L",
            value=f"₹{perf['total_pnl']:.2f}",
            delta=f"₹{perf['today_pnl']:.2f} today",
            delta_color=pnl_color
        )

    with col3:
        df_positions = get_active_positions()
        st.metric(
            label="Active Positions",
            value=len(df_positions),
            delta=None
        )

    with col4:
        settings = load_settings()
        capital = settings.get("capital", {}).get("total_capital", 0)
        st.metric(
            label="Allocated Capital",
            value=f"₹{capital:.0f}",
            delta=None
        )

    st.markdown("---")

    # Active Positions Table
    st.markdown("### 📈 Active Positions")

    df_positions = get_active_positions()

    if not df_positions.empty:
        st.dataframe(
            df_positions,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No active positions")


def render_positions():
    """Render positions table"""
    st.markdown("## 📈 Active Positions")

    df_positions = get_active_positions()

    if not df_positions.empty:
        # Format numbers
        df_display = df_positions.copy()
        df_display['Avg Entry Price'] = df_display['Avg Entry Price'].apply(lambda x: f"₹{x:.2f}")
        df_display['Total Cost'] = df_display['Total Cost'].apply(lambda x: f"₹{x:.2f}")

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )

        st.caption(f"Total Positions: {len(df_positions)}")
    else:
        st.info("No active positions")


def render_trades():
    """Render trades history"""
    st.markdown("## 📜 Trades History")

    df_trades = load_trades_from_db()

    if not df_trades.empty:
        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_symbol = st.selectbox(
                "Symbol",
                options=["All"] + sorted(df_trades['symbol'].unique().tolist())
            )

        with col2:
            filter_action = st.selectbox(
                "Action",
                options=["All", "BUY", "SELL"]
            )

        with col3:
            filter_days = st.selectbox(
                "Time Period",
                options=["Today", "Last 7 Days", "Last 30 Days", "All Time"]
            )

        # Apply filters
        df_filtered = df_trades.copy()

        if filter_symbol != "All":
            df_filtered = df_filtered[df_filtered['symbol'] == filter_symbol]

        if filter_action != "All":
            df_filtered = df_filtered[df_filtered['action'] == filter_action]

        if filter_days == "Today":
            today = datetime.now().date()
            df_filtered = df_filtered[df_filtered['timestamp'].dt.date == today]
        elif filter_days == "Last 7 Days":
            week_ago = datetime.now() - timedelta(days=7)
            df_filtered = df_filtered[df_filtered['timestamp'] >= week_ago]
        elif filter_days == "Last 30 Days":
            month_ago = datetime.now() - timedelta(days=30)
            df_filtered = df_filtered[df_filtered['timestamp'] >= month_ago]

        # Display table
        if not df_filtered.empty:
            df_display = df_filtered[['timestamp', 'symbol', 'action', 'quantity', 'price', 'source']].copy()
            df_display['timestamp'] = df_display['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df_display['price'] = df_display['price'].apply(lambda x: f"₹{x:.2f}")

            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )

            st.caption(f"Showing {len(df_filtered)} trades")

            # Export button
            csv = df_display.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"arun_trades_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No trades match the selected filters")
    else:
        st.info("No trades in database")


def render_logs():
    """Render system logs"""
    st.markdown("## 📋 System Logs")

    num_lines = st.slider("Number of lines", min_value=10, max_value=500, value=100, step=10)

    logs = read_daemon_logs(num_lines)

    if logs:
        # Search filter
        search_term = st.text_input("🔍 Search logs", "")

        if search_term:
            logs = [line for line in logs if search_term.lower() in line.lower()]

        log_text = "".join(logs)
        st.code(log_text, language="log")

        st.caption(f"Showing last {len(logs)} lines from daemon.log")

        # Auto-refresh toggle
        if st.checkbox("Auto-refresh (every 5 seconds)", value=False):
            time.sleep(5)
            st.rerun()
    else:
        st.info("No logs available. Start the daemon to generate logs.")


def render_settings():
    """Render settings (read-only)"""
    st.markdown("## ⚙️ Settings (Read-Only)")

    st.warning("⚠️ Settings are READ-ONLY. Use the desktop app to modify settings.")

    settings = load_settings()

    if settings:
        # Broker Settings
        with st.expander("🏦 Broker Settings", expanded=False):
            broker = settings.get("broker", {})
            st.json({
                "Broker": broker.get("name", "N/A"),
                "Client Code": broker.get("client_code", "N/A"),
                "TOTP Configured": bool(broker.get("totp_secret"))
            })

        # Capital Settings
        with st.expander("💰 Capital Settings", expanded=True):
            capital = settings.get("capital", {})
            st.json(capital)

        # Risk Settings
        with st.expander("🛡️ Risk Settings", expanded=False):
            risk = settings.get("risk", {})
            st.json(risk)

        # Strategies
        with st.expander("📈 Strategies", expanded=False):
            strategies = settings.get("strategies", {})
            st.json(strategies)

        # App Settings
        with st.expander("🔧 App Settings", expanded=False):
            app_settings = settings.get("app_settings", {})
            st.json(app_settings)
    else:
        st.error("Failed to load settings.json")


# ====================== Main App ======================

def main():
    """Main app"""

    # Authentication
    if not check_password():
        return

    # Header
    render_header()

    # Sidebar navigation
    st.sidebar.markdown("## 📱 Navigation")

    page = st.sidebar.radio(
        "Go to",
        options=["Dashboard", "Positions", "Trades History", "System Logs", "Settings"],
        label_visibility="collapsed"
    )

    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (5s)", value=False)

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ Info")
    st.sidebar.info(f"""
    **ARUN Bot Monitor v1.0**

    Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

    **Controls:**
    - Use `bot_daemon.py` to start/stop the bot
    - This dashboard is READ-ONLY

    **Files:**
    - Settings: `settings.json`
    - Database: `database/trades.db`
    - Logs: `daemon.log`
    """)

    # Render selected page
    if page == "Dashboard":
        render_dashboard()
    elif page == "Positions":
        render_positions()
    elif page == "Trades History":
        render_trades()
    elif page == "System Logs":
        render_logs()
    elif page == "Settings":
        render_settings()

    # Auto-refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()


if __name__ == "__main__":
    main()
