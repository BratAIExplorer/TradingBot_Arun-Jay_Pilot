# 📋 Development Backlog (ARUN Bot)

This backlog tracks future enhancements and refactoring work required to scale the bot to a production-grade SaaS.

## 🏗️ Phase 2: Structural Refactoring (High Priority)
- [ ] **Monolith Deconstruction**: Split the 2,600+ line `kickstart.py` into:
    - `services/market_data.py`: Handles YFinance, mStock, and TV data.
    - `services/order_execution.py`: Handles order placement and validation.
    - `services/strategy_engine.py`: Handles RSI and SIP logic.
- [ ] **Dependency Injection**: Pass services to the UI/Engine instead of relying on global variables.

## 📊 Phase 3: Advanced Analytics
- [ ] **Performance Engine**: Calculate Sharpe Ratio, Max Drawdown, and Win Rate per strategy.
- [ ] **Equity Curve**: Plot a live graph of account performance on the dashboard.
- [ ] **Trade Tagging**: Add 'Notes' to trades in the database (e.g., "Manual exit," "Risk trigger hit").

## 🤝 Phase 4: Customer Empowerment (SaaS Features)
- [ ] **Onboarding Wizard**: A step-by-step setup for new users (API connection, Capital setting).
- [ ] **Multi-Strategy Support**: Allow running RSI and SIP strategies simultaneously on the same symbol.
- [ ] **Mobile Notifier**: Complete the Telegram integration (Push notifications for every trade).

## 🐛 Tech Debt
- [ ] Implement Logging rotation (to prevent `bot.log` from growing too large).
- [ ] Add Integration Tests (mocking the full mStock API response flow).
