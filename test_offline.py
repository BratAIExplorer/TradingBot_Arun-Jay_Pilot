from kickstart import settings, is_offline

print("Checking why get_positions() returns empty...")
print(f"1. Paper trading mode: {settings.get('app_settings.paper_trading_mode') if settings else 'NO SETTINGS'}")
print(f"2. is_offline(): {is_offline()}")
print(f"3. Settings object: {settings}")
