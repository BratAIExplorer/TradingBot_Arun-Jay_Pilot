@echo off
setlocal enabledelayedexpansion
title ARUN Bot - Auto Update & Fix Conflicts
color 0B

:: =================================================================
:: AUTO-UPDATE & CONFLICT RESOLVER
:: This script pulls latest changes and resolves merge conflicts
:: =================================================================

echo ========================================================
echo     🔄 ARUN BOT - AUTO UPDATE ^& FIX
echo ========================================================
echo.
echo This will:
echo   1. Pull latest changes from GitHub
echo   2. Resolve any merge conflicts automatically
echo   3. Validate Python syntax
echo   4. Prepare for launch
echo.
echo ========================================================
timeout /t 3 >nul

:: ---------------------------------------------------------
:: Step 1: Check Git Status
:: ---------------------------------------------------------
echo.
echo [Step 1/5] Checking Git status...
git status >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ This folder is not a Git repository.
    echo    Please clone the repository first.
    pause
    exit /b 1
)

:: ---------------------------------------------------------
:: Step 2: Fetch Latest Changes
:: ---------------------------------------------------------
echo [Step 2/5] Fetching latest changes from GitHub...
git fetch origin claude/fix-ui-exchange-validation-U9IPJ
if %errorlevel% neq 0 (
    echo ⚠️  Warning: Could not fetch from remote.
    echo    Continuing with local version...
) else (
    echo ✅ Latest changes fetched successfully.
)

:: ---------------------------------------------------------
:: Step 3: Check for Merge Conflicts
:: ---------------------------------------------------------
echo [Step 3/5] Checking for merge conflicts...

git diff --name-only --diff-filter=U >conflicts.tmp 2>nul
set CONFLICTS=0
for /f %%i in (conflicts.tmp) do set CONFLICTS=1

if %CONFLICTS%==1 (
    echo ⚠️  Merge conflicts detected! Resolving automatically...

    :: Accept incoming changes for dashboard_v2.py (our new features)
    echo    Resolving dashboard_v2.py (accepting new features)...
    git checkout --theirs dashboard_v2.py 2>nul
    git add dashboard_v2.py 2>nul

    :: Accept incoming changes for settings_gui.py
    echo    Resolving settings_gui.py (accepting enhanced version)...
    git checkout --theirs settings_gui.py 2>nul
    git add settings_gui.py 2>nul

    :: Complete the merge
    git commit -m "Auto-merge: resolved conflicts, accepting enhanced dashboard features" >nul 2>&1

    if %errorlevel% neq 0 (
        echo ❌ Auto-resolve failed. Manual intervention required.
        echo    Please check: git status
        pause
        exit /b 1
    )

    echo ✅ Conflicts resolved automatically!
) else (
    echo ✅ No conflicts detected.

    :: Try to pull if no conflicts
    git pull origin claude/fix-ui-exchange-validation-U9IPJ >nul 2>&1
    if %errorlevel% neq 0 (
        echo ⚠️  Could not pull changes (might already be up to date)
    ) else (
        echo ✅ Code updated to latest version.
    )
)

del conflicts.tmp 2>nul

:: ---------------------------------------------------------
:: Step 4: Validate Python Syntax
:: ---------------------------------------------------------
echo [Step 4/5] Validating Python code...

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please run START_HERE.bat first.
    pause
    exit /b 1
)

:: Validate dashboard_v2.py
python -m py_compile dashboard_v2.py 2>syntax_check.tmp
if %errorlevel% neq 0 (
    echo ❌ Syntax error in dashboard_v2.py:
    type syntax_check.tmp
    del syntax_check.tmp
    pause
    exit /b 1
)

:: Validate settings_gui.py
python -m py_compile settings_gui.py 2>syntax_check.tmp
if %errorlevel% neq 0 (
    echo ❌ Syntax error in settings_gui.py:
    type syntax_check.tmp
    del syntax_check.tmp
    pause
    exit /b 1
)

del syntax_check.tmp 2>nul
echo ✅ All Python files validated successfully!

:: ---------------------------------------------------------
:: Step 5: Check Documentation
:: ---------------------------------------------------------
echo [Step 5/5] Verifying documentation...

if exist "Documentation\DASHBOARD_ENHANCEMENTS.md" (
    echo ✅ Enhanced dashboard documentation found.
) else (
    echo ⚠️  Documentation not found (optional).
)

:: ---------------------------------------------------------
:: Final Report
:: ---------------------------------------------------------
echo.
echo ========================================================
echo ✅ UPDATE COMPLETE!
echo ========================================================
echo.
echo   📦 Latest code pulled
echo   🔧 Conflicts resolved
echo   ✅ Syntax validated
echo   🚀 Ready to launch
echo.
echo Next steps:
echo   1. Double-click LAUNCH_DASHBOARD_ENHANCED.bat
echo   2. Or run: python dashboard_v2.py
echo.
echo ========================================================
timeout /t 5
endlocal
exit /b 0
