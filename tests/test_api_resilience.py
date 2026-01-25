import pytest
from unittest.mock import Mock, patch
from kickstart import validate_api_response, safe_request

def test_validate_api_response_success():
    """
    QA Perspective: Verify validator accepts correct formats.
    """
    valid_resp = {"status": "success", "data": {"key": "value"}}
    assert validate_api_response(valid_resp, "Test", required_keys=["data.key"]) is True

def test_validate_api_response_error_status():
    """
    QA Perspective: Verify validator detects explicit error status from API.
    """
    error_resp = {"status": "error", "message": "Rate limit exceeded"}
    assert validate_api_response(error_resp, "Test") is False

def test_validate_api_response_missing_key():
    """
    QA Perspective: Verify validator detects missing required fields (preventing KeyError later).
    """
    incomplete_resp = {"status": "success", "not_data": {}}
    assert validate_api_response(incomplete_resp, "Test", required_keys=["data"]) is False

def test_validate_api_response_not_dict():
    """
    QA Perspective: Handle the 'totally unexpected' return type.
    """
    assert validate_api_response("Internal Server Error", "Test") is False
    assert validate_api_response(None, "Test") is False

@patch('requests.request')
def test_safe_request_timeout(mock_req):
    """
    QA Perspective: Ensure requests don't hang indefinitely on slow connections.
    """
    import requests
    mock_req.side_effect = requests.exceptions.Timeout("Slow network")
    
    # safe_request should catch the timeout and return None (not crash)
    result = safe_request("GET", "https://api.test.com")
    assert result is None

@patch('requests.request')
def test_safe_request_connection_error(mock_req):
    """
    QA Perspective: Handle DNS or network cable issues gracefully.
    """
    import requests
    mock_req.side_effect = requests.exceptions.ConnectionError("Offline")
    
    result = safe_request("GET", "https://api.test.com")
    assert result is None
