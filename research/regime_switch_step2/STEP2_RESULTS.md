# Step 2 - Would a market-health on/off switch have cut the bots' losses?

Run date: 2026-10-31. Read-only. Nothing in the bot was touched. Files are new, inside `research/regime_switch_step2/`.

## Data used (as approved by owner)
`full_trade_export.csv`: 52 rows, 2026-01-21 to 2026-02-16 (about 4 weeks), broker mStock plus a few PAPER rows.
Only 11 real closed trades have a P&L after removing PAPER rows and exact duplicate SELL rows.
Many SELL rows (Feb 13/16 liquidation) have no P&L, so they cannot be scored.

## Method (my assumptions, not the bot's code)
- Index: Nifty 50 (^NSEI) daily close from Yahoo.
- Regime: UP = close > 20-day avg > 50-day avg. DOWN = close < 50-day avg. Otherwise CAUTION.
- Each SELL with P&L is matched to the latest earlier BUY of the same symbol and exchange. The regime on that BUY date decides whether the switch would have blocked it (DOWN = blocked).

## Result
| Entry regime | Trades | Net P&L (INR) |
|---|---|---|
| DOWN | 11 | -336.77 |
| UP / CAUTION | 0 | 0 |

- All 11 trades were entered while Nifty was in DOWN. 16 of the 20 trading days in the window were DOWN, 4 were CAUTION, 0 were UP.
- A switch would have blocked all 11 trades and avoided -336.77. That is NOT evidence the switch works. With one regime and no UP trades there is nothing to compare against.
- One trade (ITBEES, -345.95) is more than the whole net loss. The other 10 trades together are +9.18.

## Verdict: INCONCLUSIVE - cannot test with this data
- 4 weeks, one market regime, 11 trades. Too small and too one-sided.
- Per the rule "no data = stop and escalate", I am not drawing a conclusion.

## Checked vs assumed
- Checked: script ran on the real file; PAPER and duplicate rows removed; regime computed on real Nifty data.
- Assumed: the simple regime rule above; the BUY-to-SELL matching (the export's entry_timestamp column is empty, so I could not use it).
- Not checked: whether the 13 Feb liquidation SELLs without P&L were losses; the live database (not in this repo copy).

## What is needed to get a real answer
Trade history covering at least one UP period and a DOWN period, ideally 6-12+ months and 100+ closed trades. Candidates (not read yet): `TradeHistory_04Dec25_to_05Mar26_MA8224736.xlsx` (about 3 months, still short), `mstock_statement.csv`, and the live trades database on the VPS.

Reproduce: `cd research/regime_switch_step2 && python3 run_step2.py`
