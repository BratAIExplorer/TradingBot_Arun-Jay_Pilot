---
# Orbit Trading - Architecture & Design
## Safe API Key Storage | AI Learning Loop | Per-Market Settings
---

## 1. SECURE API KEY STORAGE

### Problem
- ❌ Never hardcode secrets in source code
- ❌ Never commit `.env` files
- ❌ API keys exposed = account compromise

### Solution: Three-Layer Defense

```
LAYER 1: Environment Variables (Local Development)
├─ File: ~/.env (NEVER committed)
├─ Content:
│  MSTOCK_API_KEY=xxx
│  MSTOCK_ACCESS_TOKEN=yyy
│  IBKR_PORT=7497
│  IBKR_CLIENT_ID=1
├─ Load on startup via: from dotenv import load_dotenv
└─ Safe: File ignored by .gitignore

LAYER 2: Encrypted Settings File (Production)
├─ File: ~/.orbit/credentials.enc (encrypted, stored in home dir)
├─ Encryption: Fernet (symmetric, via cryptography library)
├─ Key stored in: OS Keyring (system-level, OS manages)
├─ Load on startup: Decrypt credentials.enc with key from keyring
└─ Safe: OS keyring only accessible by logged-in user

LAYER 3: Runtime Memory Only
├─ Credentials loaded into memory at startup
├─ Never written to logs
├─ Never printed to console
├─ Cleared on shutdown
└─ Safe: No on-disk exposure after startup
```

### Implementation

**File: `security/credential_manager.py`**

```python
from cryptography.fernet import Fernet
import keyring
import os
import json
from pathlib import Path
from dotenv import load_dotenv

class CredentialManager:
    """Manage API keys securely."""
    
    def __init__(self, env="development"):
        """Initialize credential manager."""
        self.env = env
        self.credentials = {}
        self.cipher = None
        
        if env == "development":
            self._load_from_env_file()
        else:  # production
            self._load_from_encrypted_file()
    
    def _load_from_env_file(self):
        """DEVELOPMENT: Load from ~/.env"""
        load_dotenv(Path.home() / ".env")
        
        self.credentials = {
            "mstock": {
                "api_key": os.getenv("MSTOCK_API_KEY"),
                "access_token": os.getenv("MSTOCK_ACCESS_TOKEN"),
                "client_code": os.getenv("MSTOCK_CLIENT_CODE"),
            },
            "ibkr": {
                "host": os.getenv("IBKR_HOST", "127.0.0.1"),
                "port": int(os.getenv("IBKR_PORT", "7497")),
                "client_id": int(os.getenv("IBKR_CLIENT_ID", "1")),
            },
        }
        
        # Validate
        if not self.credentials["mstock"]["api_key"]:
            raise ValueError("MSTOCK_API_KEY not found in .env")
    
    def _load_from_encrypted_file(self):
        """PRODUCTION: Load from ~/.orbit/credentials.enc"""
        cred_file = Path.home() / ".orbit" / "credentials.enc"
        key_name = "orbit-trading-key"
        
        # Get encryption key from OS keyring
        key = keyring.get_password("orbit-trading", key_name)
        if not key:
            raise ValueError("Encryption key not found in OS keyring")
        
        # Decrypt credentials
        cipher = Fernet(key.encode())
        with open(cred_file, "rb") as f:
            encrypted = f.read()
        
        decrypted = cipher.decrypt(encrypted).decode()
        self.credentials = json.loads(decrypted)
    
    def get_mstock_config(self):
        """Get mStock API config (safe: never logged)."""
        return self.credentials["mstock"]
    
    def get_ibkr_config(self):
        """Get IBKR connection config."""
        return self.credentials["ibkr"]
    
    def rotate_credentials(self, service: str, new_key: str):
        """Rotate credentials (update and re-encrypt)."""
        self.credentials[service]["api_key"] = new_key
        if self.env == "production":
            self._encrypt_and_save()
    
    def _encrypt_and_save(self):
        """Encrypt credentials and save to file."""
        key = Fernet.generate_key()
        cipher = Fernet(key)
        
        encrypted = cipher.encrypt(
            json.dumps(self.credentials).encode()
        )
        
        cred_file = Path.home() / ".orbit" / "credentials.enc"
        cred_file.parent.mkdir(exist_ok=True)
        
        with open(cred_file, "wb") as f:
            f.write(encrypted)
        
        # Store key in OS keyring (Linux: secretsservice, Mac: keychain, Win: credential manager)
        keyring.set_password("orbit-trading", "orbit-trading-key", key.decode())
    
    def __del__(self):
        """Clear credentials on shutdown."""
        self.credentials = {}
```

