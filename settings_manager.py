"""
Settings Manager for ARUN Trading Bot
Handles loading, saving, and validating settings.json
"""

import json
import os
from typing import Dict, Any
from pathlib import Path


class SettingsManager:
    """
    Manages bot settings with validation and defaults
    """
    
    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = settings_file
        self.settings = {}
        self.load()
    
    def load(self) -> Dict[str, Any]:
        """
        Load settings from JSON file
        Falls back to defaults if file doesn't exist
        """
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
                print(f"✅ Settings loaded from {self.settings_file}")
                return self.settings
            except json.JSONDecodeError as e:
                print(f"❌ Error reading settings: {e}")
                print("⚠️ Using default settings")
                return self._load_defaults()
        else:
            print(f"⚠️ Settings file not found: {self.settings_file}")
            print("📝 Loading defaults from settings_default.json")
            return self._load_defaults()
    
    def _load_defaults(self) -> Dict[str, Any]:
        """
        Load default settings from settings_default.json
        """
        default_file = "settings_default.json"
        if os.path.exists(default_file):
            with open(default_file, 'r') as f:
                self.settings = json.load(f)
            # Save as user's settings.json
            self.save()
            return self.settings
        else:
            raise FileNotFoundError(f"Neither {self.settings_file} nor {default_file} found!")
    
    def save(self) -> bool:
        """
        Save current settings to JSON file
        """
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            print(f"✅ Settings saved to {self.settings_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving settings: {e}")
            return False
    
    def get(self, key_path: str, default=None):
        """
        Get setting value using dot notation
        
        Example:
            settings.get('broker.name')  # Returns 'mstock'
            settings.get('capital.total_capital')  # Returns 50000
        """
        keys = key_path.split('.')
        value = self.settings
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        Set setting value using dot notation
        
        Example:
            settings.set('capital.total_capital', 100000)
        """
        keys = key_path.split('.')
        current = self.settings
        
        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
        return self.save()
    
    def validate(self) -> tuple[bool, list]:
        """
        Validate settings for required fields
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        # Check broker settings
        if not self.get('broker.name'):
            errors.append("Broker name not configured")
        
        # Check capital settings
        total_capital = self.get('capital.total_capital', 0)
        if total_capital <= 0:
            errors.append("Total capital must be > 0")
        
        # Check risk controls
        stop_loss = self.get('risk_controls.default_stop_loss_pct', 0)
        if stop_loss <= 0 or stop_loss > 50:
            errors.append("Stop loss must be between 0-50%")
        
        profit_target = self.get('risk_controls.default_profit_target_pct', 0)
        if profit_target <= 0:
            errors.append("Profit target must be > 0%")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def get_stock_configs(self) -> list:
        """
        Load stock configurations from CSV (backward compatibility)
        TODO: Migrate to settings.json
        """
        import pandas as pd
        
        if os.path.exists('config_table.csv'):
            df = pd.read_csv('config_table.csv')
            return df.to_dict('records')
        else:
            return []
    
    def get_capital_summary(self) -> Dict[str, float]:
        """
        Get capital summary for dashboard display
        """
        return {
            'total_capital': self.get('capital.total_capital', 0),
            'starting_capital': self.get('capital.starting_capital', 0),
            'max_per_stock_pct': self.get('capital.max_per_stock_value', 10),
            'daily_loss_limit_pct': self.get('capital.daily_loss_limit_pct', 10),
            'max_positions': self.get('capital.max_simultaneous_positions', 10)
        }
    
    def get_risk_settings(self) -> Dict[str, Any]:
        """
        Get risk control settings
        """
        return {
            'use_stop_loss': self.get('risk_controls.default_use_stop_loss', True),
            'stop_loss_pct': self.get('risk_controls.default_stop_loss_pct', 5),
            'use_profit_target': self.get('risk_controls.default_use_profit_target', True),
            'profit_target_pct': self.get('risk_controls.default_profit_target_pct', 10),
            'catastrophic_stop_enabled': self.get('risk_controls.catastrophic_stop_enabled', True),
            'catastrophic_stop_pct': self.get('risk_controls.catastrophic_stop_pct', 20)
        }


# Convenience instance
settings = SettingsManager()


if __name__ == "__main__":
    # Test settings manager
    print("\n=== Testing Settings Manager ===\n")
    
    # Load settings
    s = SettingsManager()
    
    # Display current settings
    print(f"Broker: {s.get('broker.name')}")
    print(f"Total Capital: ₹{s.get('capital.total_capital'):,}")
    print(f"Stop Loss: {s.get('risk_controls.default_stop_loss_pct')}%")
    print(f"Paper Trading: {s.get('app_settings.paper_trading_mode')}")
    
    # Validate
    is_valid, errors = s.validate()
    if is_valid:
        print("\n✅ Settings are valid!")
    else:
        print(f"\n❌ Validation errors: {errors}")
    
    # Get summaries
    print("\n--- Capital Summary ---")
    capital = s.get_capital_summary()
    for key, value in capital.items():
        print(f"{key}: {value}")
    
    print("\n--- Risk Settings ---")
    risk = s.get_risk_settings()
    for key, value in risk.items():
        print(f"{key}: {value}")
