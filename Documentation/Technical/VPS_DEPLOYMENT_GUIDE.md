# 🚀 ARUN Trading Bot - VPS Deployment Guide

This guide details how to deploy the **Headless Architecture** (FastAPI Backend + Next.js Frontend) to a Linux VPS (Ubuntu 20.04/22.04 recommended).

## 📋 Prerequisites

Ensure your VPS has the following installed:
*   **Git**: `sudo apt install git`
*   **Python 3.10+**: `sudo apt install python3 python3-pip python3-venv`
*   **Node.js 18+ & npm**:
    ```bash
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    ```
*   **PM2** (Process Manager): `sudo npm install -g pm2`
*   **Nginx** (Web Server): `sudo apt install nginx`

---

## 1️⃣ Backend Setup (FastAPI)

1.  **Clone/Pull Repository**:
    ```bash
    git clone <your-repo-url> arun-bot
    cd arun-bot
    ```

2.  **Setup Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    pip install fastapi "uvicorn[standard]" python-multipart
    ```
    *(Note: Ensure `requirements.txt` includes all dependencies from `backend/`)*

4.  **Configure Environment**:
    *   Copy `env.example` to `.env` (or create one) with your API keys.

5.  **Test Run**:
    ```bash
    cd backend
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```
    *(Ctrl+C to stop after verifying it starts)*

---

## 2️⃣ Frontend Setup (Next.js)

1.  **Navigate to Frontend Directory**:
    ```bash
    cd ../web-frontend
    ```

2.  **Install Dependencies**:
    ```bash
    npm install
    ```

3.  **Build for Production**:
    ```bash
    npm run build
    ```

4.  **Test Run**:
    ```bash
    npm start
    ```
    *(Ctrl+C to stop after verifying it starts on port 3000)*

---

## 3️⃣ Production Process Management (PM2)

Use PM2 to keep both services running 24/7.

1.  **Start Backend**:
    ```bash
    cd ../backend
    pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name arun-backend
    ```

2.  **Start Frontend**:
    ```bash
    cd ../web-frontend
    pm2 start "npm start" --name arun-frontend
    ```

3.  **Save List**:
    ```bash
    pm2 save
    pm2 startup
    ```

---

## 4️⃣ Nginx Reverse Proxy (Optional but Recommended)

Serve both apps on a single domain/IP (Frontend on port 80, Backend on `/api`).

1.  **Edit Configuration**:
    ```bash
    sudo nano /etc/nginx/sites-available/default
    ```

2.  **Add Configuration**:
    ```nginx
    server {
        listen 80;
        server_name your_vps_ip_or_domain;

        # Frontend
        location / {
            proxy_pass http://localhost:3000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }

        # Backend API
        location /api {
            proxy_pass http://localhost:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
    }
    ```

3.  **Restart Nginx**:
    ```bash
    sudo systemctl restart nginx
    ```

✅ **Access your bot at:** `http://<your-vps-ip>/`

---

## 🛡️ Security Tips for VPS

1.  **Firewall (`ufw`)**:
    ```bash
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw enable
    ```
2.  **SSH**: Disable password auth and use SSH keys.
