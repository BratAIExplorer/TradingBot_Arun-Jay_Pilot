# Next-day follow-up test — frozen rules

**Written 2026-11-11, before looking at any next-day result. Do not edit after the first scoring run** (add a dated amendment at the bottom).
**Question:** after a micro-cap flagged by the spike logger, does buying near that day's close and selling on a later close make money net of costs?
**What it is:** log-only, no orders, ever. Separate from the same-day test (`SPIKE_TEST_RULES.md`), which stays unchanged and keeps its locked last 7 days.
**Code:** `research/spike_nextday.py` · `tests/test_spike_nextday.py`. Input: `spike_log.csv` event rows (already collected, nothing new on the VPS).

## Stock-days
One stock-day = one (US trading day, symbol) that has at least one `event` row (+30% or more). Days before 2026-11-03 are excluded.

## Entry and exits (simulated)
| | |
|---|---|
| Entry | that day's **official close** (daily bar from yfinance) **+ slippage** |
| Exit | the **close** 1, 2 and 3 trading days later, **minus slippage**. **T+1 is the verdict horizon**; T+2 and T+3 are reported only |
| Slippage | 2% and 5% per side; the verdict uses 5% |
| Size / commission | $500 per trade, $1 per side (same as the same-day test, IBKR tiers not verified) |
| Stops | none. Overnight gap risk is **reported** (share of cases opening 10% or more below the entry close), not modelled away |
| No next-day data | the trade is **unresolved** and counted at -50% (same stand-in as the same-day test). Days less than 5 calendar days old are `pending`, not scored yet |

## Variants (exactly three, fixed now)
- **ALL**: every stock-day.
- **HOLD**: the stock closed still up 30% or more on the day (it kept its gain).
- **STRONG**: the close is within 10% of that day's high (it finished near the top).
All three are scored and reported; none is picked afterwards. Re-tuning needs a dated amendment and counts against a 5-variant cap per thesis.

## Verdict (same shape as the same-day test)
- `no conclusion` until **≥100 stock-days across ≥10 distinct days** with a next-day result.
- `continue paper` needs, at 5% slippage, for the T+1 horizon: median net > 0, **and** median > 0 with the top-2 winners removed, **and** the same two medians > 0 with unresolved trades counted at -50%, **and** unresolved share ≤ 10%.
- Otherwise `retire or re-tune within budget`.
- **Passing never means go live.** It means keep paper-trading.

## Known limits
- Daily bars are end-of-day data from yfinance (free, may have gaps for halted or delisted micro-caps; those show up as unresolved).
- Close entry is a proxy: a real buy near the close pays the real ask, not the official close. The 5% slippage case is meant to cover that.
- The flagged stocks are chosen by the spike scanner (price $1 to $20, top percent gainers), so results do not apply to other stocks.
- Few weeks of data is one market mood. Spikes cluster in waves.
- Run it only after the 3-week review date (2026-11-23) or when ≥10 days exist, never to re-tune the same-day test.
