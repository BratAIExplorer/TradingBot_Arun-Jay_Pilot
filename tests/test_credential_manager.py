"""
TDD tests for security/credential_manager.py (Orbit Trading)

RED phase: All tests written BEFORE implementation.
These tests define the exact contract CredentialManager must fulfil.

Test groups:
  1. Development mode — load from .env file
  2. Production mode — Fernet encryption + OS keyring
  3. Config accessors — get_mstock_config / get_ibkr_config
  4. Rotation — rotate_credentials re-encrypts
  5. Security — credentials never appear in logs/stdout
"""

import os
import json
import tempfile
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    """Create a temporary .env file with all required keys."""
    env = tmp_path / ".env"
    env.write_text(
        "MSTOCK_API_KEY=test_api_key_12345\n"
        "MSTOCK_ACCESS_TOKEN=test_access_token_99\n"
        "IBKR_HOST=127.0.0.1\n"
        "IBKR_PORT=7497\n"
        "IBKR_CLIENT_ID=1\n"
    )
    return env


@pytest.fixture()
def minimal_env_file(tmp_path: Path) -> Path:
    """Only mStock keys, no IBKR — tests partial config."""
    env = tmp_path / ".env"
    env.write_text(
        "MSTOCK_API_KEY=only_mstock_key\n"
        "MSTOCK_ACCESS_TOKEN=only_mstock_token\n"
    )
    return env


@pytest.fixture()
def missing_key_env_file(tmp_path: Path) -> Path:
    """Missing MSTOCK_ACCESS_TOKEN — should raise on load."""
    env = tmp_path / ".env"
    env.write_text("MSTOCK_API_KEY=has_key_but_no_token\n")
    return env


@pytest.fixture()
def credential_dir(tmp_path: Path) -> Path:
    """Empty temp directory for encrypted credential storage."""
    creds_dir = tmp_path / "credentials"
    creds_dir.mkdir()
    return creds_dir


# ---------------------------------------------------------------------------
# Helper: import the module under test
# We use a lazy import so RED tests can be collected even when the module
# does not yet exist (collection will succeed; instantiation will fail).
# ---------------------------------------------------------------------------

def _import_cm():
    from security.credential_manager import CredentialManager
    return CredentialManager


# ===========================================================================
# GROUP 1: Development mode — load from .env file
# ===========================================================================

class TestDevModeLoad:
    """Tests 1-6: load from .env and parse correctly."""

    def test_load_from_env_file(self, env_file: Path) -> None:
        """Test 1 — CredentialManager reads a .env file without raising."""
        CredentialManager = _import_cm()
        mgr = CredentialManager(env="development", env_file=str(env_file))
        # If it doesn't raise, loading succeeded
        assert mgr is not None

    def test_parses_mstock_api_key(self, env_file: Path) -> None:
        """Test 2 — MSTOCK_API_KEY is parsed correctly."""
        CredentialManager = _import_cm()
        mgr = CredentialManager(env="development", env_file=str(env_file))
        assert mgr.get_mstock_config()["api_key"] == "test_api_key_12345"

    def test_parses_mstock_access_token(self, env_file: Path) -> None:
        """Test 3 — MSTOCK_ACCESS_TOKEN is parsed correctly."""
        CredentialManager = _import_cm()
        mgr = CredentialManager(env="development", env_file=str(env_file))
        assert mgr.get_mstock_config()["access_token"] == "test_access_token_99"

    def test_parses_ibkr_host_port_client_id(self, env_file: Path) -> None:
        """Test 4 — IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID are parsed."""
        CredentialManager = _import_cm()
        mgr = CredentialManager(env="development", env_file=str(env_file))
        cfg = mgr.get_ibkr_config()
        assert cfg["host"] == "127.0.0.1"
        assert cfg["port"] == 7497
        assert cfg["client_id"] == 1

    def test_raises_if_required_key_missing(self, missing_key_env_file: Path) -> None:
        """Test 5 — KeyError raised when a required key is absent."""
        CredentialManager = _import_cm()
        with pytest.raises(KeyError, match="MSTOCK_ACCESS_TOKEN"):
            CredentialManager(env="development", env_file=str(missing_key_env_file))

    def test_credentials_stored_in_memory_after_load(self, env_file: Path) -> None:
        """Test 6 — After load, credentials are accessible from memory (no re-read)."""
        CredentialManager = _import_cm()
        mgr = CredentialManager(env="development", env_file=str(env_file))
        # Delete the file — credentials must still be accessible from memory
        env_file.unlink()
        assert mgr.get_mstock_config()["api_key"] == "test_api_key_12345"


# ===========================================================================
# GROUP 2: Production mode — encryption + OS keyring
# ===========================================================================

