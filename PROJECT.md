# ARUN Trading Bot (Titan Project)

## What It Is
An autonomous retail unit designed for high-performance algorithmic trading across Multiple Brokers (mStock, Zerodha, Binance, Luno).

## Core Philosophy
- **Wealth Generation**: Focus on "Buy-the-Dip" and "RSI Mean Reversion" strategies.
- **Risk Management**: Mandatory Stop-Loss, Trailing Profits, and Catastrophic Circuit Breakers.
- **Independence**: Built to run headless on VPS or locally with zero dependencies on external dashboards for core trading logic.

## Key Features
- **Multi-Pair Execution**: Track and trade multiple symbols simultaneously.
- **Hybrid Butler Mode**: Integrated PnL tracking for both Bot-managed and Manually-held (CNC) positions.
- **High Reliability**: Real-time heartbeat, auto-relogin, and connectivity resilience.

## Roadmap
- **Phase 1**: Stability & Symbol Accuracy (mStock REITs).
- **Phase 2**: Multi-Pair Architecture refinement.
- **Phase 3**: Optional read-only bridge to the FinFlow Wealth Hub.

> [!IMPORTANT]
> This is an active execution engine. Do NOT share your `settings.json` with anyone, as it contains sensitive API credentials.
