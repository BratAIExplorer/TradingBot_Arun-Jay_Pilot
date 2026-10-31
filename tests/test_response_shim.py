"""
Test FakeResponse shim - ORDER RESPONSE NORMALIZATION (Phase 2).

FakeResponse mimics requests.Response so IBKR place_order returns can be
parsed by the same attempt_place_order() code as mStock (zero regression).
"""

import pytest


class TestFakeResponse:
    """FakeResponse duck-types requests.Response."""

    def test_fake_response_with_success_status(self):
        """FakeResponse returns 200 status with success payload."""
        from brokers._response_shim import FakeResponse

        response = FakeResponse(status_code=200, payload=[{"status": "success"}])

        assert response.status_code == 200
        assert response.json() == [{"status": "success"}]

    def test_fake_response_with_error_status(self):
        """FakeResponse returns error status with error payload."""
        from brokers._response_shim import FakeResponse

        response = FakeResponse(
            status_code=400,
            payload=[{"status": "error", "message": "Order rejected"}],
        )

        assert response.status_code == 400
        assert response.json() == [{"status": "error", "message": "Order rejected"}]

    def test_fake_response_text_property(self):
        """FakeResponse has .text property for error logging."""
        from brokers._response_shim import FakeResponse

        response = FakeResponse(
            status_code=500, payload=[], text_override="Internal Server Error"
        )

        assert response.text == "Internal Server Error"

    def test_fake_response_compatible_with_place_order_parsing(self):
        """FakeResponse parses like requests.Response in attempt_place_order."""
        from brokers._response_shim import FakeResponse

        # Simulate mStock success response shape
        response = FakeResponse(
            status_code=200, payload=[{"status": "success", "data": {"order_id": 12345}}]
        )

        # This is the code path from attempt_place_order (kickstart.py:2647-2656)
        try:
            payload = response.json()
            assert isinstance(payload, list)
            assert payload[0].get("status") == "success"
            assert payload[0]["data"]["order_id"] == 12345
        except Exception as e:
            pytest.fail(f"FakeResponse failed parsing: {e}")

    def test_fake_response_error_parsing(self):
        """FakeResponse error payload parses like requests.Response."""
        from brokers._response_shim import FakeResponse

        response = FakeResponse(
            status_code=400,
            payload=[{"status": "error", "message": "Invalid quantity"}],
            text_override="Bad Request: Invalid quantity",
        )

        assert response.status_code == 400
        assert response.text == "Bad Request: Invalid quantity"
        payload = response.json()
        assert payload[0].get("status") == "error"
