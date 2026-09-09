# `small_cap_dryrun.json` — field guide

One file, every rule the bot follows. Change a number, restart the bot. No code.
Nothing here places an order until `orders_enabled` is `true` **and** the Zerodha
keys are in `strategies/.env` (last step).

| Key | What it is | What to put | Safe default |
|---|---|---|---|
| `enabled` | master on/off for this strategy | `true` / `false` | `true` |
| `orders_enabled` | **the live-money switch.** `false` = log-only, nothing is bought or sold | keep `false` until every check is done | `false` |
| `broker.account_label` | a name for the Zerodha account this strategy uses | your label, e.g. `ARUN_SMALLCAP` | — |
| **`budget.per_stock_amount`** | rupees for one full position | `10000` | `10000` |
| **`budget.total_budget`** | **the hard rupee cap. The bot will never have more than this in the market.** | `30000` | `30000` |
| `budget.max_names_cap` | never hold more than this many stocks, whatever the budget allows | `10` | `10` |
| `budget.pct_of_account_cap` | extra ceiling as % of the whole account; set high (`100`) to let `total_budget` be the only cap | `100` | `100` |
| `entry.fresh_cross_max_age_days` | the buy signal must be this many trading days old or newer | `1` | `1` |
| `entry.require_200ema_uptrend` | require price > 200-EMA **and** 50-EMA > 200-EMA | `true` | `true` |
| `fundamentals_gate.enabled` | only buy companies that pass the health check | `true` | `true` |
| `fundamentals_gate.min_roe` | minimum return on equity, % | `10` | `10` |
| `fundamentals_gate.max_debt_equity` | maximum debt-to-equity ratio | `1.0` | `1.0` |
| `fundamentals_gate.require_positive_earnings` | company must be profitable | `true` | `true` |
| `fundamentals_gate.min_market_cap_cr` / `max_market_cap_cr` | company-size band, ₹ crore | `500` / `5000` | `500` / `5000` |
| `liquidity_gate.min_avg_daily_value_cr` | skip stocks trading less than this per day, ₹ crore (thin stocks can't be exited) | `1.0` | `1.0` |
| `exit.trail_giveback_pct` | the safety line sits this % below the best price since buying | `2.0` | `2.0` |
| `exit.min_profit_floor_pct` | never sell a piece for less than this % above cost, after charges | `2.0` | `2.0` |
| `exit.scale_out_step_pct` | the second half sells this % below the safety line | `3.0` | `3.0` |
| `exit.hard_stop_pct` | a real stop-loss. `null` = OFF (the whole point of this run) | `null` | `null` |
| `exit.never_sell_at_loss` | refuse any sale below the +profit floor | `true` | `true` |
| `exit.strand_final_half` | `true` = hold a stuck final half (you sell it in Zerodha); `false` = bot sells it anyway | `true` | `true` |
| `costs.stt_pct` | securities transaction tax, % of turnover, both legs | `0.1` | `0.1` |
| `costs.entry_slippage_bps` | how much worse a buy fills, basis points | `40` | `40` |
| `costs.exit_slippage_bps_thin` | how much worse a sell fills on a thin book, basis points | `300` | `300` |
| `costs.fill_assumption` | `"realistic"` uses the numbers above; `"best"` ignores them | `"realistic"` | `"realistic"` |
| `rules.circuit_band_pct` | assumed daily price limit; a stock locked at/below this is treated as frozen (no sell that day) | `10` | `10` |
| `universe` | which stock list to scan | `curated_smallcap` | `curated_smallcap` |
| `replay_stop_levels_pct` | stop-loss levels for the day-14 "what if" report only | `[5, 8, 10]` | `[5, 8, 10]` |

**Worked example — your case:** account ₹100,000, want the bot to use at most
₹30,000. Set `per_stock_amount: 10000`, `total_budget: 30000`,
`pct_of_account_cap: 100`. Result: `max_names = 30000 / 10000 = 3`. The bot buys
at most 3 stocks × ₹10,000 and `plan_entry()` refuses any buy that would push the
deployed total past ₹30,000 — verified in `strategies/tests/test_sizing.py`.

If `total_budget / per_stock_amount` works out to 0, the loader raises an error
on startup rather than silently buying nothing.
