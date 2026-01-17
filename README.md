# 🚀 ARUN Trading Bot - Setup Guide

Welcome to the **ARUN (Autonomous Retail Unit)**. This guide will help you set up and run the bot on your machine.

---

## 1. Prerequisites (Do this once)
You need **Python** installed to run this bot.

1.  **Download Python**: Go to [python.org/downloads](https://www.python.org/downloads/).
2.  **Install**: Run the installer. **IMPORTANT**: Check the box that says **"Add Python to PATH"** before clicking Install.

---

## 2. Installation
1.  **Unzip** the folder to your Desktop (e.g., `C:\Users\Arun\Desktop\ARUN_Bot`).
2.  Open the folder.
3.  Right-click anywhere in the white space and select **"Open Terminal here"** (or CMD).
4.  Type the following command and hit Enter to install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    *(Wait for it to finish downloading all libraries)*

---

## 3. Configuration
1.  Find the file named `settings.json` (or `settings_template.json`).
2.  If it's missing, just run the bot once, and it will create a default one.
3.  **Crucial Step**: You need to enter your **mStock Credentials**.
    *   **API Key**: From mStock Developer Portal.
    *   **TOTP Secret**: This is the most important part for Auto-Login.
    *   *You can do this via the Settings GUI inside the app.*

---

## 4. Launching the Bot
1.  Double-click the file **`dashboard_v2.py`** (if you have Python set to open .py files).
2.  OR, better yet, use the provided launcher:
    - Double-click **`LAUNCH_ARUN.bat`** (This ensures Python is found correctly).
3.  The **Titan V2 Dashboard** will open.
4.  Click **▶ Start Engine**.


---

## 5. Troubleshooting
*   **"403 Forbidden"**: Your API Key might be invalid, or your TOTP Secret is wrong. Check Settings.
*   **"System Offline"**: Check your internet connection.

---

**Questions?**
Check the "Knowledge Center" tab inside the application for detailed logic explanations.
