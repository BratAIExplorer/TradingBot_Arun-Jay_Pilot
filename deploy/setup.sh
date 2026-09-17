#!/bin/bash
# =============================================================================
# TradingBot Setup Script — Ubuntu 24.04 VPS (Kuala Lumpur)
# =============================================================================
# Run this on the VPS as root:
#   bash setup.sh
#
# What it does:
#   1. Creates /opt/tradingbot/ (isolated from anything else on this VPS)
#   2. Installs Python 3.11 + venv if needed
#   3. Creates a virtual environment, installs dependencies
#   4. Creates a .env file (you fill in the PIN)
#   5. Installs the two systemd services (does NOT start them — you do that)
#   6. Prints next steps
#
# What it does NOT touch:
#   - Existing nginx config, or any other service already on this VPS
#   - Any files outside /opt/tradingbot/
# =============================================================================

set -e

APP_DIR="/opt/tradingbot"

echo ""
echo "=================================="
echo "  TradingBot Setup — Ubuntu VPS"
echo "=================================="
echo ""

# --- Safety: Linux only ---
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "ERROR: run this on the VPS via SSH, not locally."
    exit 1
fi

# --- Check existing services are untouched ---
echo "[1/7] Checking existing services are safe..."
for svc in nginx postgresql docker cloudflared; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        echo "      OK: $svc is running (will not be touched)"
    fi
done
echo ""

# --- Check port 8001 is free ---
echo "[2/7] Checking port 8001..."
if ss -tlnp | grep -q ':8001'; then
    echo "WARNING: Port 8001 is already in use."
    ss -tlnp | grep ':8001'
    read -p "Continue anyway? (y/N): " confirm
    [[ "$confirm" == "y" || "$confirm" == "Y" ]] || exit 1
fi
echo "      OK: Port 8001 is available"
echo ""

# --- Python ---
echo "[3/7] Checking Python..."
PYTHON_BIN=""
for py in python3.11 python3.10 python3; do
    if command -v "$py" &>/dev/null; then
        if "$py" -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
            PYTHON_BIN=$py
            echo "      Found: $py"
            break
        fi
    fi
done
if [ -z "$PYTHON_BIN" ]; then
    echo "      Python 3.10+ not found. Installing Python 3.11..."
    apt-get update -qq
    apt-get install -y python3.11 python3.11-venv python3.11-dev
    PYTHON_BIN=python3.11
fi
echo ""

# --- App directory ---
echo "[4/7] Creating $APP_DIR ..."
mkdir -p "$APP_DIR/database" "$APP_DIR/logs"
echo "      Directory structure ready"
echo ""

# --- Virtual environment + deps ---
echo "[5/7] Creating virtual environment and installing dependencies..."
if [ ! -d "$APP_DIR/venv" ]; then
    "$PYTHON_BIN" -m venv "$APP_DIR/venv"
fi
"$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
if [ -f "$APP_DIR/requirements.txt" ]; then
    "$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
fi
if [ -f "$APP_DIR/backend/requirements.txt" ]; then
    "$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/backend/requirements.txt"
fi
echo "      Dependencies installed"
echo ""

# --- .env file ---
echo "[6/7] Creating .env file..."
if [ -f "$APP_DIR/.env" ]; then
    echo "      .env already exists — not overwriting"
else
    cat > "$APP_DIR/.env" << 'ENVEOF'
# TradingBot environment variables
# IMPORTANT: keep this file private. Never commit to git.

# PIN required for start/stop and any write from the web dashboard.
TRADINGBOT_PIN=CHANGE_THIS_PIN

# IBKR (US markets) — IB Gateway must be running on this same VPS for the IBKR
# dashboard tab to work. Port: 4002=paper, 4001=live, 7497/7496=TWS equivalents.
# This MUST be set before tradingbot-web.service starts, or it silently defaults to
# 4002 and every IBKR call fails with "connection refused" even if Gateway IS
# running — the port default is read once at import time, not re-checked later.
IBKR_PORT=4002
ENVEOF
    echo "      .env created — *** edit it and set TRADINGBOT_PIN ***"
fi
echo ""

# --- Systemd services ---
echo "[7/7] Installing systemd services..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
install_service() {
    local name=$1 src="$SCRIPT_DIR/$1" dst="/etc/systemd/system/$1"
    if [ -f "$src" ]; then
        cp "$src" "$dst"
        chmod 644 "$dst"
        echo "      Installed: $dst"
    else
        echo "      WARNING: $src not found — copy it manually"
    fi
}
install_service "tradingbot-web.service"
install_service "tradingbot-trading.service"
systemctl daemon-reload
echo ""

echo "=================================="
echo "  Setup Complete!"
echo "=================================="
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Upload the bot code to $APP_DIR (from your machine):"
echo "   scp -r . root@<VPS_IP>:$APP_DIR/"
echo ""
echo "2. Edit the PIN:"
echo "   nano $APP_DIR/.env"
echo ""
echo "3. paper_trading_mode MUST be true in settings.json before first start"
echo "   on this VPS — check it manually, do not skip this."
echo ""
echo "4. Start the web dashboard only, first:"
echo "   systemctl start tradingbot-web"
echo "   systemctl enable tradingbot-web"
echo ""
echo "5. Confirm it's reachable: http://<VPS_IP>:8001"
echo ""
echo "6. Only after the dashboard looks right, start the trading engine:"
echo "   systemctl start tradingbot-trading"
echo "   systemctl enable tradingbot-trading"
echo ""
echo "7. Logs:"
echo "   tail -f $APP_DIR/logs/web.log"
echo "   tail -f $APP_DIR/logs/trading.log"
echo ""
echo "NOTE: open port 8001 in the VPS firewall (ufw allow 8001, or your"
echo "      provider's control-panel firewall)."
echo ""