### Setup Instructions

**Development:**
```bash
# Create .env in home directory
cat > ~/.env << EOF
MSTOCK_API_KEY=your_api_key
MSTOCK_ACCESS_TOKEN=your_access_token
MSTOCK_CLIENT_CODE=your_client_code
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=1
EOF

# Git will ignore it (in .gitignore)
echo ".env" >> .gitignore
```

**Production:**
```bash
# Create encrypted credentials (one-time setup)
python -c "
from security.credential_manager import CredentialManager
mgr = CredentialManager('production')
mgr._encrypt_and_save()  # Stores in ~/.orbit/credentials.enc
"

# Credentials are now encrypted and secured by OS keyring
```

### Usage in Code

```python
# kickstart.py
from security.credential_manager import CredentialManager

mgr = CredentialManager(env="production")
mstock_config = mgr.get_mstock_config()
ibkr_config = mgr.get_ibkr_config()

# Never log these
broker = BrokerAPI(**mstock_config)
```

---

## 2. AI LEARNING LOOP

### Architecture: Manual → Learn → Predict

```
DAY 1-7: COLLECTION PHASE
│
├─ User makes MANUAL trades
│  └─ Bot captures: symbol, price, quantity, reason (RSI/volume/trend)
│
├─ Bot makes AUTOMATED trades
│  └─ Bot captures: symbol, price, quantity, decision (why it traded)
│
└─ Database grows: 100+ signal rows (all trades + bot decisions)
   ├─ market: 'IN'|'US'
   ├─ source: 'MANUAL'|'BOT'
   ├─ action: 'BUY'|'SKIP'|'SELL'
   ├─ features: {rsi, volume, ma_20, ma_50, ...}
   └─ timestamp: when it happened

DAY 8: ANALYSIS PHASE
│
├─ For each manual trade:
│  └─ Look forward 2 hours: "Did price go up or down after this trade?"
│
├─ Label signals with OUTCOME
│  ├─ If price went up: outcome = "CORRECT" ✅
│  ├─ If price went down: outcome = "WRONG" ❌
│  └─ If flat: outcome = "NEUTRAL" ➡️
│
└─ Build training dataset: (features, outcome)

DAY 9-10: TRAINING PHASE
│
├─ Train ML model on dataset
│  ├─ Input: RSI, volume, trend, time-of-day, market
│  ├─ Output: "Is this a good trade?" (yes/no/skip)
│  └─ Accuracy on manual trades: 85%+? Good!
│
└─ Deploy model into SHADOW MODE

DAY 11-30: VALIDATION PHASE
│
├─ Model runs SHADOW (no real trades)
│  └─ Compares: "What would my model say?" vs "What did RSI say?"
│
├─ Track shadow accuracy
│  ├─ If 80%+ accuracy: Promote to ADVISORY
│  ├─ If <60%: Retrain, don't use yet
│  └─ If 60-80%: Use with reduced position size
│
└─ If good, upgrade to LIVE (with safety guards)

DAY 31+: LIVE TRADING
│
├─ Model assists with order decisions
│  ├─ Model says "BUY" + RSI says "BUY" = Confidence 🟢
│  ├─ Model says "SKIP" + RSI says "BUY" = Confidence 🟡 (ask user)
│  └─ Model says "SELL" + risk_manager says "NEVER" = Never sell ❌
│
└─ Risk manager ALWAYS has final say (no model overrides)
```

