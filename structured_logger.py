"""
Structured Logging Module for ARUN Trading Bot
Provides JSON-formatted logs with rotation for production use
"""

import logging
import logging.handlers
import json
import os
from datetime import datetime
from typing import Optional
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON for easy parsing
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data
            
        return json.dumps(log_data)


class StructuredLogger:
    """
    Production-ready structured logger with:
    - JSON formatting for log aggregation
    - File rotation (7 days retention)
    - Console output for development
    - Multiple log levels
    """
    
    def __init__(
        self, 
        name: str = "arun",
        log_dir: str = "logs",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB per file
        backup_count: int = 7,  # Keep 7 rotated files
        console_output: bool = True
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []  # Clear existing handlers
        
        # Create log directory
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # JSON file handler with rotation
        json_handler = logging.handlers.RotatingFileHandler(
            log_path / f"{name}.json.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        json_handler.setFormatter(JSONFormatter())
        json_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(json_handler)
        
        # Human-readable file handler
        text_handler = logging.handlers.RotatingFileHandler(
            log_path / f"{name}.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        text_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s"
        )
        text_handler.setFormatter(text_formatter)
        text_handler.setLevel(logging.INFO)
        self.logger.addHandler(text_handler)
        
        # Console handler (for development)
        if console_output:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s",
                datefmt="%H:%M:%S"
            )
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(logging.INFO)
            self.logger.addHandler(console_handler)
    
    def debug(self, msg: str, **kwargs):
        """Log debug message with optional extra data"""
        self._log(logging.DEBUG, msg, kwargs)
    
    def info(self, msg: str, **kwargs):
        """Log info message with optional extra data"""
        self._log(logging.INFO, msg, kwargs)
    
    def warning(self, msg: str, **kwargs):
        """Log warning message with optional extra data"""
        self._log(logging.WARNING, msg, kwargs)
    
    def error(self, msg: str, **kwargs):
        """Log error message with optional extra data"""
        self._log(logging.ERROR, msg, kwargs)
    
    def critical(self, msg: str, **kwargs):
        """Log critical message with optional extra data"""
        self._log(logging.CRITICAL, msg, kwargs)
    
    def _log(self, level: int, msg: str, extra_data: dict):
        """Internal log method that attaches extra data"""
        extra = {}
        if extra_data:
            extra["extra_data"] = extra_data
        self.logger.log(level, msg, extra=extra)
    
    def trade(self, symbol: str, action: str, quantity: int, price: float, **kwargs):
        """Specialized trade logging"""
        self.info(
            f"TRADE: {action} {quantity} {symbol} @ ₹{price:.2f}",
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            **kwargs
        )
    
    def risk_event(self, event_type: str, symbol: str, details: str, **kwargs):
        """Specialized risk event logging"""
        self.warning(
            f"RISK: {event_type} - {symbol} - {details}",
            event_type=event_type,
            symbol=symbol,
            **kwargs
        )
    
    def api_call(self, endpoint: str, method: str, status_code: int, duration_ms: float):
        """Log API calls for monitoring"""
        self.debug(
            f"API: {method} {endpoint} -> {status_code} ({duration_ms:.0f}ms)",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms
        )


# Global logger instance
logger = StructuredLogger()


# Convenience functions for direct import
def debug(msg: str, **kwargs): logger.debug(msg, **kwargs)
def info(msg: str, **kwargs): logger.info(msg, **kwargs)
def warning(msg: str, **kwargs): logger.warning(msg, **kwargs)
def error(msg: str, **kwargs): logger.error(msg, **kwargs)
def critical(msg: str, **kwargs): logger.critical(msg, **kwargs)


if __name__ == "__main__":
    # Test the logger
    print("Testing structured logger...")
    
    logger.info("Bot started", version="2.1.0", mode="paper")
    logger.trade("HDFCBANK", "BUY", 10, 1550.50)
    logger.risk_event("STOP_LOSS", "RELIANCE", "Down 5.2%")
    logger.debug("Fetching market data", symbols=["HDFCBANK", "TCS", "INFY"])
    logger.error("API connection failed", retries=3, error_code="TIMEOUT")
    
    print("Check logs/ directory for output files")
