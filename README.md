# 🚀 ARUN Trading Bot - Autonomous Retail Unit

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey.svg)](https://github.com)
[![Status](https://img.shields.io/badge/status-Active%20Development-green.svg)](https://github.com)

**Professional algorithmic trading bot for Indian stock markets with RSI-based strategies, comprehensive risk management, and real-time monitoring.**

---

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Documentation](#-documentation)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [Support](#-support)
- [License](#-license)

---

## ✨ Features

### Core Trading Features
- **RSI Mean Reversion Strategy**: Buy when RSI < 30 (oversold), Sell when RSI > 70 (overbought)
- **Multi-Symbol Trading**: Track and trade multiple stocks simultaneously
- **Real-Time Market Data**: Live quotes and candle data from broker APIs
- **Risk Management**: Position limits, stop-loss, profit targets, and drawdown monitoring
- **Offline Detection**: Automatic pause when internet connectivity is lost
- **Paper Trading Mode**: Test strategies without real money

### User Interface
- **Modern Dashboard**: CustomTkinter-based GUI with dark mode
- **Live Position Tracking**: Real-time P&L updates for all open positions
- **Trade History**: Comprehensive logging of all trades with performance metrics
- **Settings Management**: Easy configuration via tabbed interface
- **Notifications**: Telegram alerts for trades and risk events

### Technical Features
- **Multi-Broker Support**: Currently supports mStock (Zerodha, Angel One coming soon)
- **Auto-Login**: TOTP-based automatic authentication
- **Database Logging**: SQLite database for trade history and analytics
- **Symbol Validation**: Automatic validation against NSE stock list
- **Headless Mode**: Run bot without GUI for VPS deployment

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Active mStock trading account with API access
- Internet connection

### Installation

1. **Clone or download** this repository:
   ```bash
   git clone https://github.com/yourusername/TradingBot_Arun-Jay_Pilot.git
   cd TradingBot_Arun-Jay_Pilot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the dashboard**:
   ```bash
   python dashboard_v2.py
   ```
   Or double-click `LAUNCH_ARUN.bat` on Windows.

4. **Configure settings**:
   - Navigate to the **Settings** tab
   - Enter your mStock API credentials
   - Configure trading parameters (capital allocation, RSI thresholds, etc.)
   - Add symbols to track in `config_table.csv`

5. **Start trading**:
   - Click **▶ Start Engine**
   - Monitor positions in real-time
   - Check trade history in the **Trades** tab

---

## 🏗️ Architecture

### Current Architecture (v3.0)

```
┌─────────────────────────────────────────┐
│      CustomTkinter Dashboard            │
│       (dashboard_v2.py)                 │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   Monolithic Trading Engine             │
│      (kickstart.py)                     │
│                                         │
│  - Trading Logic                        │
│  - Market Data Fetching                 │
│  - Risk Management                      │
│  - Order Execution                      │
│  - Position Management                  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  SQLite Database    │  mStock API       │
│  (trades.db)        │  (Broker)         │
└─────────────────────────────────────────┘
```

### Planned Architecture (v4.0 - SaaS)

See [Architecture Overview](Documentation/architecture_overview.md) for the proposed service-oriented architecture with multi-tenancy, async operations, and horizontal scaling.

---

## 📚 Documentation

### Comprehensive Guides
- **[Comprehensive Audit Report](Documentation/comprehensive_audit_report.md)** - Critical bugs analysis, security review, and UX improvements
- **[Architecture Overview](Documentation/architecture_overview.md)** - System design, service layer breakdown, and scalability considerations
- **[SaaS Transformation Plan](Documentation/saas_transformation_plan.md)** - Roadmap for cloud-native multi-tenant platform
- **[Implementation Plan](Documentation/implementation_plan.md)** - Step-by-step development roadmap
- **[Bugs and Fixes](Documentation/BUGS_AND_FIXES.md)** - Known issues and their resolutions

### Quick References
- **[Walkthrough](Documentation/walkthrough.md)** - User journey and feature explanations
- **[Product Catalogue](product_catalogue.md)** - Complete feature list

---

## 🔧 Installation

### System Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: 3.11 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space
- **Internet**: Stable connection required for live trading

### Dependencies

```txt
# Core
pandas==2.1.4
numpy==1.26.2
requests==2.31.0
python-dotenv==1.0.0

# GUI
customtkinter==5.2.1
Pillow==10.1.0

# Authentication
pyotp==2.9.0

# Notifications
python-telegram-bot==20.7

# Database
sqlite3 (built-in)

# Technical Indicators
ta-lib==0.4.28  # Optional for advanced indicators
```

### Installation Steps

1. **Install Python**:
   - Download from [python.org](https://www.python.org/downloads/)
   - ⚠️ **Important**: Check "Add Python to PATH" during installation

2. **Clone Repository**:
   ```bash
   git clone https://github.com/yourusername/TradingBot_Arun-Jay_Pilot.git
   cd TradingBot_Arun-Jay_Pilot
   ```

3. **Create Virtual Environment** (recommended):
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Mac/Linux
   source venv/bin/activate
   ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Verify Installation**:
   ```bash
   python dashboard_v2.py
   ```

---

## ⚙️ Configuration

### Broker Credentials

1. **Get mStock API Credentials**:
   - Log in to [mStock Developer Portal](https://developer.mstock.trade)
   - Generate API Key
   - Enable TOTP and save the secret key

2. **Configure in Dashboard**:
   - Open ARUN dashboard
   - Go to **Settings → Broker Settings**
   - Enter API Key
   - Enter TOTP Secret (for auto-login)
   - Click **Test Connection**

### Trading Parameters

#### App Settings
- **Paper Trading Mode**: Enable for simulation (no real orders)
- **Auto-Start**: Start trading engine on app launch
- **Nifty 50 Only**: Trade only stocks from Nifty 50 index
- **Headless Mode**: Run without GUI (for VPS/server deployment)

#### Capital Allocation
- **Total Capital**: Maximum capital to deploy (e.g., ₹1,00,000)
- **Per Trade Allocation**: Percentage of capital per trade (e.g., 10%)
- **Max Open Positions**: Limit simultaneous positions

#### RSI Strategy
- **Buy Threshold**: RSI level to trigger buy (default: 30)
- **Sell Threshold**: RSI level to trigger sell (default: 70)
- **Timeframe**: Candle timeframe for RSI calculation (1T, 5T, 15T, 30T, 60T, 1D)
- **RSI Period**: Number of periods for RSI (default: 14)

#### Risk Management
- **Stop Loss**: Maximum loss per position (%)
- **Profit Target**: Target profit per position (%)
- **Daily Loss Limit**: Maximum total loss per day (₹)
- **Max Drawdown**: Circuit breaker threshold (%)

### Symbol Configuration

Edit `config_table.csv` to add/remove stocks:

```csv
Symbol,Exchange,Timeframe,RSI_Buy_Threshold,RSI_Sell_Threshold
GOLDBEES,NSE,15T,30,70
TATASTEEL,NSE,15T,28,72
RELIANCE,NSE,30T,30,70
```

**Symbol Validation**: Use the **Symbol Validator** tab to verify stocks against NSE list.

---

## 📖 Usage

### Starting the Bot

1. **Launch Dashboard**:
   ```bash
   python dashboard_v2.py
   ```
   Or double-click `LAUNCH_ARUN.bat` (Windows)

2. **Verify Configuration**:
   - Check broker connection status (green = online)
   - Verify symbols are loaded in table
   - Confirm capital allocation settings

3. **Start Trading Engine**:
   - Click **▶ Start Engine** button
   - Watch live log for trading activity
   - Monitor positions table for open trades

### Monitoring

#### Dashboard Overview
- **System Status**: Online/Offline, Engine Running/Stopped
- **Positions Table**: Live P&L for all open positions
- **Recent Trades**: Last 10 trades executed
- **Performance Metrics**: Daily P&L, Win Rate, Total Trades

#### Tabs
- **Dashboard**: Main trading view
- **Settings**: All configuration options
- **Trades**: Complete trade history
- **Symbol Validator**: Check symbol validity
- **Knowledge Center**: Strategy documentation

### Notifications

Configure Telegram alerts in **Settings → Notifications**:
1. Create Telegram bot via [@BotFather](https://t.me/botfather)
2. Get bot token
3. Get your chat ID (use [@userinfobot](https://t.me/userinfobot))
4. Enter credentials in settings
5. Test notification

Alerts are sent for:
- Trade executions (BUY/SELL)
- Stop-loss triggers
- Profit target hits
- Circuit breaker activations
- System errors

---

## 🗺️ Roadmap

### Phase 1: Stability & Bug Fixes ✅ (Current)
- [x] Fix critical bugs (duplicate functions, thread safety)
- [x] Comprehensive documentation
- [x] Security hardening (credential management)
- [ ] Unit test coverage (target: 70%)
- [ ] Integration tests

### Phase 2: Architecture Refactoring (Months 1-2)
- [ ] Extract services from monolith
- [ ] Implement dependency injection
- [ ] Add async/await for API calls
- [ ] Repository pattern for data access
- [ ] Event-driven architecture

### Phase 3: Web UI Development (Months 3-4)
- [ ] FastAPI backend with REST + WebSocket
- [ ] React frontend with Material-UI
- [ ] Real-time dashboard updates
- [ ] Mobile-responsive design
- [ ] Advanced analytics

### Phase 4: Multi-Broker Support (Month 5)
- [ ] Broker abstraction layer
- [ ] Zerodha adapter
- [ ] Angel One adapter
- [ ] ICICI Direct adapter
- [ ] OAuth integration flows

### Phase 5: SaaS Infrastructure (Months 6-8)
- [ ] Containerization (Docker)
- [ ] Kubernetes deployment
- [ ] Multi-tenancy architecture
- [ ] User authentication (JWT + OAuth2)
- [ ] Subscription management (Stripe/Razorpay)

### Phase 6: Advanced Features (Months 9-12)
- [ ] Strategy marketplace
- [ ] Backtesting engine
- [ ] Copy trading
- [ ] Mobile app (React Native)
- [ ] White-label platform

See [SaaS Transformation Plan](Documentation/saas_transformation_plan.md) for detailed roadmap.

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Reporting Bugs
1. Check [existing issues](https://github.com/yourusername/TradingBot_Arun-Jay_Pilot/issues)
2. Create new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots (if applicable)
   - Environment details (OS, Python version)

### Submitting Pull Requests
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes with clear commit messages
4. Add/update tests
5. Ensure all tests pass
6. Submit PR with description of changes

### Code Style
- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings to functions
- Keep functions < 50 lines (ideally)
- No bare `except:` statements
- Use explicit exception types

### Testing
```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=. --cov-report=html
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 💬 Support

### Get Help
- **Issues**: [GitHub Issues](https://github.com/yourusername/TradingBot_Arun-Jay_Pilot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/TradingBot_Arun-Jay_Pilot/discussions)
- **Email**: support@arunbot.com (coming soon)

### FAQ

**Q: Can I use this with Zerodha/Angel One?**
A: Currently only mStock is supported. Multi-broker support is planned for Phase 4 (Month 5).

**Q: Is paper trading safe?**
A: Yes! Paper trading mode simulates trades without placing real orders. Perfect for testing.

**Q: What if my internet disconnects?**
A: The bot automatically detects offline status and pauses trading. It resumes when connectivity is restored.

**Q: Can I run this on a VPS/cloud server?**
A: Yes! Enable headless mode in settings and run `python kickstart.py` instead of the dashboard.

**Q: Is this legal in India?**
A: Yes, algorithmic trading is legal for retail investors. However, ensure you comply with SEBI regulations.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 ARUN Trading Bot

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- **mStock**: For providing reliable broker API
- **CustomTkinter**: Beautiful modern UI components
- **Python Trading Community**: Inspiration and support

---

## ⚠️ Disclaimer

**Trading in stock markets involves substantial risk of loss and is not suitable for every investor. The valuation of stocks may fluctuate, and as a result, investors may lose more than their original investment.**

- This bot is for educational and research purposes
- No guarantee of profits or performance
- Past performance does not indicate future results
- Use at your own risk
- Always test strategies in paper trading mode first
- Consult a financial advisor before live trading

**The developers are not responsible for any financial losses incurred while using this software.**

---

## 📊 Project Status

- **Current Version**: 3.0 (Desktop App)
- **Next Release**: 3.1 (Bug Fixes & Stability) - Jan 2026
- **SaaS Launch**: Q3 2026 (Planned)

**Star ⭐ this repo if you find it useful!**

---

**Built with ❤️ for Indian retail traders**
