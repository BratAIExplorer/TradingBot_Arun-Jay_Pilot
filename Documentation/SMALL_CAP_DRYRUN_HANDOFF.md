> ⚠️ **SUPERSEDED 2026-09-09.** This original spec is kept for history only. Several
> of its recommendations (paper-only, `trades_db.insert_trade()`,
> `risk_manager.never_sell_at_loss`, mStock, MACD-divergence exit) were changed by
> later decisions. The current design is:
> - **Plan:** `~/.claude/plans/lets-discuss-the-exact-curious-bentley.md`
> - **Design doc:** `Documentation/SMALL_CAP_DRYRUN.html`
> Key changes: reusable framework + own `strategies.db` (zero imports of
> kickstart/risk_manager/trades_db); **Zerodha** dedicated account (not mStock);
> **trailing 2% profit rope + scale-out** exit (not divergence/swing-low);
> **fundamentals gate ON**; real money with a budget (not a 2-week paper experiment).

# Small-Cap Dry-Run Strategy — Build Handoff

**Status:** Spec only, nothing built yet.
**Project:** ARUN Trading Bot (`C:\Antigravity\TradingBot`)
**Owner:** B (non-technical founder — explain any code choices in plain terms when reporting back)

---

## 1. What this is

A new, isolated strategy for ARUN that runs a 2-week dry run (paper trading) on small-cap stocks, with **no stop-loss by design**, to test whether a stop-loss actually improves outcomes vs. not having one. This is a data-collection exercise, not a live-money strategy — yet.

## 2. Hard constraints (read first)

- **Do not modify** `kickstart.py` or `risk_manager.py`'s existing logic. That code runs B's live/real ARUN bot (RSI Mean Reversion strategy). Only add new files/functions, never edit their existing behavior.
- **Do not touch** any `-Copy` folder, zip file, or `TradingBots-Aruns Project` twin. Work only inside `C:\Antigravity\TradingBot` as listed.
- Everything in this build runs in **paper trading mode** (`app_settings.paper_trading_mode: true`, already the default). Do not flip this to live without explicit sign-off.
- Every trade/log this strategy produces must be tagged with a distinct strategy name (e.g. `small_cap_dryrun`) so it never mixes with live ARUN trades in the database.

## 3. Broker reality (verified by reading the code)

- **mStock**: fully wired. `kickstart.py` has a working `place_order()` function hitting mStock's live order API. This is the only broker currently connected.
- **Zerodha**: not integrated anywhere in this codebase. Out of scope for this build unless separately requested.

## 4. What already exists and should be reused

| Component | File | Reuse how |
|---|---|---|
| MACD calculation | `scanner_engine.py` → `calculate_macd()` | Import, don't rewrite |
| MACD bullish crossover detection | `scanner_engine.py` → `detect_macd_crossover()` | Import, don't rewrite |
| 20/50 DMA check | `scanner_engine.py` → `check_moving_averages()` | Import, don't rewrite |
| RSI calculation | `scanner_engine.py` → `get_rsi()` or `getRSI.py` | Import, don't rewrite |
| "No stop-loss" toggle | `risk_manager.py` → `never_sell_at_loss` setting | Set `true` in this strategy's config block only |
| Order execution | `kickstart.py` → `place_order()` | Call it, don't duplicate it |
| Trade logging | `database/trades_db.py` → `insert_trade()` | Reuse, tag with new `strategy` field |

**Note:** `scanner_engine.py`'s `MACDScanner` class currently is NOT wired into the dashboard UI (`dashboard_v2.py`) at all — it only runs standalone. This build needs to actually connect it.

## 5. What's net-new (needs building)

1. **Small-cap filter**: filter the scanner's stock universe to market cap ₹500cr–₹5000cr (use `yf.Ticker(x).info['marketCap']`, not currently used anywhere in the codebase).
2. **`scan_results` DB table**: new table to store every day's scored candidates (ticker, score, signal, timestamp) — separate from the `trades` table, which only logs executed orders. Today, scan output disappears when the scan ends.
3. **Dashboard UI panel**: new tab/section showing the daily ranked list of top 5–10 scored small-cap candidates (currently no UI shows scanner output at all).
4. **Drip-sell (partial exit) logic**: detect RSI or OBV divergence from price. Needs a precise, codeable definition before building — e.g. "price makes a new N-day high while RSI/OBV does not, within X bars." **Confirm exact definition with B before coding.**
5. **Full-exit logic**: confirmed downtrend (2+ consecutive lower-highs/lower-lows) AND close below 50-day MA. Needs a precise swing-point definition (e.g. ZigZag % threshold) — currently undefined, ambiguous as written. **Confirm exact definition with B before coding.**
6. **Re-entry cooldown**: block same-day re-entry after a full exit; require a fresh MACD bullish crossover dated *after* the exit.
7. **Daily logging additions** (beyond what `trades_db.py` already captures):
   - Days each position sits red vs. green
   - Capital tied up in red positions vs. capital free to redeploy
   - Any day a new buy signal fired but no capital was free (blocked by a held red position)
8. **Day-14 comparison script**: replay the same 14 days of logged trades with a hypothetical 8% hard stop-loss applied, compute P&L both ways, output a side-by-side comparison. Uses only logged data — no new market data needed.

## 6. Trading rules (as specified by B)

| Action | Trigger |
|---|---|
| Enter / add tranche | Price above 50-day MA + MACD bullish crossover |
| Drip-sell (partial) | RSI or OBV diverges from price *(needs precise definition — see §5.4)* |
| Full exit | Confirmed downtrend (lower highs/lower lows) + price closes below 50-day MA *(needs precise definition — see §5.5)* |
| Stop-loss | **None** — intentional, this is the whole point of the test |
| Re-entry after full exit | Only on a fresh MACD bullish crossover, not same-day |

## 7. Build order (recommended, lowest risk first)

1. `scan_results` table + small-cap filter (pure data, zero trading risk)
2. Dashboard UI panel showing daily scored list (visibility, zero trading risk)
3. Drip-sell + full-exit + re-entry logic as a new strategy module (paper trading only)
4. Wire strategy module to `place_order()` for paper-mode execution
5. Day-14 comparison script

## 8. Open questions before coding starts

- Exact divergence definition for drip-sell (RSI/OBV, lookback window, threshold)
- Exact lower-high/lower-low definition for full exit (swing detection method)
- Tranche sizing: how much capital per entry, how many tranches per stock, max total allocation to this strategy
- Confirm ₹500cr–₹5000cr market cap band is final (previously discussed, not yet locked in code)
