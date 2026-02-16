# Error Log & Fixes — ARUN Trading Bot

**Last Updated**: February 16, 2026
**Version**: v2.5.1 (Security Audit Fixes)

---

## v2.5.1 — Security & Architecture Audit Fixes (Feb 16, 2026)

### FIX 1: Credentials Removed from Git Tracking (P0 - CRITICAL)
**Issue**: `settings.json` containing plaintext passwords, TOTP secrets, and API keys was tracked by git, exposing credentials in version history.
**Root Cause**: File was committed before `.gitignore` was set up properly.
**Fix Applied**:
- `git rm --cached settings.json bot_state.json` — removed from git tracking
- Both files were already in `.gitignore` but still tracked
- `settings_default.json` template updated with `access_token` and `totp_secret` fields
**Files Changed**: `.gitignore` (already correct), `settings_default.json`
**User Action Required**: Rotate ALL credentials via mStock Developer Console.

---

### FIX 2: Encryption Bypass in save_settings() (P0 - CRITICAL)
**Issue**: `settings_gui.py:save_settings()` built a raw dict with plaintext credentials and called `current_settings.update(new_settings)` then `settings_mgr.save()`. This bypassed the `SettingsManager.set()` method which triggers Fernet encryption via `_is_sensitive_field()`.
**Root Cause**: Bulk `dict.update()` overwrites encrypted values with plaintext.
**Fix Applied**:
- Sensitive fields (`api_key`, `api_secret`, `password`, `access_token`, `totp_secret`, `telegram_bot_token`) now routed through `self.settings_mgr.set(key_path, value)` which triggers encryption
- Non-sensitive fields still use efficient bulk `dict.update()`
- Removed duplicate `self.settings_mgr.save()` call (was called twice)
**File Changed**: `settings_gui.py` — `save_settings()` method (~line 1173)
**mStock API Impact**: None. Encryption is at-rest only; API receives decrypted values at runtime.

---

### FIX 3: Secret Logging Removed (P0 - SECURITY)
**Issue**: TOTP codes, API key prefixes, and response data containing access tokens were logged to console/files in plaintext.
**Fix Applied**:
| Location | Before | After |
|----------|--------|-------|
| `kickstart.py:296` | `print(f"DEBUG REQ: {method} {url}")` | Removed (commented) |
| `kickstart.py:1023` | `log_ok(f"Generated TOTP: {otp_code}")` | `log_ok(f"Generated TOTP: ***{otp_code[-2:]}")` |
| `kickstart.py:1048` | `log_ok(f"Response Data: {totp_data}")` | Removed (contained access tokens) |
| `kickstart.py:1268` | `API_KEY[:10]` | `'***' + API_KEY[-4:]` |
**File Changed**: `kickstart.py`

---

### FIX 4: Operator Precedence Bug (P1 - HIGH)
**Issue**: `if "TokenException" or "invalid session" in error_str:` always evaluated to `True` because Python parses it as `if ("TokenException") or ("invalid session" in error_str):` and `"TokenException"` is truthy.
**Impact**: Every exception in `safe_get_positions()` was treated as a token issue, hiding real bugs (network errors, data corruption, rate limiting).
**Fix Applied**:
```python
# Before (BUGGY):
if "TokenException" or "invalid session" in error_str:
# After (CORRECT):
if "TokenException" in error_str or "invalid session" in error_str:
```
**File Changed**: `kickstart.py:1325`

---

### FIX 5: Singleton SettingsManager (P1 - HIGH)
**Issue**: 4 independent `SettingsManager()` instances created across `kickstart.py` (lines 68, 368, 1168) and `settings_gui.py` (line 29). If one saves while another has stale data, settings can regress silently.
**Fix Applied**: Added `__new__` singleton pattern to `SettingsManager`:
```python
class SettingsManager:
    _instance = None
    _initialized = False

    def __new__(cls, settings_file="settings.json"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, settings_file="settings.json"):
        if SettingsManager._initialized:
            return
        SettingsManager._initialized = True
        ...
```
All existing `SettingsManager()` calls now return the same instance — zero caller changes needed.
**File Changed**: `settings_manager.py`

---

### FIX 6: Thread Safety Locks (P2 - MEDIUM)
**Issue**: Mutable dicts (`CYCLE_QUOTES`, `FETCH_STATE`, `live_positions`, `MISSING_TOKEN_LOGGED`) shared between GUI thread and background workers with no synchronization. Race conditions possible.
**Fix Applied**:
- Added `import threading` and `_STATE_LOCK = threading.Lock()` at module level
- Wrapped `live_positions` global assignment with `with _STATE_LOCK:`
- Wrapped `reset_cycle_state()` and `reset_cycle_quotes()` clear operations with lock
**File Changed**: `kickstart.py`

---

### FIX 7: Scanner Stop Propagation (P2 - MEDIUM)
**Issue**: `stop_scanner()` in dashboard set `self.scanner_running = False` but never called `scanner.stop()` on the `MACDScanner` instance. Scanner would continue downloading data until complete.
**Fix Applied**:
- `start_scanner()`: Added `self.active_scanner = scanner` to store reference
- `stop_scanner()`: Added `self.active_scanner.stop()` call to propagate stop signal
**File Changed**: `sensei_v1_dashboard.py`

---

### FIX 8: Dead Code Cleanup (P3 - LOW)
**Issue**: Multiple blocks of unreachable/dead code across codebase.
**Fix Applied**:
| Location | What | Lines Removed |
|----------|------|---------------|
| `state_manager.py:45-46` | Unreachable `logging.info()` + duplicate `return` after first `return merged` | 2 lines |
| `kickstart.py:709` | Duplicate `return []` after function already returned | 2 lines |
| `kickstart.py:856-987` | `_legacy_UNUSED_run_cycle()` — entire unused function | ~130 lines |
**Files Changed**: `state_manager.py`, `kickstart.py`

---

## Pre-v2.5.1 Known Issues (Previously Fixed)

### REIT OHLC API 400 Errors (Fixed v2.3.1)
- **Cause**: Numeric tokens from `REIT_TOKEN_MAP` sent to OHLC API which expects scrip names
- **Fix**: BSE fallback for REIT symbols where they're listed as EQ series

### Scanner Key Case Bug (Fixed v2.3.1)
- **Cause**: `scanner_complete()` used lowercase `r['signal']` but engine returns uppercase `r['SIGNAL']`
- **Fix**: Changed to `r.get('SIGNAL')`

### Duplicate Buys Across Exchanges (Fixed v2.4.2)
- **Cause**: Buy check was exchange-specific, allowing same symbol on NSE + BSE
- **Fix**: Symbol-aware check blocks BUY if symbol exists on ANY exchange

---

*For the full audit report, see `SECURITY_ARCHITECTURE_AUDIT_v2.5.0.md`*