class TestProductionMode:
    """Tests 7-12: Fernet encryption and OS keyring integration."""

    def test_generate_encryption_key(self, credential_dir: Path) -> None:
        """Test 7 — generate_encryption_key() returns a valid Fernet key."""
        CredentialManager = _import_cm()
        key = CredentialManager.generate_encryption_key()
        # Fernet keys are 44-character URL-safe base64 strings
        from cryptography.fernet import Fernet
        # Should not raise — key must be usable
        f = Fernet(key)
        assert f is not None

    def test_encrypt_credentials_to_file(self, env_file: Path, credential_dir: Path) -> None:
        """Test 8 — _encrypt_and_save() writes an encrypted file."""
        CredentialManager = _import_cm()
        key = CredentialManager.generate_encryption_key()
        cred_file = credential_dir / "creds.enc"

        mgr = CredentialManager(
            env="development", env_file=str(env_file)
        )
        mgr._encrypt_and_save(str(cred_file), key)

        assert cred_file.exists()
        assert cred_file.stat().st_size > 0

    def test_decrypt_credentials_from_file(self, env_file: Path, credential_dir: Path) -> None:
        """Test 9 — production mode can decrypt what was encrypted."""
        CredentialManager = _import_cm()
        key = CredentialManager.generate_encryption_key()
        cred_file = credential_dir / "creds.enc"

        # Encrypt using dev-mode manager
        dev_mgr = CredentialManager(env="development", env_file=str(env_file))
        dev_mgr._encrypt_and_save(str(cred_file), key)

        # Load using production-mode manager
        prod_mgr = CredentialManager(
            env="production",
            encrypted_file=str(cred_file),
            encryption_key=key,
        )
        assert prod_mgr.get_mstock_config()["api_key"] == "test_api_key_12345"

    def test_os_keyring_set_and_get(self, env_file: Path) -> None:
        """Test 10 — keyring.set_password / get_password called during key storage."""
        CredentialManager = _import_cm()
        key = CredentialManager.generate_encryption_key()

        with patch("keyring.set_password") as mock_set, \
             patch("keyring.get_password", return_value=key.decode()) as mock_get:

            mgr = CredentialManager(env="development", env_file=str(env_file))
            mgr.save_key_to_keyring("orbit_trading", "encryption_key", key)

            retrieved = mgr.load_key_from_keyring("orbit_trading", "encryption_key")

        mock_set.assert_called_once_with("orbit_trading", "encryption_key", key.decode())
        mock_get.assert_called_once_with("orbit_trading", "encryption_key")
        assert retrieved == key

    def test_encrypted_file_unreadable_without_key(self, env_file: Path, credential_dir: Path) -> None:
        """Test 11 — decrypting with the wrong key raises an error."""
        from cryptography.fernet import InvalidToken
        CredentialManager = _import_cm()

        good_key = CredentialManager.generate_encryption_key()
        bad_key = CredentialManager.generate_encryption_key()
        cred_file = credential_dir / "creds.enc"

        dev_mgr = CredentialManager(env="development", env_file=str(env_file))
        dev_mgr._encrypt_and_save(str(cred_file), good_key)

        with pytest.raises((InvalidToken, ValueError, Exception)):
            CredentialManager(
                env="production",
                encrypted_file=str(cred_file),
                encryption_key=bad_key,
            )

    def test_credentials_cleared_on_del(self, env_file: Path) -> None:
        """Test 12 — __del__ zeroes / clears the in-memory credential store."""
        CredentialManager = _import_cm()
        mgr = CredentialManager(env="development", env_file=str(env_file))
        # Verify credentials are present
        assert mgr.get_mstock_config()["api_key"] != ""
        # Trigger cleanup
        mgr.__del__()
        # After cleanup, internal store should be empty / cleared
        assert mgr._credentials == {}


# ===========================================================================
# GROUP 3: Config accessor methods
# ===========================================================================

class TestConfigAccessors:
    """Tests 13-14: get_mstock_config and get_ibkr_config return correct shapes."""

    def test_get_mstock_config_returns_dict_with_api_key(self, env_file: Path) -> None:
        """Test 13 — get_mstock_config() dict has 'api_key' and 'access_token'."""
        CredentialManager = _import_cm()
        mgr = CredentialManager(env="development", env_file=str(env_file))
        cfg = mgr.get_mstock_config()

        assert isinstance(cfg, dict)
        assert "api_key" in cfg
        assert "access_token" in cfg
        assert cfg["api_key"] == "test_api_key_12345"
        assert cfg["access_token"] == "test_access_token_99"

    def test_get_ibkr_config_returns_dict_with_host_port(self, env_file: Path) -> None:
        """Test 14 — get_ibkr_config() dict has host (str), port (int), client_id (int)."""
        CredentialManager = _import_cm()
        mgr = CredentialManager(env="development", env_file=str(env_file))
        cfg = mgr.get_ibkr_config()

        assert isinstance(cfg, dict)
        assert cfg["host"] == "127.0.0.1"
        assert isinstance(cfg["port"], int)
        assert isinstance(cfg["client_id"], int)

    def test_get_ibkr_config_defaults_when_keys_absent(self, minimal_env_file: Path) -> None:
        """Test 14b — get_ibkr_config() returns safe defaults when IBKR keys not in .env."""
        CredentialManager = _import_cm()
        mgr = CredentialManager(env="development", env_file=str(minimal_env_file))
        cfg = mgr.get_ibkr_config()
        # Should not raise; should return dict with sensible defaults
        assert isinstance(cfg, dict)
        assert "host" in cfg
        assert "port" in cfg