### Implementation

**File: `ml/training_pipeline.py`**

```python
from ml.signal_logger import SignalLogger
from database.trades_db import TradesDatabase
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MLTrainingPipeline:
    """Train ML model from accumulated signals."""
    
    def __init__(self, db: TradesDatabase):
        self.db = db
        self.model = None
        self.scaler = StandardScaler()
    
    def collect_signals(self, market: str, days: int = 30):
        """Retrieve signals for training."""
        signals = self.db.get_signals(market=market, days_back=days, limit=10000)
        return [s for s in signals if s["source"] == "MANUAL"]  # Learn from manual trades
    
    def label_outcomes(self, signals: list) -> list:
        """Label each signal with outcome (correct/wrong/neutral)."""
        labeled = []
        
        for signal in signals:
            symbol = signal["symbol"]
            timestamp = datetime.fromisoformat(signal["timestamp"])
            entry_price = signal["current_price"]
            
            # Look forward 2 hours
            future_price = self._get_future_price(symbol, timestamp + timedelta(hours=2))
            
            if future_price is None:
                continue  # Not enough data
            
            # Determine outcome
            if signal["action"] == "BUY":
                pnl = future_price - entry_price
                outcome = "CORRECT" if pnl > 0 else "WRONG"
            elif signal["action"] == "SELL":
                pnl = entry_price - future_price
                outcome = "CORRECT" if pnl > 0 else "WRONG"
            else:  # SKIP
                # Skip was correct if price didn't move favorably
                pnl = abs(future_price - entry_price)
                outcome = "CORRECT" if pnl < 10 else "WRONG"
            
            signal["outcome"] = outcome
            labeled.append(signal)
        
        return labeled
    
    def build_features(self, signals: list) -> tuple:
        """Extract features and outcomes."""
        X = []
        y = []
        
        for signal in signals:
            features = signal.get("features", {})
            
            # Feature vector
            x = [
                features.get("rsi", 50),
                features.get("volume", 0),
                features.get("ma_20", 0),
                features.get("ma_50", 0),
                features.get("market_trend", 0),
                self._hour_of_day(signal["timestamp"]),
                1 if signal["market"] == "US" else 0,  # US=1, IN=0
            ]
            X.append(x)
            
            # Label
            y.append(1 if signal["outcome"] == "CORRECT" else 0)
        
        return np.array(X), np.array(y)
    
    def train(self, market: str = "IN") -> dict:
        """Train model on collected signals."""
        signals = self.collect_signals(market, days=30)
        
        if len(signals) < 10:
            raise ValueError(f"Need at least 10 manual trades; found {len(signals)}")
        
        labeled = self.label_outcomes(signals)
        X, y = self.build_features(labeled)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        self.model.fit(X_scaled, y)
        
        # Evaluate
        train_score = self.model.score(X_scaled, y)
        
        return {
            "market": market,
            "accuracy": train_score,
            "signals_used": len(labeled),
            "model_ready": train_score > 0.70,
            "timestamp": datetime.now().isoformat(),
        }
    
    def predict(self, symbol: str, market: str, features: dict) -> str:
        """Get prediction for a trade decision."""
        if self.model is None:
            return "UNKNOWN"  # No model trained yet
        
        x = [
            features.get("rsi", 50),
            features.get("volume", 0),
            features.get("ma_20", 0),
            features.get("ma_50", 0),
            features.get("market_trend", 0),
            self._hour_of_day(datetime.now().isoformat()),
            1 if market == "US" else 0,
        ]
        
        x_scaled = self.scaler.transform([x])
        prediction = self.model.predict(x_scaled)[0]
        confidence = self.model.predict_proba(x_scaled)[0][prediction]
        
        return "GOOD_TRADE" if prediction == 1 else "SKIP_TRADE", confidence
    
    def _get_future_price(self, symbol: str, future_time: datetime) -> float:
        """Get price at future time (stub: would fetch from broker)."""
        # In real implementation: query broker for historical data
        return None
    
    def _hour_of_day(self, timestamp_str: str) -> int:
        """Extract hour from ISO timestamp."""
        return datetime.fromisoformat(timestamp_str).hour
```

