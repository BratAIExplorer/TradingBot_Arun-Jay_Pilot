# ARUN Trading Bot - Sharing Guide

Follow these steps to safely share the trading bot with your friends.

## For You (The Sharer)

Before copying or zipping the folder, you **MUST** delete the following files from the copy to protect your account:

1.  **`settings.json`**: This contains your live broker credentials (API keys, passwords).
2.  **.encryption_key**: Each user must generate their own key for data security.
3.  **`bot_state.json`**: This contains your personal portfolio and active positions.
4.  **`market_data_cache.json`**: Not sensitive, but deleting it reduces the zip size.
5.  **`nse_master.csv`**: Not sensitive, but will be re-downloaded fresh by the new user.
6.  **`logs/` folder contents**: To avoid sharing your historical trade logs.

### Recommended Sharing Checklist
- [ ] Create a copy of the `TradingBots-Aruns Project` folder.
- [ ] In the COPY, delete the files listed above.
- [ ] Zip the copy and send it to your friend.

> [!CAUTION]
> **Developer Warning (File Locking)**: DO NOT rename or move `settings.json` while any bot process (wizard, dashboard, or engine) is still active. These processes may flush their in-memory state back to disk on exit or logout, potentially overwriting your restored file with their current (possibly empty) session data. Always ensure all bot windows are closed before manual file maintenance.

---

## For Your Friend (The User)

1.  **Prerequisites**:
    -   mStock Broker Account (Open at miaboraonline.com)
    -   mStock API Credentials (Get from developer.mstock.trade)
    -   Python 3.11+ (Installer handles this)
2.  **Getting Started**:
    -   Extract the zip folder.
    -   Run **`START_HERE.bat`**.
    -   Follow the **First-Run Setup Wizard** to enter API credentials and risk preferences.
3.  **Safety First**:
    -   **Start in Paper Trading Mode** (Enabled by default).
    -   Test the system with small quantities once comfortable.

> [!WARNING]
> Trading involves risk of loss. Always use caution and never share your `settings.json` file with anyone.
