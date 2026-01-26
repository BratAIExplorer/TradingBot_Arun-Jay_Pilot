# 🚀 Founder's Start Guide (Titan V3.0.1)

**Date**: January 26, 2026
**Version**: 3.0.1 (Stability Release)
**Branch**: `backup-state-jan26` (Latest)

---

## 🟢 How to Start the Bot (Testing Mode)

The system has been patched with critical fixes for **SIP (Buy the Dip)** and **Paper Trading Risk**.

### Step 1: Launch the Dashboard
Double-click the following file in the project folder:
👉 `LAUNCH_DASHBOARD_ENHANCED.bat`

*(This will open the Dark Neon Command Center)*

### Step 2: Verify Configuration
1.  Go to **Settings Tab**.
2.  Enable **"SIMULATION MODE (Paper Trading)"** (Recommended for first run).
3.  Check **"Risk Controls"**: Ensure Stop Loss is ~5% and Profit Target is ~10%.
4.  Click **"SAVE CONFIGURATION"**.

### Step 3: Start the Engine
1.  Go to **Dashboard Tab**.
2.  Click the green **"▶ START SYSTEM"** button.
3.  **Watch the Log**: You should see:
    *   `✅ LOADED KICKSTART V3.0.1`
    *   `✅ SIP Engine Initialized`
    *   `🟢 Market open — resuming` (if market is open)

---

## 🧪 Verification Checklist (What to look for)

| Feature | Action to Test | Expected Result |
| :--- | :--- | :--- |
| **SIP Strategy** | Price drops 2% on a defined SIP Bucket stock | Log shows `Targeting SIP allocation` and triggers BUY. |
| **Risk Manager** | Paper Position drops below 5% | Log shows `🚨 RISK TRIGGER: Stop Loss` and executes SELL. |
| **Profit Logic** | SIP Position hits 10% Profit | Log executes SELL (New Feature). |
| **App Stability** | Click "STOP" and "START" multiple times | App responds instantly without freezing. |

---

## ⚠️ Troubleshooting

*   **"Connection Failed"**: Check your TOTP in Settings > Broker.
*   **"No Trades"**: Ensure **"SIMULATION MODE"** is ON if outside market hours (though simulation usually requires live data, the engine will still initialize).
*   **Stuck?**: Run `HEADLESS_ENGINE.bat` to see raw error logs in the console.
