"""
Shared constants for the ARUN Trading Bot.
Centralizes configuration data to avoid circular imports and duplication.
"""

# ---------------- Specialized Symbol Mapping ----------------
# Some REITs/InVITs are not recognized by the mStock OHLC API via scrip name.
# We map them to their numeric tokens from the Scrip Master.
REIT_TOKEN_MAP = {
    "EMBASSY": "9383",
    "BIRET": "2203",
    "MINDSPACE": "22308",
    "POWERGRID": "2209" # Example InvIT if needed
}
