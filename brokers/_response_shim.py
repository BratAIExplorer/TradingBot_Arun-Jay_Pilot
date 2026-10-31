"""
FakeResponse shim - normalizes order responses across brokers.

Both mStock (requests.Response) and IBKR return order responses with the same
shape so attempt_place_order() can parse them identically. Zero changes to
kickstart.py's place_order parsing logic.

This is Phase 2's critical "regression safety shim" — IBKR responses are
wrapped in FakeResponse so the existing code path stays 100% unchanged.
"""

from typing import Any, List, Dict, Optional


class FakeResponse:
    """
    Duck-types requests.Response for order-response compatibility.

    Used by IBKRBroker.place_order() to return a shape compatible with
    the existing mStock parsing code in kickstart.py:attempt_place_order().

    Attributes:
        status_code: HTTP status (200, 400, 500, etc.)
        payload: List of dicts matching mStock response shape
        text_override: Optional error text (for logging)
    """

    def __init__(
        self,
        status_code: int,
        payload: List[Dict[str, Any]],
        text_override: Optional[str] = None,
    ):
        """
        Initialize FakeResponse.

        Args:
            status_code: HTTP-like status code (200=success, 400=client error, etc.)
            payload: List of response dicts, each with 'status' key
                     Expected shape: [{"status": "success"|"error", "message": "...", ...}]
            text_override: Optional text representation (for error logging)
        """
        self.status_code = status_code
        self._payload = payload
        self.text = text_override or self._default_text()

    def json(self) -> List[Dict[str, Any]]:
        """Return payload (mimics requests.Response.json())."""
        return self._payload

    def _default_text(self) -> str:
        """Generate default .text from payload."""
        if not self._payload:
            return f"Status {self.status_code}"

        first = self._payload[0]
        status = first.get("status", "unknown")
        message = first.get("message", "")

        if message:
            return f"{status.upper()}: {message}"
        return status.upper()

    def __repr__(self) -> str:
        return f"FakeResponse(status_code={self.status_code}, text={self.text!r})"
