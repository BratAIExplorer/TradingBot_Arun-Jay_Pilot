#!/usr/bin/env python
"""
ORBIT TRADING LAUNCHER
Quick-start script to launch the dashboard
"""

import os
import sys
import subprocess
import time
from pathlib import Path
import io

# Fix encoding for Windows console (emoji support)
if sys.platform == 'win32':
    # Redirect stdout to UTF-8 for emoji support
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_environment():
    """Verify all dependencies are available"""
    print("🔍 Checking environment...")

    required_packages = {
        'customtkinter': 'UI framework',
        'pandas': 'Data analysis',
        'requests': 'HTTP requests',
        'sklearn': 'Machine learning',
        'pyotp': 'Two-factor auth',
    }

    missing = []
    for package, desc in required_packages.items():
        try:
            __import__(package)
            print(f"  ✅ {package:20} ({desc})")
        except ImportError:
            print(f"  ❌ {package:20} ({desc}) - MISSING")
            missing.append(package)

    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print(f"\nInstall with:")
        print(f"  pip install {' '.join(missing)}")
        return False

    print("\n✅ All dependencies available!\n")
    return True

def check_files():
    """Verify required files exist"""
    print("📁 Checking files...")

    required_files = {
        'sensei_v1_dashboard.py': 'Main dashboard',
        'kickstart.py': 'Trading engine',
        'settings.json': 'Configuration',
        'database/trades.db': 'Database',
    }

    missing = []
    for filepath, desc in required_files.items():
        full_path = PROJECT_ROOT / filepath
        if full_path.exists():
            print(f"  ✅ {filepath:35} ({desc})")
        else:
            print(f"  ⚠️  {filepath:35} ({desc}) - Not found")
            if filepath == 'settings.json':
                print(f"     → Will use settings_default.json")
            elif 'database' in filepath:
                print(f"     → Will create on first run")

    print()
    return True

def main():
    """Launch the dashboard"""
    os.chdir(PROJECT_ROOT)

    print("=" * 70)
    print("🚀 ORBIT TRADING LAUNCHER")
    print("=" * 70)
    print()

    # Check environment
    if not check_environment():
        sys.exit(1)

    # Check files
    check_files()

    print("🎯 Starting dashboard...")
    print("-" * 70)

    try:
        # Launch dashboard
        result = subprocess.run(
            [sys.executable, 'sensei_v1_dashboard.py'],
            cwd=str(PROJECT_ROOT)
        )
        sys.exit(result.returncode)

    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
