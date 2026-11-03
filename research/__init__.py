"""Research harness — the honesty layer for signal testing.

This package exists because the org has now retracted one "finding" that a
naive test produced (see FinFlow/CURRENT_STATUS.md). Every tool here exists to
make that failure mode structurally hard to repeat:

- `stats`       — HAC t-stats, block bootstrap, deflated Sharpe, matched base rates
- `walkforward` — purged + embargoed K-fold (Lopez de Prado) for any fitted model
- `data`        — cached daily bars, earnings events, GDELT historical news
- `signals`     — signal construction with no-lookahead guarantees
- `run_pead`    — the post-earnings-drift study (Tier 1)
- `run_news`    — the news-headline study (standalone + incremental over PEAD)

Nothing here touches the live bot. It is a sandbox for deciding what is real.
"""
