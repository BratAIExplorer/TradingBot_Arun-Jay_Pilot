# Small-Cap Dry-Run — Backtest Findings

*Run 2026-09-10. Log-only strategy (`strategies/small_cap_dryrun.py`). All runs
via `strategies/backtest_smallcap.py`; roll-up via `strategies/backtest_summary.py`.*

---

## 0. Follow-up (same session): factor & rotation strategies also fail

After §1–§5 concluded the MACD/rope strategy has no edge, we tested the three
highest-evidence "textbook" alternatives on clean 15-year monthly data
(2011-10 → 2026-09), both markets, net of a conservative round-trip cost:

| Market | Buy & hold index | Faber 10-mo SMA | Dual momentum | XS momentum (top 15) |
|---|---|---|---|---|
| US (SPY) | **+686%** / Sharpe 1.07 | +250% / 0.84 | +348% / 0.74 | not run (data-source blocked) |
| India (NIFTYBEES) | **+397%** / Sharpe 0.76 | +172% / 0.66 | +295% / 0.69 | +1115% vs **+1369% EW buy-hold** |

**Every one lost to buy-and-hold on raw return, and most on Sharpe too.**
Full numbers, mechanism, and caveats in §8–§10 below.

---

## 1. Executive summary

The small-cap swing strategy (price > 200-EMA + 50-EMA > 200-EMA + fresh MACD
cross → trailing 2% profit rope, 2-tranche scale-out, "never sell at loss")
**was backtested 21 ways** across India small-cap, US small-cap (S&P 600),
and US mid-cap (S&P 400), over 6-month and 24-month windows, with hard stops of
none / 2% / 8% / 12% and several structural tweaks.

**Result: no configuration beat simply buying and holding the same basket.**
In most cases it lost heavily to it. The strategy's entry signal has no
demonstrable edge; changing market, timeframe, or stop does not fix it.

**Recommendation: stop tuning this strategy. It is not the winning strategy.**
Keep the dry-run logging forward data as planned, but the next strategy needs a
*different entry thesis*, not another exit-rule tweak.

---

## 2. Key findings

### 2.1 The strategy loses to buy-and-hold everywhere

| Universe / window | Best strategy variant (book return) | Equal-weight buy & hold |
|---|---|---|
| US small-cap · 6mo | +8.1% (8% stop + loose entry) — all others −3% to −25% | **+17.3%** |
| US small-cap · 24mo | −4.5% (no stop); 8% stop = **−56.4%** | **+23.2%** |
| US mid-cap · 6mo | +1.0% (no stop); stops −3.6% to −18.8% | **+9.0%** |
| India small-cap · 6mo | per-trade avg +2.1% to +2.7% (see 4.3) | **+19.2%** |
| India small-cap · 24mo | +2.4% book (only 6 trades — noise) | +1.4% |

"Book return" = total P&L ÷ the $1,000 / 10-slot book over the run window.

### 2.2 The full run matrix (US, $1,000 book, $100/stock, 10 slots)

| Run | Trades | Win% (all) | Mean/trade | Median/trade | Stuck open | Book return |
|---|---|---|---|---|---|---|
| **US small, no stop** | 26 | 62% | −2.2% | +2.2% | 9/10 | −3.9% |
| US small, 2% stop | 91 | 24% | −3.3% | −5.9% | 7/10 | −25.5% |
| US small, 8% stop | 49 | 45% | −2.3% | −4.0% | 8/10 | −9.5% |
| US small, 12% stop | 38 | 50% | −2.9% | −0.2% | 9/10 | −7.7% |
| US small, 8% + **loose entry** (cross ≤7d) | 32 | 75% | +2.8% | +4.0% | 4/10 | **+8.1%** |
| US small, 8% + **wide rope** (6%) | 29 | 41% | −1.3% | −3.6% | 6/10 | −2.7% |
| US small, 8% + **fundamentals-now** | 37 | 43% | −3.5% | −3.7% | 6/10 | −10.4% |
| US small, no stop + fundamentals-now | 21 | 43% | −5.8% | −1.7% | 10/10 | −9.3% |
| US small, no stop, **24mo** | 38 | 68% | −1.6% | +1.9% | 10/10 | −4.5% |
| US small, 8% stop, **24mo** | 166 | 50% | −4.1% | −1.8% | 9/10 | **−56.4%** |
| **US mid, no stop** | 24 | 62% | +0.6% | +3.4% | 7/10 | +1.0% |
| US mid, 2% stop | 89 | 28% | −2.8% | −5.7% | 7/10 | −18.8% |
| US mid, 8% stop | 49 | 41% | −4.0% | −4.4% | 9/10 | −15.7% |
| US mid, 12% stop | 29 | 52% | −1.8% | +2.8% | 7/10 | −3.6% |