# ===========================================================================
# GROUP 4: rotate_credentials
# ===========================================================================

class TestRotateCredentials:
    """Test 15 — rotate_credentials updates the credential and re-encrypts."""

    def test_rotate_credentials_updates_and_re_encrypts(
        self, env_file: Path, credential_dir: Path
    ) -> None:
        """Test 15 — rotate_credentials() replaces a key and persists to encrypted file."""
        CredentialManager = _import_cm()
        key = CredentialManager.generate_encryption_key()
        cred_file = credential_dir / "creds.enc"

        mgr = CredentialManager(env="development", env_file=str(env_file))
        mgr._encrypt_and_save(str(cred_file), key)

        # Rotate the mstock API key
        mgr.rotate_credentials("MSTOCK_API_KEY", "brand_new_key_xyz", str(cred_file), key)

        # In-memory value is updated immediately
        assert mgr.get_mstock_config()["api_key"] == "brand_new_key_xyz"

        # Re-load from encrypted file to confirm persistence
        reloaded = CredentialManager(
            env="production",
            encrypted_file=str(cred_file),
            encryption_key=key,
        )
        assert reloaded.get_mstock_config()["api_key"] == "brand_new_key_xyz"


# ===========================================================================
# GROUP 5: Security — credentials NEVER appear in logs or stdout
# ===========================================================================

class TestNoCredentialLeakage:
    """Test 16 — credentials must never appear in captured output or log records."""

    def test_credentials_not_logged_to_stdout(
        self, env_file: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test 16a — no credential values printed to stdout/stderr during load."""
        CredentialManager = _import_cm()
        mgr = CredentialManager(env="development", env_file=str(env_file))
        _ = mgr.get_mstock_config()
        _ = mgr.get_ibkr_config()

        captured = capsys.readouterr()
        assert "test_api_key_12345" not in captured.out
        assert "test_api_key_12345" not in captured.err
        assert "test_access_token_99" not in captured.out
        assert "test_access_token_99" not in captured.err

    def test_credentials_not_in_log_records(
        self, env_file: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test 16b — no credential values emitted to the logging system."""
        CredentialManager = _import_cm()
        with caplog.at_level(logging.DEBUG):
            mgr = CredentialManager(env="development", env_file=str(env_file))
            _ = mgr.get_mstock_config()
            _ = mgr.get_ibkr_config()

        full_log = caplog.text
        assert "test_api_key_12345" not in full_log
        assert "test_access_token_99" not in full_log

    def test_repr_does_not_expose_credentials(self, env_file: Path) -> None:
        """Test 16c — repr() / str() of the manager redacts credential values."""
        CredentialManager = _import_cm()
        mgr = CredentialManager(env="development", env_file=str(env_file))
        representation = repr(mgr)
        assert "test_api_key_12345" not in representation
        assert "test_access_token_99" not in representation


# ===========================================================================
# GROUP 6: Edge-case / error-path coverage
# ===========================================================================

class TestEdgeCases:
    """Cover remaining error branches for 95%+ coverage."""

    def test_invalid_env_raises_value_error(self, env_file: Path) -> None:
        """Unknown env string must raise ValueError immediately."""
        CredentialManager = _import_cm()
        with pytest.raises(ValueError, match="development.*production"):
            CredentialManager(env="staging", env_file=str(env_file))

    def test_production_mode_missing_params_raises(self) -> None:
        """Production mode without encrypted_file raises ValueError."""
        CredentialManager = _import_cm()
        with pytest.raises(ValueError):
            CredentialManager(env="production")

    def test_encrypted_file_not_found_raises(self, credential_dir: Path) -> None:
        """FileNotFoundError raised when the encrypted file path does not exist."""
        CredentialManager = _import_cm()
        key = CredentialManager.generate_encryption_key()
        missing = str(credential_dir / "ghost.enc")
        with pytest.raises(FileNotFoundError):
            CredentialManager(env="production", encrypted_file=missing, encryption_key=key)

    def test_load_key_from_keyring_missing_raises_key_error(self, env_file: Path) -> None:
        """load_key_from_keyring raises KeyError when entry absent in OS keyring."""
        CredentialManager = _import_cm()
        mgr = CredentialManager(env="development", env_file=str(env_file))
        with patch("keyring.get_password", return_value=None):
            with pytest.raises(KeyError):
                mgr.load_key_from_keyring("orbit_trading", "nonexistent_key")

    def test_ibkr_config_handles_non_numeric_port(self, tmp_path: Path) -> None:
        """Non-numeric IBKR_PORT falls back to default 7497."""
        env = tmp_path / ".env"
        env.write_text(
            "MSTOCK_API_KEY=k\n"
            "MSTOCK_ACCESS_TOKEN=t\n"
            "IBKR_HOST=10.0.0.1\n"
            "IBKR_PORT=not_a_number\n"
            "IBKR_CLIENT_ID=also_wrong\n"
        )
        CredentialManager = _import_cm()
        mgr = CredentialManager(env="development", env_file=str(env))
        cfg = mgr.get_ibkr_config()
        assert cfg["port"] == 7497
        assert cfg["client_id"] == 1