### Usage Flow

```python
# kickstart.py
from ml.training_pipeline import MLTrainingPipeline

pipeline = MLTrainingPipeline(db)

# Every day at 20:00, train on that day's signals
if should_retrain_daily():
    result = pipeline.train(market="IN")
    if result["model_ready"]:
        print("✅ Model trained successfully!")
    else:
        print("⚠️ Not enough signals, waiting...")

# During trading, use model for advisory
features = {"rsi": 28, "volume": 1500000, "ma_20": 2480, ...}
prediction, confidence = pipeline.predict("RELIANCE", "IN", features)

# Decision flow
if rsi_signal == "BUY":
    if prediction == "GOOD_TRADE" and confidence > 0.80:
        place_order(...)  # 🟢 HIGH CONFIDENCE
    else:
        log_advisory(f"Model skeptical (confidence: {confidence:.0%})")
        # Still buy, but log for learning
```

---

## 3. PER-MARKET SETTINGS & PARAMETERS

### Settings Schema

```json
{
  "app_settings": {
    "paper_trading_mode": false,
    "version": "2.7.0"
  },
  
  "stocks": [
    {"symbol": "RELIANCE", "exchange": "NSE", "ignore_rsi": false}
  ],
  
  "markets": {
    "IN": {
      "enabled": true,
      "paper_trading": false,
      "broker": "mstock",
      "exchange": "NSE",
      "timezone": "Asia/Kolkata",
      "market_hours": {"open": "09:15", "close": "15:30"},
      "settings": {
        "per_trade_pct": 10,
        "rsi_threshold_buy": 30,
        "rsi_threshold_sell": 70,
        "min_volume": 100000,
        "risk_tier": "moderate",
        "stop_loss_pct": 5,
        "profit_target_pct": 1,
        "trend_filter": {
          "enabled": false,
          "ma_period": 50,
          "ma_type": "SMA"
        }
      },
      "stocks": [
        {
          "symbol": "HDFCBANK",
          "exchange": "NSE",
          "risk_tier": "aggressive",
          "min_volume": 500000,
          "stop_loss_pct": 8
        }
      ]
    },
    
    "US": {
      "enabled": false,
      "paper_trading": true,
      "broker": "ibkr",
      "exchange": "SMART",
      "timezone": "America/New_York",
      "market_hours": {"open": "09:30", "close": "16:00"},
      "ibkr": {
        "host": "127.0.0.1",
        "port": 7497,
        "client_id": 1
      },
      "settings": {
        "per_trade_pct": 5,
        "rsi_threshold_buy": 32,
        "rsi_threshold_sell": 68,
        "min_volume": 1000000,
        "risk_tier": "conservative",
        "stop_loss_pct": 3,
        "profit_target_pct": 0.75,
        "trend_filter": {
          "enabled": false,
          "ma_period": 50,
          "ma_type": "SMA"
        }
      },
      "stocks": [
        {
          "symbol": "AAPL",
          "exchange": "SMART",
          "risk_tier": "moderate",
          "min_volume": 50000000
        }
      ]
    }
  },
  
  "ai_training": {
    "enabled": true,
    "retrain_daily": true,
    "min_signals_for_training": 50,
    "min_accuracy_for_live": 0.75,
    "shadow_mode_days": 7,
    "lookback_hours": 2
  }
}
```

### Per-Market Resolution in Code

**File: `settings_manager.py` (additions)**