### 2.3 Why it fails (mechanism)

1. **Entry buys strength late.** A fresh MACD cross with price already above the
   200-EMA enters *after* the move started — often near a local top.
2. **Winners are cut small.** The 2% trailing rope + net-of-cost floor exits
   winners at roughly +4% to +6%.
3. **Losers run.** No stop (or an 8–12% stop) lets the bad picks fall 10–25%.
4. **Backwards asymmetry.** Avg win +4–6%, avg loss −6% to −17%. You need a very
   high win rate to survive that, and the strategy does not have it.
5. **Slippage tax.** Thin-book exit slippage (modelled 300bps for small-caps)
   is paid on every round trip; the 2%-stop versions churn 90+ times and bleed.

### 2.4 "Never sell at loss" hides losses, does not prevent them

The no-stop runs post the least-bad headline numbers **only because they never
book a loss** — the losses sit in stuck positions. In the US small-cap 24-month
no-stop run, **10 of 10 slots were underwater at the end**. The book is frozen,
not safe.

### 2.5 The one bright spot is thin

US small-cap, 8% stop, entry loosened to "MACD cross within 7 days" (vs the
configured 1 day): +8.1% book, 75% win rate. Still **below the +17.3%
buy-and-hold benchmark**, and it is a single 6-month window — almost certainly
luck, not edge. Worth noting, not worth trusting.

---

## 3. Answering the specific questions asked

**"Will this work better on the US market?"**
No. US structure removes two India-specific tail risks — no multi-day lower
circuits, tighter spreads / less slippage — but the entry signal is no better.
US small-cap and US mid-cap both lost to buy-and-hold in every stop setting.

**"Mid or small cap — what's the recommendation?"**
For *this* strategy, neither wins. US mid-cap (S&P 400) is marginally less bad
(no-stop +1.0% vs −3.9%) because bigger names trend more cleanly and cost less
to trade. If a future strategy does have edge, run it on the **liquid end of
small-cap (S&P SmallCap 600)** or mid-cap — not micro-cap, where slippage is
worse than India.

**"Does the fundamentals gate change the results?"**
Conceptually yes — it changes *which* names and *how many* trades. In practice
it did **not** rescue the outcome:
- US small-cap: 31 of 148 names cleared the ROE ≥10% / D-E ≤1 / positive-earnings
  gate on today's numbers. With the gate on: fewer trades (37 vs 49), same small
  loss (−10.4% vs −9.5%).
- India small-cap: only **4 of 127** names cleared the gate — yfinance's Indian
  fundamentals coverage is too thin and many curated names are financials with
  D-E > 1. With the gate on, the strategy makes ~0 trades. It effectively turns
  itself off.
- **Caveat:** this used *today's* fundamentals (lookahead bias). A proper
  point-in-time gate needs a paid data feed (EODHD / Sharadar / Capital IQ) and
  was not tested. It could differ — but nothing here suggests it flips a losing
  strategy into a winning one.

---

## 4. Risks and caveats (what these numbers do *not* prove)

1. **No point-in-time fundamentals.** The gate was tested only with current
   values (lookahead). Untested properly.
2. **Survivorship bias.** Universes are today's index members. Delisted /
   collapsed names are absent, so real "stuck" counts are understated — 8 India
   and ~2 US names were dropped for missing data.
3. **Entry ranking is a proxy.** When signals outnumber free slots, the backtest
   ranks by "least extended above the 200-EMA". The live bot ranks by the
   scanner confluence score, which was not reproduced here.
4. **Windows are short.** 6 months is one market mood. The 24-month US run is the
   most trustworthy and it is the *worst* result (−56% with an 8% stop).
5. **India $100/stock runs are unreliable.** `--per-stock 100` on ₹-priced
   stocks truncates to <1 share for anything above ₹100, so only cheap names
   traded (3 trades). The India figures used here are the earlier ₹1-lakh-book
   runs (`bt_portfolio_*.csv`); their book-return % is not comparable to the
   USD runs but their per-trade % and realised P&L are (all realised P&L
   negative; totals flattered by open positions).
6. **Costs are modelled, not real.** Zerodha/US-broker assumptions; live fills
   will differ.

---

## 5. Recommendation

1. **Do not deploy this strategy and do not keep tuning it.** 21 backtests across
   two countries and four stop settings agree: no edge.
