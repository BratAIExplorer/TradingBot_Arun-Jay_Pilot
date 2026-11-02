# Spike Shadow Test — frozen rules

**Written 2026-10-31, before any data. Do not edit after logging starts** (add a dated amendment at the bottom instead).
**What it is:** a log-only test of "buy US micro-cap spikes, sell the same day". No orders, ever.
**Code:** `research/spike_logger.py` (collects) · `research/spike_scorer.py` (scores) · `tests/test_spike.py` · `deploy/voyager-spike-logger.service`

## Data gate (hard)
Logged only if SPY's quote type is **real-time (1)**. Otherwise the logger writes `gate_fail` rows and logs nothing else.
**The 3-week clock starts on the first day with no `gate_fail`.** `get_quote()` in `brokers/ibkr_broker.py` says this account had *no* real-time subscription — check.

## Rules
| | |
|---|---|
| Scan | IBKR `TOP_PERC_GAIN`, US, price $1–20, 04:00–15:55 ET (premarket included) |
| Triggers | day gain crosses **+30% / +50% / +100%**; all three scored separately, none picked afterwards |
| Entry (simulated) | the ask at the flag moment **+ slippage** |
| Slippage | **2%** and **5%** per side; the verdict uses 5% |
| Exit | bid ≤ entry −10% (fills at the real bid, so gaps through the stop are counted) or forced at 15:55 ET. No overnight. |
| Halts | cannot sell into a halted tick; counted as `halt_trapped` |
| Size | $500 per trade, commission $1/side (**IBKR tiers not verified**) — a $5K account at 1% risk |
| Unit of evidence | **stock-days**, not trades (one stock flagged at 3 levels = 1) |

## Verdict (`python -m research.spike_scorer spike_log.csv`)
- `no conclusion` until **≥100 stock-days across ≥10 distinct days** (judgement, not a standard).
- `continue paper` needs, at 5% slippage: median net trade > 0, **and** median > 0 with the top-2 winners removed, **and** halt-trapped ≤ 10%.
- Otherwise `retire or re-tune within budget`.
- **Passing never means go live.** It means keep paper-trading.

## Re-tune rule (agreed direction: re-tune allowed, not unlimited — **confirm**)
- ≤ 5 variants per thesis, each logged and counted (deflated Sharpe).
- Tune on early data; the **last 7 trading days stay locked** until the final verdict.
- New ideas are unlimited; the cap is on re-tuning the same one.

## Known limits
- Free of paper-fill optimism, but quotes are not tick-by-tick (5 s polling); fast spikes can be missed.
- IBKR quote lines: capped at 40 here; default account limit believed ~100 (verify).
- Holidays are not modelled (no ticks arrive, so no rows).
- 3 weeks is one market mood; spikes cluster in waves.
- Capacity is tiny: micro-caps cannot absorb size.

## Amendment 2026-11-02 (implementation fix, no rule change; logging had not started)
- The data gate is now "marketDataType 1 **and** a valid SPY last price" — ib_insync defaults the type to 1, so the old check passed when the real-time request failed (IBKR error 10089). Same intent as the rule above.
- Scanner is a 30 s snapshot instead of a long-lived subscription (it died silently on an IBKR reconnect). Same query: TOP_PERC_GAIN, STK.US.MAJOR, $1–20.
- The logger also writes an `hb` heartbeat row every 10 min; the scorer ignores it.
- Clock start (2026-11-02, after the real-time feeds were bought): **Day 1 = 2026-11-03.** 2026-11-02 rows are excluded from scoring (gate_fail earlier that day; logger started mid-session so its `event` rows are stale entries). Score with: `grep -v '^2026-11-02' spike_log.csv > scored.csv && python -m research.spike_scorer scored.csv`.
- Known limitation: if the logger is down when a stock really crosses a level, the `event` is logged late (at the first poll after reconnect) with a later, higher ask. Keep downtime low (watch the Telegram alerts).
