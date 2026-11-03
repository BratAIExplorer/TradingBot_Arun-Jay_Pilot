#!/bin/bash
# =============================================================================
# Headless IB Gateway setup — Ubuntu VPS (Kuala Lumpur)
# =============================================================================
# Run on the VPS as root, AFTER deploy/setup.sh:
#   bash setup_ibgateway.sh
#
# Installs IB Gateway + Xvfb (virtual display, Gateway is a GUI app) + IBC
# (IBController, automates the login dialog Gateway normally needs a human for).
# Does NOT touch tradingbot-web/trading services or anything from setup.sh.
#
# Ports: IBC starts Gateway which listens on 4001 (live) or 4002 (paper) —
# must match TradingMode in ibc/config.ini and IBKR_PORT in .env.
# =============================================================================
set -e

IBC_DIR="/opt/ibc"
GATEWAY_DIR="/opt/ibgateway"
IBC_VERSION="3.21.0"
GATEWAY_INSTALLER_URL="https://download2.interactivebrokers.com/installers/ibgateway/stable-standalone/ibgateway-stable-standalone-linux-x64.sh"

if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "ERROR: run this on the VPS via SSH, not locally."
    exit 1
fi

echo "[1/5] Installing Xvfb + unzip..."
apt-get update -qq
apt-get install -y xvfb unzip default-jre >/dev/null
echo "      OK"

echo "[2/5] Installing IB Gateway (unattended)..."
mkdir -p "$GATEWAY_DIR"
if [ ! -f "$GATEWAY_DIR/ibgateway/*/ibgateway" ] 2>/dev/null; then
    curl -sSL "$GATEWAY_INSTALLER_URL" -o /tmp/ibgateway-installer.sh
    chmod +x /tmp/ibgateway-installer.sh
    /tmp/ibgateway-installer.sh -q -dir "$GATEWAY_DIR"
    echo "      Installed to $GATEWAY_DIR"
else
    echo "      Already installed — skipping"
fi

echo "[3/5] Installing IBC (login automation)..."
mkdir -p "$IBC_DIR"
if [ ! -f "$IBC_DIR/scripts/ibcstart.sh" ]; then
    curl -sSL "https://github.com/IbcAlpha/IBC/releases/download/${IBC_VERSION}/IBCLinux-${IBC_VERSION}.zip" -o /tmp/ibc.zip
    unzip -q /tmp/ibc.zip -d "$IBC_DIR"
    chmod +x "$IBC_DIR"/*.sh "$IBC_DIR"/scripts/*.sh
    echo "      Installed to $IBC_DIR"
else
    echo "      Already installed — skipping"
fi

echo "[4/5] Installing IBC config..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ ! -f "$IBC_DIR/config.ini" ]; then
    cp "$SCRIPT_DIR/ibc/config.ini.template" "$IBC_DIR/config.ini"
    chmod 600 "$IBC_DIR/config.ini"
    echo "      *** EDIT $IBC_DIR/config.ini with real IBKR credentials before starting ***"
else
    echo "      config.ini already exists — not overwriting"
fi

echo "[5/5] Installing systemd service..."
install_service() {
    cp "$SCRIPT_DIR/$1" "/etc/systemd/system/$1"
    chmod 644 "/etc/systemd/system/$1"
    echo "      Installed: /etc/systemd/system/$1"
}
install_service "ibgateway-headless.service"
systemctl daemon-reload

echo ""
echo "=================================="
echo "  IB Gateway headless setup done"
echo "=================================="
echo ""
echo "NEXT STEPS:"
echo "1. nano $IBC_DIR/config.ini   — fill in IbLoginId / IbPassword / TradingMode"
echo "2. TradingMode in config.ini MUST match IBKR_PORT in $APP_DIR/.env"
echo "   (paper=4002, live=4001) — a mismatch fails silently, see HANDOVER doc."
echo "3. systemctl start ibgateway-headless"
echo "4. systemctl enable ibgateway-headless"
echo "5. Verify: python brokers/check_ibkr_connection.py (read-only, safe)"
echo "6. Only once that's green, start tradingbot-web to expose the IBKR tab."
echo ""
