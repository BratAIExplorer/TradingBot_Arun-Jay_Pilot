# What To Actually Buy — one-page plan

*Written 2026-09-10. Follows directly from `BACKTEST_FINDINGS.md`: across MACD/rope,
trend-timing, dual-momentum and cross-sectional momentum, two countries, 15 years,
net of costs — **no active strategy beat buying and holding a broad index.** This
is the plan that finding implies.*

---

## The rule

Fixed amount, fixed date, every month. No buy signal. No waiting for dips. No
selling on a chart. The only edge that showed up in every test was *not selling
during drawdowns*.

---

## What to hold

| Sleeve | Instrument | Why |
|---|---|---|
| **India equity** (core) | **NIFTYBEES** (Nifty 50 ETF) | Tested: 11.3% CAGR over 15y. Locally listed, ~0.05% cost, no FX, no remittance. |
| **International equity** | **CSPX** (Irish S&P 500 acc) *or* **VWRA** (Irish all-world acc) | Same beta as SPY/VT, better tax home (no US estate tax, 15% vs 30% dividend withholding). Needs overseas broker + LRS — see below. |
| **Gold** (optional, 5–10%) | **GOLDBEES** | Domestic. Don't use a foreign gold ETF — the return gets polluted by GBP/USD FX. |
| **Cash you'll need <3 yrs** | **LIQUIDBEES** / bank FD | Not equity. Don't put short-term money in the above. |

A simple split: 60–70% NIFTYBEES, 20–30% CSPX/VWRA, 0–10% GOLDBEES. Adjust once
for your home-bias preference, then leave it.

---

## Explorer sleeve (optional, max 10%)

Separate pot for single stocks. **Not core.** Every backtest says this loses on
average — it is sized so being wrong is a scratch, not a wound.

- **Size:** 5–10% of total, across **4–6 names minimum**, no name > 2% of total.
- **US (live FinViz data):** GOOGL, DECK, INTU, AOS, CPRT.
- **India (verify valuation on screener.in first):** Nesco, ITC, Asian Paints,
  P I Industries.
- **Pre-committed sell rules** (per name, in `VALUE_QUALITY_SHORTLIST.md`) — a
  falling price is **not** one of them.
- If the whole sleeve trails the core index for 3 years, shut it down.

Full reasoning + per-name sell triggers: `VALUE_QUALITY_SHORTLIST.md`.
Screen method + filters: `EXPLORER_SLEEVE_SCREEN.md`.

---

## ₹20,000/month, at the tested 11.3%

| Duration | You invest | Projected value | Realistic range (9–12%) |
|---|---|---|---|
| 10 years | ₹24 L | ~₹44 L | ₹38–48 L |
| 15 years | ₹36 L | ~₹93 L | ₹76 L – ₹1.0 Cr |
| 20 years | ₹48 L | ~₹1.8 Cr | ₹1.4 – 2.1 Cr |

**These are not promises.** 11.3% is one past 15-year window. Expect several
years of −20% to −30% on the way. After ~5% inflation, the 15-year figure is
worth ~₹58 L in today's money.

---

## International sleeve — the setup friction

- **Broker:** Interactive Brokers (realistic route for LSE-listed UCITS).
- **Remittance:** RBI LRS cap, USD 250k / financial year. File the bank's A2 form.
- **Tax:** foreign assets must be reported in the India return (Schedule FA).
  Use *accumulating* (Acc) share classes — no dividends to track.
- If this friction isn't worth it to you, **NIFTYBEES-only is a valid plan.**
  You lose geographic diversification, not expected edge.

---

## What this plan deliberately does NOT do

- No stock picking **in the core** (the explorer sleeve above is capped at 10%
  and ring-fenced — it never touches the core SIP).
- No AI stock scoring. No "predict the trend" bets sized large.
- No market timing, no regime filter (it made the India momentum test *worse*).
- No monthly rebalancing of individual names.

## Open / not done

- **Re-verify blocked:** the one result that contradicts the external research
  doc (India momentum losing, regime filter hurting) should be re-run on
  survivorship-free point-in-time data with a proper holdout. Needs a paid feed
  (EODHD / Sharadar). Not done — pending data access.
- Projections assume the tested 11.3% holds. It may not.
- International buy-and-hold numbers were computed on monthly bars, lump-sum —
  not as a SIP, not on daily bars.
