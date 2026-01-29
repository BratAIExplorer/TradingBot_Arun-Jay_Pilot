"""
Settings Manager for ARUN Trading Bot
Handles loading, saving, and validating settings.json
"""

import json
import os
from typing import Dict, Any
from pathlib import Path
from cryptography.fernet import Fernet
import base64


class SettingsManager:
    """
    Manages bot settings with validation and defaults
    """
    
    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = settings_file
        self.settings = {}
        self._encryption_key = self._get_or_create_encryption_key()
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
    
    def _get_or_create_encryption_key(self) -> bytes:
        """
        Get or create encryption key for sensitive data
        Stores key in .encryption_key file (should be added to .gitignore)
        """
        key_file = ".encryption_key"
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            print("🔐 New encryption key generated for sensitive data")
            return key
    
    def _encrypt_value(self, value: str) -> str:
        """
        Encrypt a string value
        """
        if not value:
            return ""
        fernet = Fernet(self._encryption_key)
        encrypted = fernet.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """
        Decrypt a string value
        Returns empty string if decryption fails
        """
        if not encrypted_value:
            return ""
        try:
            fernet = Fernet(self._encryption_key)
            encrypted_bytes = base64.b64decode(encrypted_value.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception:
            # If decryption fails, assume it's plain text (backward compatibility)
            return encrypted_value
    
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
        
        # Set the value (encrypt if sensitive field)
        if self._is_sensitive_field(key_path):
            current[keys[-1]] = self._encrypt_value(str(value))
        else:
            current[keys[-1]] = value
        return self.save()
    
    def _is_sensitive_field(self, key_path: str) -> bool:
        """
        Check if field should be encrypted
        """
        sensitive_patterns = ['api_key', 'api_secret', 'password', 'token']
        return any(pattern in key_path.lower() for pattern in sensitive_patterns)
    
    def get_decrypted(self, key_path: str, default=None):
        """
        Get setting value and decrypt if it's a sensitive field
        """
        value = self.get(key_path, default)
        if value and self._is_sensitive_field(key_path):
            return self._decrypt_value(str(value))
        return value
    
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
        Get stock configurations from settings.json
        Migrates from CSV if necessary
        """
        # Auto-migrate if stocks not in settings but CSV exists
        if 'stocks' not in self.settings and os.path.exists('config_table.csv'):
            self.migrate_stock_configs()
            
        return self.settings.get('stocks', [])

    def migrate_stock_configs(self):
        """
        Migrate stocks from config_table.csv to settings.json
        """
        import pandas as pd
        csv_path = 'config_table.csv'
        if not os.path.exists(csv_path):
            return

        try:
            df = pd.read_csv(csv_path)
            stocks = []
            for _, row in df.iterrows():
                stock = {
                    "symbol": str(row.get('Symbol', '')).upper(),
                    "exchange": str(row.get('Exchange', 'NSE')).upper(),
                    "enabled": str(row.get('Enabled', 'False')).lower() == 'true',
                    "strategy": row.get('Strategy', 'TRADE'),
                    "timeframe": row.get('Timeframe', '15T'),
                    "buy_rsi": int(row.get('Buy RSI', 30)),
                    "sell_rsi": int(row.get('Sell RSI', 70)),
                    "quantity": int(row.get('Quantity', 0)),
                    "profit_target_pct": float(row.get('Profit Target %', 1.0))
                }
                stocks.append(stock)
            
            self.settings['stocks'] = stocks
            self.save()
            print(f"✅ Migrated {len(stocks)} stocks from CSV to settings.json")
            
            # Optional: Rename CSV to avoid confusion, but keeping it for safety for now
            # os.rename(csv_path, csv_path + ".bak")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")

    def add_stock_config(self, stock_data: Dict[str, Any]) -> bool:
        """
        Add or update a stock configuration
        """
        stocks = self.get_stock_configs()
        
        # Remove existing if present (update mode)
        stocks = [s for s in stocks if not (s['symbol'] == stock_data['symbol'] and s['exchange'] == stock_data['exchange'])]
        
        stocks.append(stock_data)
        self.settings['stocks'] = stocks
        return self.save()

    def delete_stock_config(self, symbol: str, exchange: str) -> bool:
        """
        Delete a stock configuration
        """
        stocks = self.get_stock_configs()
        initial_count = len(stocks)
        
        stocks = [s for s in stocks if not (s['symbol'] == symbol and s['exchange'] == exchange)]
        
        if len(stocks) < initial_count:
            self.settings['stocks'] = stocks
            return self.save()
        return False
    
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
