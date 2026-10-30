# Step 1 - "Top 8 by HQM score, weekly" vs buy-and-hold index

Run date: 2026-10-30. Nothing in the existing bot was touched (all files are new, inside `research/momentum_step1/`).

## What was tested
- Rules copied from the momentum_trader README, no tuning: score = average percentile of 1M/3M/6M/1Y returns, drop anyone below the 25th percentile in any period, top 8, equal weight, weekly.
- Signal on the last trading day of the week, **fill at the next day's open** (no same-day fill). Cost 0.10% per side.
- Variant A = rules as published. Variant B = same, but skip the latest month (3M/6M/1Y only). B was chosen AFTER the idea came up, not tuned on results, but it is one extra try - treat it with suspicion.
- US: today's S&P 500 (503 names, all had data) vs QQQ. India: the 99 symbols in the repo's `nifty500.csv` (92 had data) vs ^NSEI.
- Data: Yahoo (yfinance), adjusted prices, 2015-06 to 2026-10. Measured period starts 2016-07.

## Gate (set before running)
After costs, must beat the index on BOTH return and max drawdown in at least 3 of 5 non-overlapping 2-year slices.

## Results
| Market | Variant | CAGR strat / index | MaxDD strat / index | Sharpe strat / index | Slices beating on return | on drawdown | on both |
|---|---|---|---|---|---|---|---|
| US | A | 30.9% / 21.0% | -39.6% / -36.7% | 0.96 / 0.99 | 3 of 5 | 1 | **1** |
| US | B | 48.8% / 21.0% | -39.4% / -36.7% | 1.23 / 0.99 | 4 of 5 | 1 | **1** |
| India | A | 16.6% / 10.2% | -43.7% / -37.8% | 0.77 / 0.66 | 3 of 5 | 2 | **2** |
| India | B | 15.5% / 10.2% | -42.5% / -37.8% | 0.72 / 0.66 | 3 of 5 | 1 | **1** |

Per-slice detail: `results_US.json`, `results_IN.json`. Raw logs: `log_US.txt`, `log_IN.txt`.

## Verdict: FAIL the gate in all four cases
- It never beats the index on drawdown in most slices. Max drawdown is worse than the index every time.
- US variant A has a lower Sharpe than just holding QQQ (0.96 vs 0.99).
- This result is flattered, not penalised: the universe is today's winners (survivorship bias). The 48.8% CAGR of US variant B is not believable for that reason. Failing despite the flattery is the strong signal.
- Weak spot: strategy loses badly in 2020-21 (US) and 2018-19 / 2024-25 (India) while the index does fine.

## What I checked vs assumed
- Checked: code ran end to end on real Yahoo data; fills use next-day open; slices do not overlap (I fixed an overlap bug in the first run).
- Assumed: Yahoo adjusted prices are right (not cross-checked). The India index ^NSEI is a price index (no dividends), so the India benchmark is understated by roughly 1%/yr (my estimate). India costs of 0.10% per side are probably too low once taxes/STT are included.
- Not done: no point-in-time universe, no stops/regime filter (those were not part of the cheap test).
- 7 India symbols had no Yahoo data (TATAMOTORS, LTIM, ZOMATO, UNITEDBREW, MCDOWELL-N and 2 more) - renamed/delisted names, itself a small survivorship signal.

## Decision needed (yours)
The data says stop. Options:
1. Stop the momentum idea here. (Simplest.)
2. Go to Step 2 anyway, only to test the regime on/off switch (no stock picking) - the cheaper idea from the review.
3. Go to Step 2 as planned (point-in-time universe) - costs time/data and the bias-flattered result already failed.
Recommendation: 2.

Reproduce: `cd research/momentum_step1 && python3 run_step1.py US` (or `IN`).
