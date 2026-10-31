"""
security/credential_manager.py — Orbit Trading Secure Credential Manager

Design principles:
  SIMPLE  — Two clean accessor methods: get_mstock_config() / get_ibkr_config()
  SMART   — Env-agnostic: dev uses .env, prod uses Fernet-encrypted file
  SECURE  — 3-layer defence: env file → encrypted storage → memory-only access
  RESPECTFUL — Clear boundaries; never logs credential values

Supported environments:
  "development"  — reads a plaintext .env file (local dev only)
  "production"   — reads a Fernet-encrypted credential file

Usage (development):
    mgr = CredentialManager(env="development", env_file=".env")
    cfg = mgr.get_mstock_config()   # {"api_key": ..., "access_token": ...}

Usage (production):
    key = CredentialManager.generate_encryption_key()
    mgr = CredentialManager(
        env="production",
        encrypted_file="/secure/creds.enc",
        encryption_key=key,
    )
    cfg = mgr.get_ibkr_config()    # {"host": ..., "port": ..., "client_id": ...}
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import keyring
from cryptography.fernet import Fernet, InvalidToken
from dotenv import dotenv_values

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Required .env keys — KeyError raised at load time if any are absent.
# IBKR keys are optional (safe defaults are used when missing).
# ---------------------------------------------------------------------------
_REQUIRED_KEYS: tuple[str, ...] = (
    "MSTOCK_API_KEY",
    "MSTOCK_ACCESS_TOKEN",
)

_IBKR_DEFAULTS: dict[str, Any] = {
    "host": "127.0.0.1",
    "port": 7497,
    "client_id": 1,
}


class CredentialManager:
    """
    Secure credential manager for Orbit Trading.

    All credential values are held in a private dict (_credentials).
    No value ever appears in repr(), log messages, or stdout.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        *,
        env: str = "development",
        env_file: Optional[str] = None,
        encrypted_file: Optional[str] = None,
        encryption_key: Optional[bytes] = None,
    ) -> None:
        """
        Parameters
        ----------
        env:             "development" or "production"
        env_file:        Path to .env file (development mode)
        encrypted_file:  Path to Fernet-encrypted JSON blob (production mode)
        encryption_key:  Fernet key bytes (production mode)
        """
        if env not in ("development", "production"):
            raise ValueError(f"env must be 'development' or 'production', got {env!r}")

        self._env = env
        self._credentials: dict[str, str] = {}

        if env == "development":
            self._load_from_env_file(env_file or ".env")
        else:
            if not encrypted_file or not encryption_key:
                raise ValueError(
                    "production mode requires both encrypted_file and encryption_key"
                )
            self._load_from_encrypted_file(encrypted_file, encryption_key)

    # ------------------------------------------------------------------
    # Class-level helpers
    # ------------------------------------------------------------------

    @staticmethod
    def generate_encryption_key() -> bytes:
        """Return a fresh Fernet key (32 random bytes, URL-safe base64 encoded)."""
        return Fernet.generate_key()

    # ------------------------------------------------------------------
    # Dev mode — .env file
    # ------------------------------------------------------------------

    def _load_from_env_file(self, env_file: str) -> None:
        """Read a .env file and populate _credentials. Raises KeyError for missing keys."""
        raw: dict[str, Optional[str]] = dotenv_values(env_file)

        for key in _REQUIRED_KEYS:
            if key not in raw or not raw[key]:
                raise KeyError(key)

        # Store all non-None values; never log them
        self._credentials = {k: v for k, v in raw.items() if v is not None}
        logger.debug("Credentials loaded from env file (values redacted)")

    # ------------------------------------------------------------------
    # Production mode — Fernet-encrypted file
    # ------------------------------------------------------------------

    def _load_from_encrypted_file(self, encrypted_file: str, key: bytes) -> None:
        """Decrypt a Fernet-encrypted JSON credential file into _credentials."""
        path = Path(encrypted_file)
        if not path.exists():
            raise FileNotFoundError(f"Encrypted credential file not found: {encrypted_file}")

        cipher = Fernet(key)
        try:
            ciphertext = path.read_bytes()
            plaintext = cipher.decrypt(ciphertext)
        except InvalidToken as exc:
            raise InvalidToken("Decryption failed — wrong key or corrupted file") from exc

        data: dict[str, str] = json.loads(plaintext.decode("utf-8"))
        self._credentials = data
        logger.debug("Credentials loaded from encrypted file (values redacted)")

    # ------------------------------------------------------------------
    # Encryption helper
    # ------------------------------------------------------------------

    def _encrypt_and_save(self, encrypted_file: str, key: bytes) -> None:
        """Serialise _credentials to JSON, encrypt with Fernet, write to disk."""
        cipher = Fernet(key)
        plaintext = json.dumps(self._credentials).encode("utf-8")
        ciphertext = cipher.encrypt(plaintext)
        Path(encrypted_file).write_bytes(ciphertext)
        logger.debug("Credentials encrypted and saved (values redacted)")

    # ------------------------------------------------------------------
    # OS keyring helpers
    # ------------------------------------------------------------------

    def save_key_to_keyring(self, service: str, username: str, key: bytes) -> None:
        """Persist a Fernet key in the OS keyring."""
        keyring.set_password(service, username, key.decode())
        logger.debug("Encryption key saved to OS keyring (value redacted)")

    def load_key_from_keyring(self, service: str, username: str) -> bytes:
        """Retrieve a Fernet key from the OS keyring. Returns bytes."""
        value = keyring.get_password(service, username)
        if value is None:
            raise KeyError(f"No keyring entry for service={service!r}, username={username!r}")
        return value.encode()

    # ------------------------------------------------------------------
    # Config accessors
    # ------------------------------------------------------------------

    def get_mstock_config(self) -> dict[str, str]:
        """
        Return mStock broker configuration.

        Returns
        -------
        dict with keys:
            api_key       — MSTOCK_API_KEY
            access_token  — MSTOCK_ACCESS_TOKEN
        """
        return {
            "api_key": self._credentials.get("MSTOCK_API_KEY", ""),
            "access_token": self._credentials.get("MSTOCK_ACCESS_TOKEN", ""),
        }

    def get_ibkr_config(self) -> dict[str, Any]:
        """
        Return Interactive Brokers TWS/Gateway configuration.

        Returns
        -------
        dict with keys:
            host       — IBKR_HOST  (str, default "127.0.0.1")
            port       — IBKR_PORT  (int, default 7497)
            client_id  — IBKR_CLIENT_ID (int, default 1)
        """
        host = self._credentials.get("IBKR_HOST", _IBKR_DEFAULTS["host"])
        try:
            port = int(self._credentials.get("IBKR_PORT", _IBKR_DEFAULTS["port"]))
        except (ValueError, TypeError):
            port = _IBKR_DEFAULTS["port"]
        try:
            client_id = int(self._credentials.get("IBKR_CLIENT_ID", _IBKR_DEFAULTS["client_id"]))
        except (ValueError, TypeError):
            client_id = _IBKR_DEFAULTS["client_id"]

        return {"host": host, "port": port, "client_id": client_id}

    # ------------------------------------------------------------------
    # Rotation
    # ------------------------------------------------------------------

    def rotate_credentials(
        self,
        credential_key: str,
        new_value: str,
        encrypted_file: str,
        encryption_key: bytes,
    ) -> None:
        """
        Replace a single credential value in-memory and re-encrypt to disk.

        Parameters
        ----------
        credential_key   : The key name (e.g. "MSTOCK_API_KEY")
        new_value        : The replacement value
        encrypted_file   : Path to the encrypted credentials file
        encryption_key   : Fernet key used for encryption
        """
        # Immutable update: build a new dict rather than mutating in-place
        self._credentials = {**self._credentials, credential_key: new_value}
        self._encrypt_and_save(encrypted_file, encryption_key)
        logger.debug("Credential %r rotated and re-encrypted (value redacted)", credential_key)

    # ------------------------------------------------------------------
    # Memory cleanup
    # ------------------------------------------------------------------

    def __del__(self) -> None:
        """Zero out the in-memory credential store on garbage collection."""
        self._credentials = {}

    # ------------------------------------------------------------------
    # Safe repr — never expose credential values
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        keys = list(self._credentials.keys())
        return f"CredentialManager(env={self._env!r}, loaded_keys={keys})"
