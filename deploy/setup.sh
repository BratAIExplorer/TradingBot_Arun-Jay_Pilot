#!/bin/bash
# =============================================================================
# Zepp Setup Script — ARUN Trading Bot on Hostinger VPS
# =============================================================================
# Run this on the VPS as root:
#   bash setup.sh
#
# What it does:
#   1. Creates /opt/zepp/ (isolated from all other projects)
#   2. Installs Python 3.11 + venv if needed
#   3. Creates Python virtual environment
#   4. Installs dependencies
#   5. Creates .env file (you fill in the PIN)
#   6. Installs systemd services (does NOT start them — you do that manually)
#   7. Prints next steps
#
# What it does NOT touch:
#   - Existing nginx config
#   - Existing services (cloudflared, uvicorn, docker, postgresql)
#   - Any files outside /opt/zepp/
# =============================================================================

set -e

ZEPP_DIR="/opt/zepp"
PYTHON_MIN="3.10"

echo ""
echo "=============================="
echo "  Zepp Setup — ARUN Bot VPS"
echo "=============================="
echo ""

# --- Safety: Check we're on Linux ---
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "ERROR: This script must run on Linux (Ubuntu). Run it on your VPS via SSH."
    exit 1
fi

# --- Check existing projects are untouched ---
echo "[1/7] Checking existing services are safe..."
for svc in nginx postgresql docker cloudflared; do
    if systemctl is-active --quiet $svc 2>/dev/null; then
        echo "      OK: $svc is running (will not be touched)"
    fi
done
echo ""

# --- Check port 8001 is free ---
if ss -tlnp | grep -q ':8001'; then
    echo "WARNING: Port 8001 is already in use."
    ss -tlnp | grep ':8001'
    read -p "Continue anyway? (y/N): " confirm
    [[ "$confirm" == "y" || "$confirm" == "Y" ]] || exit 1
fi
echo "      OK: Port 8001 is available"
echo ""

# --- Python ---
echo "[2/7] Checking Python..."
PYTHON_BIN=""
for py in python3.11 python3.10 python3; do
    if command -v $py &>/dev/null; then
        VER=$($py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if python3 -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
            PYTHON_BIN=$py
            echo "      Found: $py ($VER)"
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

# --- Create Zepp directory ---
echo "[3/7] Creating /opt/zepp/ ..."
if [ -d "$ZEPP_DIR" ]; then
    echo "      /opt/zepp/ already exists — updating only"
else
    mkdir -p "$ZEPP_DIR"
    echo "      Created /opt/zepp/"
fi
mkdir -p "$ZEPP_DIR/database"
mkdir -p "$ZEPP_DIR/logs"
echo "      Directory structure ready"
echo ""

# --- Virtual environment ---
echo "[4/7] Creating Python virtual environment..."
if [ ! -d "$ZEPP_DIR/venv" ]; then
    $PYTHON_BIN -m venv "$ZEPP_DIR/venv"
    echo "      Virtualenv created"
else
    echo "      Virtualenv already exists — skipping"
fi
echo ""

# --- Install dependencies ---
echo "[5/7] Installing Python dependencies..."
"$ZEPP_DIR/venv/bin/pip" install --quiet --upgrade pip
"$ZEPP_DIR/venv/bin/pip" install --quiet \
    fastapi==0.110.0 \
    uvicorn[standard]==0.27.0 \
    python-multipart==0.0.9 \
    pandas==2.2.0 \
    numpy==1.26.4 \
    requests==2.31.0 \
    pyotp==2.9.0 \
    yfinance==0.2.37 \
    python-dotenv==1.0.0
echo "      Dependencies installed"
echo ""

# --- .env file ---
echo "[6/7] Creating .env file..."
if [ -f "$ZEPP_DIR/.env" ]; then
    echo "      .env already exists — not overwriting"
else
    cat > "$ZEPP_DIR/.env" << 'ENVEOF'
# Zepp Environment Variables
# IMPORTANT: Keep this file private. Never commit to git.

# PIN required for panic stop, start, and settings changes
# Choose any strong PIN (e.g. 6+ digits)
ZEPP_PIN=CHANGE_THIS_PIN

# Paths (defaults are correct if code is in /opt/zepp/)
ZEPP_DB_PATH=/opt/zepp/database/trades.db
ZEPP_SETTINGS_PATH=/opt/zepp/settings.json
ENVEOF
    echo "      .env created at /opt/zepp/.env"
    echo "      *** IMPORTANT: Edit /opt/zepp/.env and set ZEPP_PIN ***"
fi
echo ""

# --- Systemd services ---
echo "[7/7] Installing systemd services..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

install_service() {
    local name=$1
    local src="$SCRIPT_DIR/$name"
    local dst="/etc/systemd/system/$name"
    if [ -f "$src" ]; then
        cp "$src" "$dst"
        chmod 644 "$dst"
        echo "      Installed: $dst"
    else
        echo "      WARNING: $src not found — copy it manually"
    fi
}

install_service "zepp-web.service"
install_service "zepp-trading.service"
systemctl daemon-reload
echo ""

# --- Summary ---
echo "=============================="
echo "  Setup Complete!"
echo "=============================="
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Upload your bot code to /opt/zepp/:"
echo "   scp -r . root@76.13.179.32:/opt/zepp/"
echo ""
echo "2. Edit the PIN in /opt/zepp/.env:"
echo "   nano /opt/zepp/.env"
echo "   (Change CHANGE_THIS_PIN to something secure)"
echo ""
echo "3. Start the web dashboard:"
echo "   systemctl start zepp-web"
echo "   systemctl enable zepp-web   # auto-start on reboot"
echo ""
echo "4. Test from your phone:"
echo "   http://76.13.179.32:8001"
echo ""
echo "5. When ready to run trading engine on VPS:"
echo "   systemctl start zepp-trading"
echo "   systemctl enable zepp-trading"
echo ""
echo "6. View logs:"
echo "   tail -f /opt/zepp/logs/web.log"
echo "   tail -f /opt/zepp/logs/trading.log"
echo ""
echo "NOTE: Port 8001 must be open in your Hostinger firewall."
echo "      Go to: Hostinger Panel > VPS > Firewall > Add Rule > TCP 8001"
echo ""
