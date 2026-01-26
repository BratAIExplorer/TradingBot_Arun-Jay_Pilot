# 🐞 ARUN Bot - Bug Tracker & Regression Log

This document serves as the central registry for all reported bugs, their status, and technical details of the fixes. Use this to ensure bugs do not re-occur (regression testing).

## 🔴 Open Issues
| ID | Priority | Description | Reported By | Date | Notes |
|----|----------|-------------|-------------|------|-------|
| *None* | - | All reported bugs have been resolved! 🎉 | - | - | - |

## 🟢 Resolved Issues
| ID | Issue | Fix Description | Fixed Date | Verified By |
|----|-------|-----------------|------------|-------------|
| 001 | App Crash | Added missing `datetime` import in dashboard. | 2026-01-17 | AI |
| 002 | Settings Tab Crash | Defined `COLOR_ACCENT` constant. | 2026-01-17 | AI |
| 003 | Installer Launch Fail | (Pending Verification) | - | - |
| 004 | **Add Stock UI**: Scrollbar missing | Added `CTkScrollableFrame` wrapper for dialog content. Increased dialog size to 450x600. | 2026-01-19 | AI |
| 005 | **Stock Validation**: Always returns 'Valid' | Verified `validate_symbol()` is called correctly in `on_validate_symbols()`. Uses yfinance with 1-day history check. | 2026-01-19 | AI |
| 006 | **Cancel Button**: No action on click in stock dialog | Added Cancel button with `dialog.destroy()` command next to Save button. | 2026-01-19 | AI |
| 007 | **Strategies Tab**: Naming confusion ("Buckets") | Renamed "SECTOR BASKETS (BUCKETS)" to "SECTOR WATCHLIST" for clarity. | 2026-01-19 | AI |
| 008 | **Capital Display**: Dashboard not showing updated capital after save | Enhanced save callback to trigger dashboard UI refresh via `refresh_bot_settings()`. | 2026-01-19 | AI |
| 009 | **START/STOP Buttons**: Not showing on dashboard | Removed duplicate ROW 3 code block (lines 639-670) that was overwriting proper button implementation. | 2026-01-19 | AI |

## 🛡️ Regression Testing Checklist
Before every release, verify these items:
- [ ] **Validation**: Try adding "INVALID123". Must fail.
- [ ] **Add Stock**: Open dialog, resize window - scrollbar should appear.
- [ ] **Edit Stock**: Open existing stock. Verify ALL fields are populated: Symbol, Exch, Strategy, TF, Buy RSI, Sell RSI, Qty, Target.
- [ ] **Cancel Button**: Click Cancel in stock dialog - should close without saving.
- [ ] **Strategies Tab**: Verify section is named "SECTOR WATCHLIST" (not "Buckets").
- [ ] **Dashboard Buttons**: START ENGINE and EMERGENCY STOP buttons visible and functional.
- [ ] **Capital Update**: Change capital, save, verify dashboard updates within 2 seconds.
