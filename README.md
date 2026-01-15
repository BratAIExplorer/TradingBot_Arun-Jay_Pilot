# 📈 ARUN (Automated RSI-based Utility Network)
### Advanced Algorithmic Trading Bot for Indian Markets

ARUN is a robust, Python-based algorithmic trading bot designed specifically for the Indian stock market (NSE/BSE). It utilizes real-time RSI indicators to execute trades automatically across multiple symbols and timeframes.

![ARUN Dashboard](file:///c:/Users/user/.gemini/antigravity/brain/4464297b-e7f7-4247-986f-ea5ac2fdff03/uploaded_image_1768144198898.png)

## ✨ Features

- **🚀 Real-time Execution**: Automated buy/sell signals based on RSI thresholds.
- **📊 Interactive Dashboard**: Monitor live positions, RSI values, and trade history in a sleek GUI.
- **🔐 Secure Credentials**: API keys, passwords, and tokens are encrypted using Fernet (cryptography).
- **❓ In-GUI Help**: Click the "?" icons in the Settings to learn exactly where to find your API keys and tokens for each broker.
- **🛡️ Advanced Risk Management**:
  - **Never Sell at Loss**: Optional override for stop-loss when in loss territory.
  - **Catastrophic Stop**: Emergency exit for extreme market drops.
  - **Daily Circuit Breaker**: Auto-stops if total portfolio loss exceeds limit.
- **💼 Smart Capital Allocation**: Dual-mode quantity selection (Fixed shares vs. % Capital).
- **🔍 Symbol Validation**: Integrated validation of stock symbols via yfinance.

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/BratAIExplorer/TradingBot_Arun-Jay_Pilot.git
   cd "LiveBot Code"
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Required: customtkinter, yfinance, pandas, numpy, cryptography, requests, python-dotenv*

3. **Setup Environment**:
   - Create a `.env` file with your broker credentials.
   - Run `settings_gui.py` to configure your preferences.

## 🚀 Getting Started

1. **Configure Symbols**: Edit `config_table.csv` to add your target stocks.
2. **Launch Settings**:
   ```bash
   python settings_gui.py
   ```
   - Enter your API Key/Secret.
   - Set your Risk and Capital limits.
   - Click "Validate Symbols" in the Stocks tab.
3. **Start Trading**:
   ```bash
   python kickstart_gui.py
   ```
   - Click "▶ Start Bot" to begin automated scanning and execution.

## 📈 Trading Strategy

ARUN follows a mean-reversion RSI strategy:
- **BUY**: Triggered when RSI drops below the defined **Buy RSI** (default: 30-35).
- **SELL**: Triggered when RSI rises above the **Sell RSI** (default: 65-70) OR **Profit Target** is reached.
- **EXIT**: Managed by strict risk controls (Stop-Loss, Catastrophic Stop).

## ⚠️ Disclaimer

Trading in the stock market involves substantial risk. This bot is provided for educational and utility purposes only. Always test thoroughly in **Paper Trading Mode** before using live capital. The developers are not responsible for any financial losses incurred.

---
Built with ❤️ for Indian Traders.
