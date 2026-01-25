# Changelog

All notable changes to ARUN Trading Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive audit documentation
- Architecture modernization plan
- SaaS transformation roadmap

### Fixed
- **BUG-001**: Removed duplicate `run_cycle()` function definition (kickstart.py:771 and 2280)
- **BUG-003**: Added thread safety to database writes using threading.Lock()
- **BUG-007**: Completed incomplete `get_today_trades()` function implementation

### Changed
- Updated README with comprehensive documentation and roadmap
- Enhanced documentation structure with audit reports and guides

## [3.0.0] - 2026-01-25

### Added
- **Seamless RSI Strategy**: Phase B and C implementation with incremental polling
- **Risk Controls**: 200-bar stabilization period before trading
- **Risk Management Service**: Position limits, stop-loss, profit targets
- **State Manager**: Persisted stop requests across sessions
- **Notification Service**: Multi-channel alerts (Telegram, Email)
- **Database Logging**: Comprehensive trade history with P&L tracking
- **Symbol Validator**: Automatic validation against NSE stock list
- **Offline Detection**: Automatic pause when connectivity is lost
- **Paper Trading Mode**: Risk-free strategy testing

### Fixed
- RSI calculation stabilization with 200-bar minimum requirement
- Auto-login flow with TOTP integration
- Order placement error handling and retry logic
- Position tracking across broker API sessions

### Changed
- Migrated to mStock Type-A API
- Improved dashboard UI with dark mode
- Enhanced logging with structured output
- Optimized candle data caching

## [2.0.0] - 2025-12-15

### Added
- **CustomTkinter Dashboard**: Modern GUI with tabbed interface
- **Multi-Symbol Support**: Track and trade multiple stocks simultaneously
- **Settings GUI**: User-friendly configuration management
- **Trade History Tab**: View all past trades with filters
- **Knowledge Center**: In-app strategy documentation

### Fixed
- Memory leak in candle cache
- Thread safety issues in position updates
- API authentication failures

### Changed
- Replaced Tkinter with CustomTkinter for better UI
- Refactored settings management to use JSON instead of CSV
- Improved error messages and user feedback

## [1.0.0] - 2025-10-01

### Added
- **Initial Release**: Basic RSI mean reversion strategy
- **mStock Integration**: Broker API connectivity
- **Manual Trading**: Buy/sell with basic UI
- **SQLite Database**: Trade logging functionality
- **Basic Risk Management**: Position size limits

### Known Issues
- Single-threaded execution (no parallel processing)
- Limited error handling
- No automated tests
- Basic console-only interface

---

## Legend

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements

---

## Versioning

Version format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes
- **MINOR**: New features (backward-compatible)
- **PATCH**: Bug fixes (backward-compatible)

---

## Links

- [Unreleased Changes](https://github.com/ORIGINAL_OWNER/TradingBot_Arun-Jay_Pilot/compare/v3.0.0...HEAD)
- [3.0.0 Release](https://github.com/ORIGINAL_OWNER/TradingBot_Arun-Jay_Pilot/releases/tag/v3.0.0)
- [2.0.0 Release](https://github.com/ORIGINAL_OWNER/TradingBot_Arun-Jay_Pilot/releases/tag/v2.0.0)
- [1.0.0 Release](https://github.com/ORIGINAL_OWNER/TradingBot_Arun-Jay_Pilot/releases/tag/v1.0.0)
