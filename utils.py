"""
Utilities for ARUN Trading Bot
Retry logic, decorators, and helpers
"""

import time
import logging
from functools import wraps
from typing import Callable, Any

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for retrying failed operations with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay on each retry
    
    Usage:
        @retry_on_failure(max_retries=3, delay=2)
        def fetch_data():
            # API call that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries - 1:
                        # Final attempt failed
                        logging.error(f"❌ {func.__name__} failed after {max_retries} attempts: {e}")
                        raise
                    
                    wait_time = delay * (backoff ** attempt)
                    logging.warning(
                        f"⚠️ {func.__name__} attempt {attempt+1}/{max_retries} failed: {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
            
            # Should never reach here
            raise last_exception
        
        return wrapper
    return decorator


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safe division that returns default instead of raising ZeroDivisionError
    """
    try:
        return numerator / denominator if denominator != 0 else default
    except:
        return default


def safe_get(dictionary: dict, key: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary values
    
    Usage:
        safe_get(data, 'response.data.price', default=0)
    """
    keys = key.split('.')
    value = dictionary
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


def format_inr(amount: float) -> str:
    """
    Format amount as Indian Rupees
    """
    return f"₹{amount:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format as percentage with sign
    """
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{decimals}f}%"


if __name__ == "__main__":
    # Test retry logic
    attempt_count = 0
    
    @retry_on_failure(max_retries=3, delay=0.5)
    def flaky_function():
        global attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError(f"Attempt {attempt_count} failed")
        return "Success!"
    
    result = flaky_function()
    print(f"Result: {result}")
    print(f"Took {attempt_count} attempts")
