# The Plan — Core + Satellite

**Money split: 90% boring, 10% experiment. The two never touch.**

## Core — 90% (the money-maker, untouchable)

- **Buy:** VWRA (whole world) or CSPX (S&P 500), Ireland-domiciled, *accumulating* (reinvests dividends itself).
- **Why Irish:** 15% US dividend withholding (vs 25–30% for US ETFs) + no US estate tax.
- **How:** a fixed amount every month, forever. Don't look. Don't sell in a crash — a drop means you buy more shares.
- **Cost:** ~0.07–0.22%/yr hidden + ~$1–4 per trade. Keep buys ≥ $200–300 so fees stay under ~1%.
- **Rule:** never withdraw from this to fund trading. Ever.

## Satellite — 10% (the AI trading, money you're fine losing)

- **Separate account.** If it goes to zero, your life doesn't change.
- **Paper-first:** no real money until it beats the index on paper for a full year.
- **The system:**
  1. Six-agent pipeline — Regime, News Ingestor, Interpreter, Screener, Backtester, Decision Engine.
  2. **Every agent outputs numbers/scores, never free-text opinion** — so the Backtester can grade it.
  3. **Guardrails live outside the AI**, in a deterministic layer it can't modify (position caps, max loss, pre-registered exits, kill switch).
  4. **Autonomy is earned per-rule**: a rule only ships after the Backtester passes it (HAC-t + DSR + sub-period stable).
  5. **First thing to run:** the forward paper-trade of gap-down reversion — the only edge that passed testing.

## The one rule that holds it all together

> The 10% is money you've already said goodbye to. The 90% is money you never touch. If you ever feel the urge to move money from 90% to 10%, that's the signal to stop — not the market's, yours.

## Next actions (in order)

1. Open/mark a separate IBKR account (or sub-account) for the 10%.
2. Set up monthly auto-buy of VWRA or CSPX for the 90%.
3. Start the gap-reversion paper-trade (the real out-of-sample gate).
4. Only after the paper-trade shows an edge — build the 6-agent pipeline, advisory first.
