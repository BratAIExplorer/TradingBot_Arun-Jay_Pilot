# ARUN Trading Bot — TODO List
**Last Updated:** May 21, 2026

---

## 🔴 HIGH PRIORITY

### [ ] Integrate US Market Module (andy-12-08/autonomous_trading_agent)
**Source:** `C:/Antigravity/trading-repos/autonomous_trading_agent/`
**Why here:** Titan already handles India (NSE via mStock). This adds US (NYSE/NASDAQ via Alpaca).
Together they make ARUN a truly multi-market autonomous trading system.

**What it brings:**
- Full day-trading loop for US stocks (NYSE + NASDAQ)
- Claude AI decision engine (same model powering Fortress Intelligence)
- 7-dimensional signal scorer: Trend, Momentum, Volume, ATR, RSI, Multi-TF, Structural
- 7 hard risk gates before every order (earnings blackout, revenge-trade guard, sector limits, GFV checks)
- Conviction-weighted position sizing (30% / 50% / 60% of daily capital)
- ATR-based stops that OVERRIDE Claude's own judgment (safety first)
- 180-day weekly backtester built in — auto-runs every Sunday 8 AM
- Self-managing scheduler — no manual restarts needed

**Hard caps (configurable):**
- Max daily capital: $4,000 (on $10K account)
- Max risk per trade: $100
- Max concurrent positions: 4
- Daily drawdown limit: $200 (2%)
- Max trades/day: 10

**Integration steps:**
1. [ ] Open Alpaca paper trading account (free) → alpaca.markets
2. [ ] Add to `.env`: `ALPACA_KEY`, `ALPACA_SECRET`, `ANTHROPIC_API_KEY`
3. [ ] Paper trade for 30 days minimum — DO NOT go live before this
4. [ ] Track: win rate (target >45%), expectancy (target >0.3R), max drawdown (<8%)
5. [ ] After validation, evaluate running alongside Titan as "ARUN US Module"
6. [ ] Consider shared risk dashboard showing both India + US P&L in one view

**Key risks to discuss before starting:**
- US stocks only — no NSE/BSE access via Alpaca
- Pattern Day Trader (PDT) rule: need $25K+ to trade freely
- Claude API costs ~$2–5/day (manageable)
- Tax/FEMA compliance for Indian resident trading US stocks
- Must paper trade first — no exceptions
- Full risk discussion documented in: `C:/Antigravity/Fortress/TRADING_INTEGRATION_PLAN.md`

---

## 🟡 MEDIUM PRIORITY

### [ ] Install Trading Skills into Arun's Claude Code Context
The 30 trading skills installed for Fortress Intelligence are global (`~/.claude/skills/`)
and are therefore already available here too. Use them to enhance bot development:

**Directly useful for Titan/ARUN:**
- `/nse-trading-toolkit SYMBOL` — Full NSE analysis to validate bot signals manually
- `/rsi-divergence SYMBOL` — Cross-check bot's RSI readings
- `/multi-timeframe-analysis SYMBOL` — 3-screen confluence check
- `/invest-stock-eval SYMBOL` — Piotroski quality check on bot candidates
- `/position-sizing` — Validate bot's sizing calculations
- `/risk-reward-ratio` — Sanity check before any trade

### [ ] Review scanner_engine.py Against andy-12-08 Signal Scorer
Titan's `scanner_engine.py` and the US agent's `analysis/signal_scorer.py` use
overlapping logic (RSI, MACD, ATR, EMA). Worth comparing:
- Can Titan's India scanner adopt the 7-dimension scoring system?
- Unified 0–10 conviction score across both India + US would enable cross-market comparison
- See: `C:/Antigravity/trading-repos/autonomous_trading_agent/analysis/signal_scorer.py`

### [ ] Shared Risk Dashboard
Titan has a working dashboard (Titan V2 Dashboard). Consider adding:
- US module P&L panel (from Alpaca paper/live account)
- Combined daily drawdown across both markets
- Cross-market exposure view (total capital at risk India + US)

---

## 🟢 BACKLOG / FUTURE

### [ ] Evaluate tradermonty/claude-trading-skills for Titan
40+ Claude Code skills for CANSLIM, VCP, market breadth, macro regime detection.
Some of these can enhance Titan's stock universe selection for India.
Source: `C:/Antigravity/trading-repos/` (to be cloned)

### [ ] NSE-Specific Claude Skills Already Installed
9 NSE trading skills are live and ready:
- `nse-trading-toolkit`, `rsi-divergence`, `multi-timeframe-analysis`
- `fibonacci-trading`, `position-sizing`, `stop-loss-strategies`
- `trailing-stops`, `risk-reward-ratio`, `nse-technical-analysis`
Use these as a manual validation layer on top of Titan's automated signals.

### [ ] Connect ARUN to FinFlow (Phase 3 as per existing roadmap)
Per existing PROJECT.md: Optional read-only bridge to FinFlow Wealth Hub.
Shows bot trading performance alongside insurance, loans, bank accounts.
Status: Planned (existing roadmap item)

---

## ✅ DONE

- [x] Autonomous trading agent repo cloned → `C:/Antigravity/trading-repos/autonomous_trading_agent/`
- [x] 30 trading skills installed globally → `~/.claude/skills/`
- [x] Full risk/benefit analysis documented → `C:/Antigravity/Fortress/TRADING_INTEGRATION_PLAN.md`
- [x] Decision made: US agent belongs in ARUN project, NOT Fortress Intelligence ✅

---

## 📁 KEY REFERENCES
| File | Purpose |
|------|---------|
| `C:/Antigravity/trading-repos/autonomous_trading_agent/` | US trading agent source code |
| `C:/Antigravity/trading-repos/autonomous_trading_agent/config.py` | All risk parameters |
| `C:/Antigravity/trading-repos/autonomous_trading_agent/analysis/signal_scorer.py` | 7-dimension signal scoring |
| `C:/Antigravity/Fortress/TRADING_INTEGRATION_PLAN.md` | Full risk/benefit analysis |
| `C:/Antigravity/TradingBots-Aruns Project/PROJECT.md` | Titan project overview |
| `C:/Antigravity/Arun Samant - F&O 1/README.md` | F&O bot overview |
