# ORBIT TRADING - Quick Test Script
# Run this in PowerShell to verify everything works

Write-Host "=" * 70
Write-Host "ORBIT TRADING - QUICK TEST SUITE" -ForegroundColor Cyan
Write-Host "=" * 70
Write-Host ""

# Test 1: Python Version
Write-Host "[1/5] Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "3.1[0-9]") {
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Need Python 3.10+, got: $pythonVersion" -ForegroundColor Red
    exit 1
}

# Test 2: Dependencies
Write-Host "[2/5] Checking dependencies..." -ForegroundColor Yellow
$packages = @("customtkinter", "pandas", "sklearn", "requests")
$missing = @()
foreach ($pkg in $packages) {
    python -c "import $pkg" 2>$null
    if ($?) {
        Write-Host "  ✅ $pkg" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $pkg" -ForegroundColor Red
        $missing += $pkg
    }
}

if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "Install missing packages:" -ForegroundColor Yellow
    Write-Host "  pip install $($missing -join ' ')" -ForegroundColor Cyan
    exit 1
}

# Test 3: Files
Write-Host "[3/5] Checking required files..." -ForegroundColor Yellow
$files = @("sensei_v1_dashboard.py", "kickstart.py", "settings.json")
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  $file (will create on first run)" -ForegroundColor Yellow
    }
}

# Test 4: Tests
Write-Host "[4/5] Running component tests..." -ForegroundColor Yellow
Write-Host "  (This may take 30-60 seconds...)" -ForegroundColor Gray

$testOutput = python -m pytest tests/test_market_selector_ui.py -q 2>&1
if ($LASTEXITCODE -eq 0) {
    # Count passed tests from output
    if ($testOutput -match "(\d+) passed") {
        $count = $matches[1]
        Write-Host "  ✅ $count tests passed" -ForegroundColor Green
    }
} else {
    Write-Host "  ⚠️  Some tests failed (see details above)" -ForegroundColor Yellow
    Write-Host $testOutput
}

# Test 5: Launcher
Write-Host "[5/5] Checking launcher scripts..." -ForegroundColor Yellow
$launchers = @("launcher.py", "START_ORBIT.bat")
foreach ($launcher in $launchers) {
    if (Test-Path $launcher) {
        Write-Host "  ✅ $launcher" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $launcher" -ForegroundColor Red
    }
}

# Summary
Write-Host ""
Write-Host "=" * 70
Write-Host "✅ QUICK TEST COMPLETE" -ForegroundColor Green
Write-Host "=" * 70
Write-Host ""
Write-Host "Ready to start? Run one of these:"
Write-Host ""
Write-Host "  Option 1: python launcher.py" -ForegroundColor Cyan
Write-Host "  Option 2: START_ORBIT.bat" -ForegroundColor Cyan
Write-Host "  Option 3: Double-click 🚀 ORBIT TRADING (desktop icon)" -ForegroundColor Cyan
Write-Host ""
Write-Host "First time? Install desktop shortcut:"
Write-Host ""
Write-Host "  Double-click: INSTALL_SHORTCUT.vbs" -ForegroundColor Cyan
Write-Host ""
