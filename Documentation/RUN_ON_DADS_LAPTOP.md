# Running the Small-Cap Bot on Dad's Laptop

Branch: `feat/small-cap-strategy` ·
Repo: `https://github.com/BratAIExplorer/TradingBot_Arun-Jay_Pilot`

> **Status:** the strategy framework is built and tested (79 pytest). The bot
> **cannot place orders yet** — `broker.py` / `runner.py` / the dashboard are not
> built (blocked on the four Step-0 decisions below). These steps set the laptop
> up so it's ready the moment those land, and let Dad run the offline scan/tests.

---

## 1. What Dad's laptop needs (one-time)

| Requirement | Notes |
|---|---|
| **Windows 10/11** | same as your machine |
| **Python 3.11** | https://www.python.org/downloads/ — tick *"Add python.exe to PATH"* during install |
| **Git** | https://git-scm.com/download/win — accept defaults |
| **A Zerodha account** | one of your two, dedicated to this strategy. Dad logs in each morning (one tap+paste). |
| **A Kite Connect app** | https://developers.kite.trade — created on the **free Personal plan** (order placement works; no paid tier). Gives an **API key** + **API secret**. |
| **Internet** | for the daily scan and order placement |

Nothing else. No database to copy, no server, no cloud account.

---

## 2. Get the code

Open **Command Prompt** and run:

```bat
cd %USERPROFILE%
git clone -b feat/small-cap-strategy https://github.com/BratAIExplorer/TradingBot_Arun-Jay_Pilot.git TradingBot
cd TradingBot
python -m pip install -r requirements.txt
```

To get later updates from you:

```bat
cd %USERPROFILE%\TradingBot
git pull
```

---

## 3. Secrets — created fresh on Dad's laptop, never copied, never committed

Create a file `strategies\.env` (Notepad, "Save as", filename in quotes: `".env"`):

```
ZERODHA_API_KEY=xxxxxxxxxxxxxxxx
ZERODHA_API_SECRET=xxxxxxxxxxxxxxxx
ZERODHA_ACCOUNT_LABEL=ARUN_SMALLCAP
```

- Values come from the Kite Connect app (step 1).
- `.gitignore` already blocks `strategies/.env`, `strategies/zerodha_token.json`,
  `*.db`, `status.txt`, `logs/` — secrets and the database can never be pushed.
- **The API secret never leaves this laptop. Do not email it, do not paste it in chat.**

### How the daily login is stored (once `broker.py` exists)

1. Dad runs `LAUNCH_SMALLCAP.bat`.
2. The bot checks the saved token. If it's dead, it prints an **"Authorize" link**.
3. Dad opens the link → logs in to Zerodha → the browser jumps to a redirect URL.
4. Dad copies that whole URL, pastes it back into the bot window, presses Enter.
5. The bot writes `strategies\zerodha_token.json` (`access_token`, timestamp).
   Valid until ~6 am next day, survives restarts. **One tap+paste per trading day.**

No password or 2FA code is ever stored — only the day's access token.

---

## 4. What Dad can do *today* (offline, safe)

From `%USERPROFILE%\TradingBot`:

```bat
python -m pytest strategies\tests -q
```
Expect: `79 passed`. Confirms the install is good.

The live scan, order placement, and dashboard need `broker.py` + `runner.py`
(not built yet).

---

## 5. Still to build before the first real run

| # | Item | Blocked on |
|---|---|---|
| 0 | **Name the Zerodha account** in config | your decision — which of the two |
| 0 | **Kite API key + secret** into `strategies\.env` | you create the app / hand over keys |
| 0 | **`per_stock_amount` + `total_budget`** for run 1 (e.g. ₹10,000 × 3 = ₹30,000) | your decision |
| 0 | **First `strategies\configs\fundamentals.csv`** | quarterly human export (screener.in) or one run of `python -m strategies.framework.fundamentals` |
| 4 | `framework/broker.py` — Zerodha orders + cost model + `orders_enabled` log-only flag | Step-0 above |
| 5 | `framework/runner.py` + `LAUNCH_SMALLCAP.bat` + `status.txt`; wire the fundamentals + liquidity gates | step 4 |
| 6 | `backend/strategy_routes.py` + `backend/static/strategy.html` (the dad page — mock is `SMALL_CAP_DASHBOARD_MOCK.html`) | step 5 |
| 8 | `strategies/small_cap_compare.py` — day-14 stop-loss diagnostic | logged data |

### Must-fix before `orders_enabled=true` (from the LEAD review)

1. **Wire the liquidity gate** — `min_avg_daily_value_cr` is loaded but enforced
   nowhere; thin small-caps give bad fills and can't be exited.
2. **Net-of-cost floor** — the +2% floor is gross until `broker.py`'s cost model
   lands; a "winner" can be a net loss after STT + slippage.
3. **Circuit / limit-down awareness** — when a small-cap is locked lower-circuit
   there is no bid; the runner must show "can't sell — stock frozen", not a
   phantom fill.

---

## 6. Daily routine for Dad (once live)

1. Morning: double-click `LAUNCH_SMALLCAP.bat`, do the one tap+paste login.
2. Open `http://localhost:8000/strategy` — read the top line. If it says
   "1 needs you to look", read that card.
3. Only manual action ever asked of him: a **"stranded half — sell it yourself"**
   banner (rare). Everything else is automatic.
4. Big red **STOP** button on the page halts the bot and cancels pending orders.