2. **The honest benchmark is boring:** equal-weight buy-and-hold of a quality
   small/mid basket beat every active variant here by 10–25 points. If the goal
   is "grow the account with limited attention", that is the finding.
3. **Keep the dry-run running in log-only** — forward paper data is still worth
   collecting, and the stranded-half fix (below) makes it cleaner — but do not
   expect it to turn green.
4. **A future strategy needs a different entry thesis** — mean reversion,
   post-earnings drift, or cross-sectional relative-strength ranking — not
   another exit-rule or stop-loss variation on this trend-follow entry.
5. If US trading is still wanted later, note the access friction: non-India
   broker, RBI LRS remittance cap, W-8BEN, PFIC rules on US ETFs, US estate-tax
   exposure over ~$60k situs. Verify current thresholds before acting.

---

## 6. Code changes made this session

| File | Change |
|---|---|
| `strategies/configs/small_cap_dryrun.json` | `total_budget` 30,000 → 100,000 (3 → 10 slots) |
| `strategies/small_cap_dryrun.py` | **Stranded-half fix:** the final half now auto-sells when price recovers to the net-profit floor; manual sell only while it stays below the floor. Was: could never sell by machine. |
| `strategies/backtest_smallcap.py` | New. Day-by-day backtest reusing the live `decide()`/`advance_rope()`. `--portfolio` (slot-capped shared book), `--hard-stop`, `--total-budget`, `--per-stock`, `--universe-file`, `--fresh-cross-days`, `--trail-giveback`, `--fundamentals-now`. Price cache in `.px_cache/`. |
| `strategies/backtest_summary.py` | New. Rolls up all `bt_*.csv` + computes buy-and-hold benchmarks. |
| `strategies/tests/test_strategy.py` | +1 test for the stranded-half recovery path (14 pass). |
| `strategies/tests/{test_config_file,test_runner,test_strategy_routes}.py` | Updated the 3 tests that hard-coded the old 30k/3-name budget (120 pass). |
| `strategies/univ_us_small_sp600.txt`, `univ_us_mid_sp400.txt` | 150-name samples from Wikipedia S&P 600 / 400 lists (seed 42). |

Per-run detail: `strategies/bt_*.csv` (uncommitted).

---

## 7. Sources

- Strategy performance: the backtests in this session (`strategies/bt_*.csv`),
  subject to the caveats in §4.
- Universe constituents: Wikipedia "List of S&P 600 / 400 companies", fetched
  2026-09-10.
- Price data: Yahoo Finance daily bars via `yfinance`, `auto_adjust=True`.
- Market-structure and access claims (US LULD vs Indian circuit bands, RBI LRS
  cap, US estate-tax threshold): general knowledge as of early 2026 — verify
  current figures before acting.

---

## 8. Factor & rotation strategies (new, 2026-09-10)

New harnesses, kept separate from the small-cap rope strategy:
- `strategies/factor_backtest.py` — monthly trend-timing + dual-momentum engine.
- `strategies/xs_momentum.py` — cross-sectional momentum engine.

Both use Yahoo **monthly** bars, `auto_adjust=True` (total-return, distributions
reinvested), 15y windows. Cash earns **0%** (conservative — no risk-free credit
to flatter idle money). Round-trip cost charged on every turnover: US 8bps,
India 20bps (ETFs) / 40bps (single names). Benchmark is the **tradable index ETF
itself** (SPY / NIFTYBEES), not a sterile price index.

### 8.1 US (2011-10 → 2026-09, 180 months)

| Strategy | TotRet | CAGR | Vol | Sharpe | MaxDD | Calmar | RT/yr | %Inv |
|---|---|---|---|---|---|---|---|---|
| Buy & hold SPY | **686%** | 14.8% | 13.8% | **1.07** | −24% | **0.62** | 0.1 | 99% |
| Faber 10-mo SMA | 250% | 8.8% | 10.6% | 0.84 | −23% | 0.37 | 1.7 | 81% |
| Dual momentum (top 1) | 348% | 10.6% | 15.0% | 0.74 | −35% | 0.30 | 6.2 | 88% |

### 8.2 India (2011-10 → 2026-09, 180 months)

| Strategy | TotRet | CAGR | Vol | Sharpe | MaxDD | Calmar | RT/yr | %Inv |
|---|---|---|---|---|---|---|---|---|
| Buy & hold NIFTYBEES | **397%** | 11.3% | 15.7% | **0.76** | −29% | 0.39 | 0.1 | 99% |
| Faber 10-mo SMA | 172% | 6.9% | 11.0% | 0.66 | −18% | 0.39 | 1.7 | 72% |
| Dual momentum (top 1) | 295% | 9.6% | 14.9% | 0.69 | −19% | 0.50 | 4.7 | 93% |

