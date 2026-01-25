import pytest
import threading
import time
from unittest.mock import patch, MagicMock
from kickstart import (
    is_stop_requested, set_stop_requested, 
    is_offline, mark_offline_once, mark_online_if_needed,
    get_offline_since
)

def test_stop_request_thread_safety():
    """
    QA Perspective: Verify that STOP_REQUESTED can be toggled safely by multiple threads.
    PO Perspective: Ensure the 'Stop' button reliably stops the trading loop.
    """
    # Reset state
    set_stop_requested(False)
    assert is_stop_requested() is False
    
    def toggler():
        for _ in range(100):
            set_stop_requested(True)
            assert is_stop_requested() is True
            set_stop_requested(False)
            assert is_stop_requested() is False

    threads = [threading.Thread(target=toggler) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    assert is_stop_requested() is False

def test_offline_status_thread_safety():
    """
    QA Perspective: Verify that connectivity status doesn't cause race conditions.
    """
    mark_online_if_needed()
    assert is_offline() is False
    
    def flapper():
        for _ in range(50):
            mark_offline_once()
            assert is_offline() is True
            mark_online_if_needed()
            assert is_offline() is False

    threads = [threading.Thread(target=flapper) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    assert is_offline() is False

def test_offline_since_timestamp():
    """
    QA Perspective: Verify that 'since' timestamp is correctly set and retrieved.
    """
    mark_online_if_needed()
    assert get_offline_since() is None
    
    mark_offline_once()
    since = get_offline_since()
    assert since is not None
    
    mark_online_if_needed()
    assert get_offline_since() is None
