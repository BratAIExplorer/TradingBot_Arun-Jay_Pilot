"""
UI Logger - Simple logging utility for dashboard UI
Provides colored console output and log section markers.
"""

import sys
from datetime import datetime


class UILogger:
    """Simple logger for UI components with colored output"""
    
    @staticmethod
    def log_section(message: str):
        """Log a section header"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n{'='*60}")
        print(f"[{timestamp}] {message}")
        print(f"{'='*60}")
    
    @staticmethod
    def log_component_start(component_name: str):
        """Log component initialization start"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🔄 Initializing {component_name}...")
    
    @staticmethod
    def log_component_success(component_name: str):
        """Log successful component initialization"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ✅ {component_name} loaded successfully")
    
    @staticmethod
    def log_component_error(component_name: str, error: Exception):
        """Log component initialization error"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ❌ {component_name} failed: {error}")
    
    @staticmethod
    def log_info(message: str):
        """Log info message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ℹ️  {message}")
    
    @staticmethod
    def log_warning(message: str):
        """Log warning message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ⚠️  {message}")
    
    @staticmethod
    def log_error(message: str):
        """Log error message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ❌ {message}")
    
    @staticmethod
    def log_success(message: str):
        """Log success message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ✅ {message}")


# Backward compatibility - if imported elsewhere
def log_section(message: str):
    UILogger.log_section(message)

def log_component_start(component_name: str):
    UILogger.log_component_start(component_name)

def log_component_success(component_name: str):
    UILogger.log_component_success(component_name)

def log_component_error(component_name: str, error: Exception):
    UILogger.log_component_error(component_name, error)
