"""
security — Orbit Trading credential management package.

Public exports:
    CredentialManager  — load, encrypt, rotate and access credentials
"""

from security.credential_manager import CredentialManager

__all__ = ["CredentialManager"]