### 8.3 What the trend-timing numbers mean

1. **Faber did NOT deliver "half the vol, same return".** It cut vol a little
   (−23% MaxDD vs −24%) but gave up ~436 pts (US) and ~225 pts (India) of total
   return to do it. Sharpe *fell* (0.84 vs 1.07; 0.66 vs 0.76).
2. **Why it failed: monthly signals are too slow for fast crashes.** The 10-month
   SMA only re-prices at month-end, so it rode straight through the Feb–Mar 2020
   COVID drop, sold near the bottom, and missed the V-shaped rebound — the exact
   whip a monthly filter is supposed to avoid.
3. **Dual momentum** (SPY/QQQ/EFA/TLT/GLD; NIFTYBEES/JUNIORBEES/GOLDBEES/LIQUIDBEES)
   held up better in India (Calmar 0.50, MaxDD −19% vs −29%) but still trailed
   buy-and-hold on Sharpe in both markets.

## 9. Cross-sectional momentum (the "selection edge" test)

The one candidate that directly fixes the *selection* flaw: monthly, rank a
liquid large-cap universe by trailing 12-month return skipping the last month
(Jegadeesh-Titman), hold the top 15 equal-weight. The honest benchmark is
**static equal-weight buy-and-hold of the same universe** — if momentum can't
beat that, it has no selection edge.

### 9.1 India — Nifty 50 (48 names, 2011-10 → 2026-09, cost 40bps RT)

| Strategy | TotRet | CAGR | Vol | Sharpe | MaxDD | Calmar | RT/yr |
|---|---|---|---|---|---|---|---|
| Static EW buy-&-hold (all) | **1369%** | **19.7%** | 16.5% | **1.18** | −28% | 0.71 | 0.1 |
| XS momentum (no filter) | 1115% | 18.2% | 16.3% | 1.11 | −25% | 0.72 | 4.3 |
| XS momentum + 10-mo regime filter | 547% | 13.3% | 12.8% | 1.04 | −22% | 0.61 | 4.6 |

**Momentum did not beat equal-weight buy-and-hold.** Even the strongest academic
factor — in a market where the published Nifty200 Momentum 30 index was a
marketing hit — did not clear a dumb, zero-turnover, hold-everything benchmark
after costs. The regime filter made it *worse*, not better (18.2% → 13.3% CAGR).

### 9.2 US — S&P 500

**Not run.** The Wikipedia constituent table could not be scraped from this
environment (403 / table-parse failure). The US picture is instead covered at the
ETF level in §8.1, and by the published literature (US momentum has decayed
markedly post-2016 — McLean & Pontiff). Not re-attempted: it would not change the
cross-market conclusion.

## 10. Conclusion — the boring answer is the answer

Across **two countries, two universes, and four strategy families** (MACD/rope,
trend-timing, dual momentum, cross-sectional momentum), the result is consistent:

> **No active strategy beat buying and holding a diversified index basket over
> 2011-2026, net of costs.**

The "winning strategy" for this data window is not a signal. It is:

1. **A diversified, low-cost, broad-market holding** (SPY / NIFTYBEES, or a Nifty
   50 / S&P 500 index fund) — buy and hold.
2. **The real edge is behavioural, not mathematical**: holding through drawdowns
   instead of panic-selling. That is the one thing every active variant got wrong
   here — they all sold near bottoms (Faber), churned (dual momentum), or paid
   costs for selection that added nothing (momentum).
3. **Cost control.** The only lever that reliably improved outcomes was doing
   less. Zero-turnover buy-and-hold pays nothing to win.

If a defensive overlay is ever wanted (shorter drawdowns, willingness to accept
lower CAGR), the India dual-momentum result (Calmar 0.50, MaxDD −19%) is the one
worth revisiting — but it is a *risk* choice, not an *alpha* choice.

