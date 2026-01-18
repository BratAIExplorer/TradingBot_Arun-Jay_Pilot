# 🔌 mStock API Integration Reference (Type A)

This document provides a technical overview of the **mStock Open API (Type A)** endpoints utilized by the ARUN Trading Bot for market data, order execution, and session management.

---

## 🔐 Authentication & Session
The bot uses a **Dynamic Token Generation** flow with TOTP for automated daily logins.

### 1. Login (Phase 1)
*   **Endpoint**: `POST https://api.mstock.trade/openapi/typea/connect/login`
*   **Payload**: `username`, `password`
*   **Purpose**: Initial handshake to receive a request token.

### 2. Verify TOTP (Auto-Login)
*   **Endpoint**: `POST https://api.mstock.trade/openapi/typea/session/verifytotp`
*   **Payload**: `api_key`, `totp` (6-digit code from `pyotp`)
*   **Purpose**: Validates the 2FA code to proceed with session generation.

### 3. Generate Access Token
*   **Endpoint**: `POST https://api.mstock.trade/openapi/typea/session/token`
*   **Payload**: `api_key`, `request_token`, `checksum` (SHA256)
*   **Purpose**: Retrieves the `access_token` used for all subsequent authenticated requests.

---

## 📊 Market Data
The bot polls live data at intervals defined in the strategy configuration.

### 1. OHLC Quote
*   **Endpoint**: `GET https://api.mstock.trade/openapi/typea/instruments/quote/ohlc`
*   **Params**: `i` (e.g., `NSE:RELIANCE`)
*   **Returns**: Last price, open, high, low, close, and volume.

---

## 💰 Portfolio & Funds
Used for risk management and capital allocation checks.

### 1. Cash Limits
*   **Endpoint**: `GET https://api.mstock.trade/openapi/typea/limits/getCashLimits`
*   **Purpose**: Checks available balance before placing new trades.

### 2. Holdings (Portfolio)
*   **Endpoint**: `GET https://api.mstock.trade/openapi/typea/portfolio/holdings`
*   **Purpose**: Fetches currently held quantities and average prices.

---

## 📉 Order Management
Handles execution, tracking, and the "Panic" cancel logic.

### 1. Place Order
*   **Endpoint**: `POST https://api.mstock.trade/openapi/typea/orders/regular`
*   **Payload**: `tradingsymbol`, `exchange`, `transaction_type`, `order_type`, `quantity`, `product`, `validity`, `price`, `symboltoken`.
*   **Note**: Supports `MARKET` and `LIMIT` orders.

### 2. Fetch Orders (Daily)
*   **Endpoint**: `GET https://api.mstock.trade/openapi/typea/orders`
*   **Purpose**: Refreshes the "Orders" tab in the dashboard.

### 3. Cancel Order
*   **Endpoint**: `POST https://api.mstock.trade/openapi/typea/orders/cancel`
*   **Payload**: `orderId`
*   **Purpose**: Cancels a specific pending order (used in Panic Mode).

---

## 🛠️ Implementation Details
All requests are handled via the `safe_request()` wrapper in `kickstart.py`, which provides:
- **Auto-Retry**: Backoff logic for transient network failures.
- **Auto-Login**: Detects `401/403` errors and triggers the TOTP refresh flow automatically.
- **Offline Mode**: Stops traffic if the broker API is unreachable to prevent logic errors.
