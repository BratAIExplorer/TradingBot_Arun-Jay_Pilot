# 📈 ARUN (Automated RSI-based Utility Network)
### Advanced Algorithmic Trading & Investment Bot for Indian Markets

ARUN is a smart, automated trading assistant designed for Indian investors. It automates RSI-based buying and selling on the NSE/BSE markets (via mStock). It is designed to be your **"Excel for Trading"**—you set the rules, and it executes them with discipline.

![ARUN Dashboard](file:///c:/Users/user/.gemini/antigravity/brain/4464297b-e7f7-4247-986f-ea5ac2fdff03/uploaded_image_1768144198898.png)

---

## 🌟 New V1 Product Features (Friends & Family Release)

### 🧪 Paper Trading Mode (Simulator)
- **What it is:** A risk-free simulation mode.
- **How it works:** The bot "pretends" to buy and sell. Trades are recorded in a local database, but **NO real money** is used.
- **Visuals:** Paper trades appear in **BLUE** on the dashboard. Real trades (if you enable them) appear in **GREEN/RED**.
- **Default:** Enabled by default for safety.

### 💎 Investment Mode (Accumulation)
- **The "HODL" Strategy:** Set any stock to **INVEST** mode instead of **TRADE**.
- **Behavior:** The bot will **BUY the dip** (when RSI is low) but will **NEVER Sell** based on RSI signals.
- **Goal:** Perfect for accumulating ETFs (NIFTYBEES, GOLDBEES) or Bluechip stocks for long-term wealth.
- *Note: Profit Targets (e.g., +20%) will still trigger a sell if configured.*

### 🛡️ Nifty 50 Safety Filter
- **Guardrail:** A toggle to strictly block trading of any stock NOT in India's top 50 companies.
- **Why:** Prevents accidental exposure to risky, low-volume "penny stocks."

---

## ✨ Core Features

- **🚀 Real-time Execution**: Automated buy/sell signals based on RSI thresholds.
- **📊 Interactive Dashboard**: Monitor live positions, RSI values, and trade history.
- **🔐 Secure Credentials**: API keys are encrypted locally on your machine.
- **💼 Smart Capital**: Allocates capital based on your settings (Fixed Qty or % Portfolio).

## 🚀 Getting Started (Desktop App)

### How to Distribute (Friends & Family)
Since you are distributing this yourself, here is the easiest way for your friends to get started:

**Method 1: Share the EXE directly**
1.  Run `install_and_build.bat` on your computer.
2.  Go to the `dist` folder.
3.  Zip the `ARUN_Bot.exe` file.
4.  Send it to your friends via Email/WhatsApp/Drive.
5.  They just double-click to run.

**Method 2: One-Click Source Setup**
If they downloaded the source code (Zip from GitHub):
1.  Extract the folder.
2.  Double-click **`install_and_build.bat`**.
3.  Wait for it to finish.
4.  It will automatically create an **ARUN Bot shortcut** on their Desktop.

### Usage Guide

1.  **First Run:**
    - Accept the **User Responsibility Disclaimer**.
    - Go to **Settings** -> **Broker** tab.
    - Enter your mStock credentials (API Key, Secret, Client Code).
    - *Tip:* Keep "Enable Paper Trading" **ON** for your first week!

3.  **Configure Strategy:**
    - Go to **Stocks** tab.
    - Click **➕ Add**.
    - **Symbol:** `TCS` | **Exchange:** `NSE`
    - **Mode:** `INVEST` (for long term) or `TRADE` (for swing trading).
    - **RSI:** Buy < 30, Sell > 70.

4.  **Start:**
    - Close Settings.
    - Click **▶ Start Bot** on the main dashboard.

---

## 🛠️ For Developers (Source Code)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/BratAIExplorer/TradingBot_Arun-Jay_Pilot.git
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Build the .exe**:
   ```cmd
   build_release.bat
   ```
   *This uses PyInstaller to package the app into `dist/ARUN_Bot.exe`.*

## ❓ FAQ & Troubleshooting

### Q: Does this run 24/7?
**A:** Because this is a **Desktop Application**, it only runs when your computer is ON and the app is OPEN.
*   If your PC sleeps, the bot stops.
*   If you need true 24/7 trading (e.g., for servers), you should run this on a **VPS (Virtual Private Server)** or wait for the Phase 2 Web Version.

### Q: Can I add more strategies?
**A:** Yes! The current version supports **RSI Trading** and **Investment (Accumulation)**.
*   The architecture is modular. New strategies can be added by modifying the `kickstart.py` logic engine.
*   *Note:* This requires Python knowledge.

### Q: The Installer Failed!
**A:** Check the **`install_log.txt`** file created in the folder. It contains the detailed error message.
*   **Common Fix:** Ensure you have Python 3.10+ installed and added to your PATH.

## ⚠️ Disclaimer

**Not Investment Advice.** ARUN is a software tool for order execution. You are solely responsible for the configuration, strategy, and risk management. Always test strategies in **Paper Trading Mode** first. The developers are not liable for financial losses.

---
Built with ❤️ for Indian Traders.