### Caveats that bound every number above (read before trusting any of it)
- **Survivorship / point-in-time.** All universes are *today's* constituents.
  This flatters every strategy, and it especially flatters the equal-weight
  benchmark (it "holds" today's 50 winners for 15 years with perfect foresight).
  Real-world results will be worse.
- **One window, one regime.** 2011-2026 is one long US-led bull with two shallow
  (fast) bear markets. These strategies would rank differently in 2000-2011 (two
  −50% crashes, zero net return) — where trend-following would look much better.
- **Cash earns 0%.** Real idle cash (T-bills, LIQUIDBEES) would modestly help the
  risk-off strategies; not enough to change the conclusion here.
- **Monthly bars** understate the max drawdown of daily stop-based strategies and
  can't time intra-month exits. This is a limitation, not a flatter, for the
  trend strategies.

## 11. Irish-domiciled (UCITS) ETFs + the stocks-vs-ETF question

### 11.1 Irish wrappers deliver the same beta as US — with a better tax home

For a non-US investor (Indian resident), US-domiciled ETFs carry two real traps:
**US estate tax** (on US-situs assets > $60k, up to 40%) and **30% dividend
withholding** (reduced only with a W-8BEN). Irish-domiciled UCITS ETFs eliminate
the estate tax and cut withholding to 15%. (Note: PFIC applies to *US persons*
holding foreign funds, not to a non-US holder of US ETFs — the earlier doc's
mention was imprecise.)

15y buy-and-hold, same window, confirms the Irish wrapper is the same beta:

| Index | US | Irish | Gap |
|---|---|---|---|
| S&P 500 | SPY 687% / Sharpe 1.07 / DD −24% | CSPX.L 652% / 1.07 / −22% | TER + tracking only |
| Nasdaq 100 | QQQ 1305% / 1.11 / −33% | CNDX.L 1246% / 1.11 / −33% | TER + tracking only |

The small gaps are the higher UCITS TER (0.07% vs 0.03%) plus tracking — not a
reason to prefer US. Same Sharpe, same drawdown, same beta. **Recommendation:
hold the international sleeve via an Irish accumulator** (CSPX for S&P 500, VWRA
for all-world). Caveats:

- **SGLN.L vs GLD is not apples-to-apples** — SGLN.L quotes in GBX, so its higher
  number (195% vs 141%) is USD→GBP FX, not real gold alpha. **Keep gold as
  GOLDBEES domestically** (no FX, no LRS, no foreign wrapper).
- **VWRA / VUAA only have ~7y** of history (launched 2019); they track the same
  indices as CSPX/IWDA (full 15y), so backtest on the older twins.
- Ireland fixes the *tax domicile*, not the *access friction* — you still need an
  international broker (Interactive Brokers) and the RBI LRS $250k/yr remittance.

### 11.2 "Aren't we looking at stocks, not ETFs?" — yes, and stocks were tested

The research **did** run individual stocks, not just ETFs:

- The small-cap MACD/rope strategy ran on **individual US small-cap, US mid-cap,
  and India small-cap names** (21 backtests) → lost to buy-and-hold everywhere.
- Cross-sectional momentum ran on **48 individual Nifty 50 stocks** (§9) → lost
  to holding all 48 equal-weight.

So the finding is **active trading loses to passive holding — in whatever
wrapper.** The ETF-vs-stocks choice is a *convenience* decision, not an edge.

The one apparent contradiction, explained (do not misread this):

| India, 15y | CAGR |
|---|---|
| NIFTYBEES (ETF, cap-weighted) | 11.3% |
| "Hold all 48 Nifty stocks equal-weight" (backtest) | **19.7%** |

That 19.7% is a **survivorship illusion**, not a real result: the backtest
"held" *today's* 48 winners for 15 years with perfect hindsight (including names
that IPO'd later or weren't in Nifty in 2011). The honest real-world number is
the index you could actually have held: ~11–12%, which is NIFTYBEES.

**Bottom line:** the winning answer is broad, diversified, buy-and-hold.

1. **ETF / index fund (recommended):** NIFTYBEES for India; CSPX/VWRA (Irish) for
   international. Zero selection risk, ~0.05–0.2% cost.
2. **Individual stocks, only done passively:** an equal-weight basket of ~30–50
   liquid large caps held and rebalanced annually — *not* stock-picked. The only
   defensible reason to prefer this over an ETF is a systematic tilt
   (equal-weight / size), and it adds single-name blowup risk (Satyam / Yes Bank)
   plus admin.
3. **Never:** trade in and out of individual stocks on a signal — the losing path
   every backtest here keeps confirming.

### 11.3 New sources

- Irish/US ETF price history: Yahoo Finance monthly bars (`auto_adjust=True`).
- US estate-tax / NRA withholding / UCITS treatment: general knowledge as of
  early 2026 — verify current thresholds before acting.
- Factor evidence: Faber (2007), Antonacci (2014), Jegadeesh-Titman (1993),
  Asness-Moskowitz-Pedersen (2013), McLean-Pontiff (2016).