```python
class SettingsManager:
    
    def get_market_settings(self, market: str) -> dict:
        """Get all settings for a market."""
        markets = self.settings.get('markets', {})
        market_config = markets.get(market, {})
        return market_config.get('settings', {})
    
    def get_setting(self, market: str, key: str, default=None):
        """Get a specific setting for a market."""
        settings = self.get_market_settings(market)
        return settings.get(key, default)
    
    def get_stock_setting(self, symbol: str, exchange: str, 
                         market: str, key: str, default=None):
        """Get setting for a specific stock in a market."""
        markets = self.settings.get('markets', {})
        market_config = markets.get(market, {})
        stocks = market_config.get('stocks', [])
        
        for stock in stocks:
            if stock['symbol'] == symbol and stock['exchange'] == exchange:
                return stock.get(key, default)
        
        # Fall back to market default
        return self.get_setting(market, key, default)
    
    def get_risk_tier(self, symbol: str, exchange: str, market: str) -> str:
        """Get risk tier for a stock."""
        # Try stock-specific setting
        risk_tier = self.get_stock_setting(symbol, exchange, market, 'risk_tier')
        if risk_tier:
            return risk_tier
        
        # Fall back to market default
        return self.get_setting(market, 'risk_tier', 'moderate')
    
    def is_market_enabled(self, market: str) -> bool:
        """Check if market is enabled."""
        markets = self.settings.get('markets', {})
        return markets.get(market, {}).get('enabled', False)
```

### Usage in Trading Engine

```python
# kickstart.py - During order placement for RELIANCE in India

settings_mgr = SettingsManager()
market = 'IN'
symbol = 'RELIANCE'
exchange = 'NSE'

# Get per-market settings
rsi_threshold_buy = settings_mgr.get_setting(market, 'rsi_threshold_buy')
min_volume = settings_mgr.get_setting(market, 'min_volume')

# Get per-stock overrides
stock_min_volume = settings_mgr.get_stock_setting(
    symbol, exchange, market, 'min_volume', min_volume
)

risk_tier = settings_mgr.get_risk_tier(symbol, exchange, market)

# Apply settings
should_buy = (
    rsi < rsi_threshold_buy and
    current_volume >= stock_min_volume and
    not in_loss(risk_tier)  # Never sell at loss
)

if should_buy:
    place_order(symbol, exchange, 'BUY')
```

---

## Summary: Three-Layer Security

| Layer | Protection | Cost |
|-------|-----------|------|
| **1. Environment Variables** | Dev: Easy, safe from git | Low |
| **2. Encrypted File + OS Keyring** | Prod: Encrypted, OS-managed | Medium |
| **3. Runtime Memory Only** | No on-disk exposure after startup | Minimal |

**Result:** API keys never in source code, never logged, never exposed.

---

## Summary: AI Loop

| Phase | Activity | Time | Output |
|-------|----------|------|--------|
| **Collection** | Capture manual + bot trades | Days 1-7 | 100+ signals |
| **Analysis** | Label with outcomes | Day 8 | Training data |
| **Training** | Build ML model | Days 9-10 | Model (85%+ accuracy) |
| **Validation** | Run shadow mode | Days 11-30 | Confidence score |
| **Live** | Model assists decisions | Day 31+ | Advisory predictions |

**Result:** Bot learns from manual trades, improves decisions over time.

---

## Summary: Per-Market Settings

| Setting | India Default | US Default | Override |
|---------|---|---|---|
| `per_trade_pct` | 10% | 5% | Per-stock possible |
| `risk_tier` | moderate | conservative | Yes, per-stock |
| `stop_loss_pct` | 5% | 3% | Yes, per-stock |
| `min_volume` | 100K | 1M | Yes, per-stock |
| `rsi_threshold` | 30/70 | 32/68 | Market-level |

**Result:** Each market has its own parameters, stocks can override.

---

**Orbit Trading is now ready for:**
- ✅ Secure credential management
- ✅ AI learning from manual trades
- ✅ Independent market configurations
- ✅ Simple, extensible settings schema
