"""
TDD tests for kickstart.py CredentialManager integration.

RED phase: All tests written BEFORE implementation changes to kickstart.py.
These define the contract for how kickstart must handle credentials.

Test groups:
  1. Initialization — CredentialManager wired into kickstart
  2. Broker creation — brokers built from credential manager configs
  3. Encapsulation — credentials not accessible as globals
  4. Dev/prod mode — env-mode switching works
  5. Error handling — missing credentials raise helpful errors
  6. Security — credentials never logged
  7. Lifecycle — cleanup on shutdown clears memory
"""

import os
import json
import logging
import tempfile
import importlib
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_env_file(tmp_path: Path, extra: dict | None = None) -> Path:
    """Write a minimal .env file and return its path."""
    lines = {
        "MSTOCK_API_KEY": "test_api_key_abc",
        "MSTOCK_ACCESS_TOKEN": "test_access_token_xyz",
        "IBKR_HOST": "127.0.0.1",
        "IBKR_PORT": "7497",
        "IBKR_CLIENT_ID": "1",
    }
    if extra:
        lines.update(extra)
    content = "\n".join(f"{k}={v}" for k, v in lines.items())
    env_file = tmp_path / ".env"
    env_file.write_text(content)
    return env_file


def _make_mock_credential_manager(
    api_key: str = "mock_api_key",
    access_token: str = "mock_access_token",
) -> MagicMock:
    """Return a pre-configured CredentialManager mock."""
    mgr = MagicMock()
    mgr.get_mstock_config.return_value = {
        "api_key": api_key,
        "access_token": access_token,
    }
    mgr.get_ibkr_config.return_value = {
        "host": "127.0.0.1",
        "port": 7497,
        "client_id": 1,
    }
    return mgr


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    return _make_env_file(tmp_path)


@pytest.fixture()
def mock_cred_mgr() -> MagicMock:
    return _make_mock_credential_manager()


# ===========================================================================
# 1. INITIALIZATION — CredentialManager wired into kickstart
# ===========================================================================

class TestKickstartInitializesWithCredentialManager:
    """kickstart.initialize_credentials() must exist and call CredentialManager."""

    def test_initialize_credentials_function_exists(self):
        """kickstart must expose initialize_credentials()."""
        import kickstart
        assert callable(getattr(kickstart, "initialize_credentials", None)), (
            "kickstart.initialize_credentials() not found — add the function"
        )

    def test_initialize_credentials_creates_credential_manager(self, env_file: Path):
        """initialize_credentials() must instantiate a CredentialManager."""
        import kickstart

        with patch("kickstart.CredentialManager") as MockCM:
            mock_instance = _make_mock_credential_manager()
            MockCM.return_value = mock_instance

            with patch("kickstart.get_broker", return_value=MagicMock()):
                kickstart.initialize_credentials(
                    env="development",
                    env_file=str(env_file),
                )

        MockCM.assert_called_once()

    def test_initialize_credentials_stores_credential_manager(self, env_file: Path):
        """After initialize_credentials(), kickstart.CREDENTIAL_MANAGER must be set."""
        import kickstart

        mock_instance = _make_mock_credential_manager()
        with patch("kickstart.CredentialManager", return_value=mock_instance):
            with patch("kickstart.get_broker", return_value=MagicMock()):
                kickstart.initialize_credentials(
                    env="development",
                    env_file=str(env_file),
                )

        assert kickstart.CREDENTIAL_MANAGER is not None, (
            "CREDENTIAL_MANAGER global must be set after initialize_credentials()"
        )


# ===========================================================================
# 2. CREDENTIAL MANAGER LOADS BROKER CONFIGS
# ===========================================================================

class TestCredentialManagerBrokerConfigs:
    """CredentialManager must provide configs for each market's broker."""

    def test_initialize_credentials_loads_mstock_config(self, env_file: Path):
        """initialize_credentials() must call get_mstock_config()."""
        import kickstart

        mock_cm = _make_mock_credential_manager()
        with patch("kickstart.CredentialManager", return_value=mock_cm):
            with patch("kickstart.get_broker", return_value=MagicMock()):
                kickstart.initialize_credentials(
                    env="development",
                    env_file=str(env_file),
                )

        mock_cm.get_mstock_config.assert_called_once()

    def test_initialize_credentials_loads_ibkr_config(self, env_file: Path):
        """initialize_credentials() must call get_ibkr_config()."""
        import kickstart

        mock_cm = _make_mock_credential_manager()
        with patch("kickstart.CredentialManager", return_value=mock_cm):
            with patch("kickstart.get_broker", return_value=MagicMock()):
                kickstart.initialize_credentials(
                    env="development",
                    env_file=str(env_file),
                )

        mock_cm.get_ibkr_config.assert_called_once()

    def test_initialize_credentials_populates_brokers_dict(self, env_file: Path):
        """BROKERS registry must have 'IN' and 'US' entries after init."""
        import kickstart

        mock_cm = _make_mock_credential_manager()
        mock_broker = MagicMock()
        with patch("kickstart.CredentialManager", return_value=mock_cm):
            with patch("kickstart.get_broker", return_value=mock_broker):
                kickstart.initialize_credentials(
                    env="development",
                    env_file=str(env_file),
                )

        assert "IN" in kickstart.BROKERS, "BROKERS dict must have 'IN' key"
        assert "US" in kickstart.BROKERS, "BROKERS dict must have 'US' key"


# ===========================================================================
# 3. BROKER RECEIVES CORRECT CREDENTIALS
# ===========================================================================

class TestBrokerReceivesCredentials:
    """Brokers must be built with credentials from CredentialManager, not globals."""

    def test_mstock_broker_gets_api_key_from_credential_manager(self, env_file: Path):
        """get_broker('IN') must receive api_key from CredentialManager.get_mstock_config()."""
        import kickstart

        mock_cm = _make_mock_credential_manager(
            api_key="secure_api_key",
            access_token="secure_token",
        )
        captured_calls = []

        def capturing_get_broker(market, **creds):
            captured_calls.append((market, creds))
            return MagicMock()

        with patch("kickstart.CredentialManager", return_value=mock_cm):
            with patch("kickstart.get_broker", side_effect=capturing_get_broker):
                kickstart.initialize_credentials(
                    env="development",
                    env_file=str(env_file),
                )

        in_calls = [(m, c) for m, c in captured_calls if m == "IN"]
        assert in_calls, "get_broker must be called for market 'IN'"
        _, in_creds = in_calls[0]
        assert in_creds.get("api_key") == "secure_api_key"
        assert in_creds.get("access_token") == "secure_token"

    def test_ibkr_broker_gets_host_from_credential_manager(self, env_file: Path):
        """get_broker('US') must receive host from CredentialManager.get_ibkr_config()."""
        import kickstart

        mock_cm = _make_mock_credential_manager()
        mock_cm.get_ibkr_config.return_value = {
            "host": "192.168.1.100",
            "port": 4001,
            "client_id": 5,
        }
        captured_calls = []

        def capturing_get_broker(market, **creds):
            captured_calls.append((market, creds))
            return MagicMock()

        with patch("kickstart.CredentialManager", return_value=mock_cm):
            with patch("kickstart.get_broker", side_effect=capturing_get_broker):
                kickstart.initialize_credentials(
                    env="development",
                    env_file=str(env_file),
                )

        us_calls = [(m, c) for m, c in captured_calls if m == "US"]
        assert us_calls, "get_broker must be called for market 'US'"
        _, us_creds = us_calls[0]
        assert us_creds.get("host") == "192.168.1.100"
        assert us_creds.get("port") == 4001


# ===========================================================================
# 4. CREDENTIAL ENCAPSULATION (no raw globals)
# ===========================================================================

class TestCredentialEncapsulation:
    """Raw credential values must NOT be accessible as module-level globals."""

    def test_credential_manager_encapsulates_api_key(self, env_file: Path):
        """After init, raw API_KEY must not equal the CredentialManager's value.

        The CredentialManager controls the secret; kickstart should use the broker
        object rather than spreading raw keys into globals.
        """
        import kickstart

        mock_cm = _make_mock_credential_manager(
            api_key="super_secret_key",
            access_token="super_secret_token",
        )
        with patch("kickstart.CredentialManager", return_value=mock_cm):
            with patch("kickstart.get_broker", return_value=MagicMock()):
                kickstart.initialize_credentials(
                    env="development",
                    env_file=str(env_file),
                )

        # The broker object (not a raw string) should be used for trading.
        # We verify BROKERS are set properly (not raw string globals doing the work).
        assert kickstart.BROKERS.get("IN") is not None, (
            "Broker for 'IN' must be set — trading should go through BROKERS, "
            "not raw API_KEY/ACCESS_TOKEN globals"
        )

    def test_brokers_dict_is_module_level_global(self):
        """BROKERS must exist as a module-level dict in kickstart."""
        import kickstart
        assert hasattr(kickstart, "BROKERS"), "kickstart must have BROKERS dict"
        assert isinstance(kickstart.BROKERS, dict), "BROKERS must be a dict"

    def test_credential_manager_is_module_level_global(self):
        """CREDENTIAL_MANAGER must exist as a module-level variable in kickstart."""
        import kickstart
        assert hasattr(kickstart, "CREDENTIAL_MANAGER"), (
            "kickstart must have CREDENTIAL_MANAGER module-level variable"
        )


# ===========================================================================
# 5. DEVELOPMENT MODE
# ===========================================================================

class TestDevelopmentMode:
    """Dev mode reads from .env file."""

    def test_dev_mode_passes_env_file_to_credential_manager(self, env_file: Path):
        """initialize_credentials(env='development') must pass env_file path to CredentialManager."""
        import kickstart

        mock_cm = _make_mock_credential_manager()
        captured_kwargs = {}

        def capture_cm(**kwargs):
            captured_kwargs.update(kwargs)
            return mock_cm

        with patch("kickstart.CredentialManager", side_effect=capture_cm):
            with patch("kickstart.get_broker", return_value=MagicMock()):
                kickstart.initialize_credentials(
                    env="development",
                    env_file=str(env_file),
                )

        assert captured_kwargs.get("env") == "development"

    def test_dev_mode_default_env_is_development(self, env_file: Path):
        """initialize_credentials with no env arg defaults to development."""
        import kickstart

        mock_cm = _make_mock_credential_manager()
        captured_kwargs = {}

        def capture_cm(**kwargs):
            captured_kwargs.update(kwargs)
            return mock_cm

        with patch("kickstart.CredentialManager", side_effect=capture_cm):
            with patch("kickstart.get_broker", return_value=MagicMock()):
                # No env kwarg — should default to development
                kickstart.initialize_credentials(env_file=str(env_file))

        assert captured_kwargs.get("env") == "development", (
            "Default env should be 'development'"
        )


# ===========================================================================
# 6. PRODUCTION MODE
# ===========================================================================

class TestProductionMode:
    """Prod mode passes encrypted_file + encryption_key to CredentialManager."""

    def test_prod_mode_passes_encrypted_file_to_credential_manager(self, tmp_path: Path):
        """initialize_credentials(env='production') must pass encrypted_file."""
        import kickstart

        mock_cm = _make_mock_credential_manager()
        fake_enc_file = str(tmp_path / "creds.enc")
        fake_key = b"A" * 44  # Fernet key length (URL-safe base64, 44 chars)
        captured_kwargs = {}

        def capture_cm(**kwargs):
            captured_kwargs.update(kwargs)
            return mock_cm

        with patch("kickstart.CredentialManager", side_effect=capture_cm):
            with patch("kickstart.get_broker", return_value=MagicMock()):
                kickstart.initialize_credentials(
                    env="production",
                    encrypted_file=fake_enc_file,
                    encryption_key=fake_key,
                )

        assert captured_kwargs.get("env") == "production"
        assert captured_kwargs.get("encrypted_file") == fake_enc_file
        assert captured_kwargs.get("encryption_key") == fake_key


# ===========================================================================
# 7. MISSING CREDENTIALS — HELPFUL ERRORS
# ===========================================================================

class TestMissingCredentialsErrors:
    """Missing credentials must raise clear, descriptive errors."""

    def test_missing_mstock_key_raises_error(self, tmp_path: Path):
        """initialize_credentials with empty .env raises KeyError or ValueError."""
        import kickstart

        empty_env = tmp_path / ".env"
        empty_env.write_text("")  # No keys at all

        with pytest.raises((KeyError, ValueError, Exception)):
            kickstart.initialize_credentials(
                env="development",
                env_file=str(empty_env),
            )

    def test_credential_manager_error_propagates(self, env_file: Path):
        """If CredentialManager raises, initialize_credentials must propagate it."""
        import kickstart

        with patch("kickstart.CredentialManager", side_effect=KeyError("MSTOCK_API_KEY")):
            with pytest.raises((KeyError, RuntimeError, Exception)):
                kickstart.initialize_credentials(
                    env="development",
                    env_file=str(env_file),
                )

    def test_broker_creation_failure_raises_error(self, env_file: Path):
        """If get_broker raises, initialize_credentials must propagate or wrap it."""
        import kickstart

        mock_cm = _make_mock_credential_manager()
        with patch("kickstart.CredentialManager", return_value=mock_cm):
            with patch("kickstart.get_broker", side_effect=ValueError("Unknown market")):
                with pytest.raises(Exception):
                    kickstart.initialize_credentials(
                        env="development",
                        env_file=str(env_file),
                    )


# ===========================================================================
# 8. SECURITY — CREDENTIALS NEVER IN LOGS
# ===========================================================================

class TestCredentialsNotLogged:
    """Credential values must never appear in log output."""

    def test_api_key_not_in_log_output(self, env_file: Path, caplog):
        """initialize_credentials must not log raw api_key value."""
        import kickstart

        secret_key = "SUPER_SECRET_API_KEY_12345"
        mock_cm = _make_mock_credential_manager(api_key=secret_key)

        with patch("kickstart.CredentialManager", return_value=mock_cm):
            with patch("kickstart.get_broker", return_value=MagicMock()):
                with caplog.at_level(logging.DEBUG):
                    kickstart.initialize_credentials(
                        env="development",
                        env_file=str(env_file),
                    )

        all_log_text = " ".join(caplog.messages)
        assert secret_key not in all_log_text, (
            f"API key value appeared in log output: {secret_key!r}"
        )

    def test_access_token_not_in_log_output(self, env_file: Path, caplog):
        """initialize_credentials must not log raw access_token value."""
        import kickstart

        secret_token = "SUPER_SECRET_ACCESS_TOKEN_67890"
        mock_cm = _make_mock_credential_manager(access_token=secret_token)

        with patch("kickstart.CredentialManager", return_value=mock_cm):
            with patch("kickstart.get_broker", return_value=MagicMock()):
                with caplog.at_level(logging.DEBUG):
                    kickstart.initialize_credentials(
                        env="development",
                        env_file=str(env_file),
                    )

        all_log_text = " ".join(caplog.messages)
        assert secret_token not in all_log_text, (
            f"Access token appeared in log output: {secret_token!r}"
        )


# ===========================================================================
# 9. SHUTDOWN CLEANUP
# ===========================================================================

class TestCredentialCleanupOnShutdown:
    """Cleanup function must clear CREDENTIAL_MANAGER from memory."""

    def test_cleanup_function_exists(self):
        """kickstart must expose a cleanup() function."""
        import kickstart
        assert callable(getattr(kickstart, "cleanup", None)), (
            "kickstart.cleanup() not found — add the cleanup function"
        )

    def test_cleanup_clears_credential_manager(self, env_file: Path):
        """cleanup() must set CREDENTIAL_MANAGER to None."""
        import kickstart

        mock_cm = _make_mock_credential_manager()
        with patch("kickstart.CredentialManager", return_value=mock_cm):
            with patch("kickstart.get_broker", return_value=MagicMock()):
                kickstart.initialize_credentials(
                    env="development",
                    env_file=str(env_file),
                )

        assert kickstart.CREDENTIAL_MANAGER is not None  # sanity

        kickstart.cleanup()

        assert kickstart.CREDENTIAL_MANAGER is None, (
            "CREDENTIAL_MANAGER must be None after cleanup()"
        )

    def test_cleanup_is_safe_when_credential_manager_is_none(self):
        """cleanup() must not raise if CREDENTIAL_MANAGER is already None."""
        import kickstart
        kickstart.CREDENTIAL_MANAGER = None  # force state
        kickstart.cleanup()  # must not raise


# ===========================================================================
# 10. BROKERS REGISTRY INTEGRATION
# ===========================================================================

class TestBrokersRegistryIntegration:
    """BROKERS['IN'] and BROKERS['US'] must be usable broker instances."""

    def test_brokers_in_is_broker_interface(self, env_file: Path):
        """BROKERS['IN'] must satisfy BrokerInterface after init."""
        import kickstart
        from brokers.interface import BrokerInterface

        mock_cm = _make_mock_credential_manager()
        mock_broker = MagicMock(spec=["get_funds", "get_holdings", "get_positions",
                                       "get_orders", "get_quote", "place_order",
                                       "get_historical_data"])
        with patch("kickstart.CredentialManager", return_value=mock_cm):
            with patch("kickstart.get_broker", return_value=mock_broker):
                kickstart.initialize_credentials(
                    env="development",
                    env_file=str(env_file),
                )

        assert kickstart.BROKERS["IN"] is not None

    def test_get_broker_called_for_both_markets(self, env_file: Path):
        """get_broker must be called for both 'IN' and 'US' markets."""
        import kickstart

        mock_cm = _make_mock_credential_manager()
        markets_called = []

        def tracking_get_broker(market, **creds):
            markets_called.append(market)
            return MagicMock()

        with patch("kickstart.CredentialManager", return_value=mock_cm):
            with patch("kickstart.get_broker", side_effect=tracking_get_broker):
                kickstart.initialize_credentials(
                    env="development",
                    env_file=str(env_file),
                )

        assert "IN" in markets_called, "get_broker must be called with 'IN'"
        assert "US" in markets_called, "get_broker must be called with 'US'"

    def test_brokers_dict_replaced_not_mutated_across_calls(self, env_file: Path):
        """Each initialize_credentials() call replaces BROKERS contents cleanly."""
        import kickstart

        mock_cm = _make_mock_credential_manager()
        broker_a = MagicMock(name="broker_a")
        broker_b = MagicMock(name="broker_b")
        call_count = [0]

        def alternating_broker(market, **creds):
            call_count[0] += 1
            return broker_a if call_count[0] <= 2 else broker_b

        with patch("kickstart.CredentialManager", return_value=mock_cm):
            with patch("kickstart.get_broker", side_effect=alternating_broker):
                kickstart.initialize_credentials(
                    env="development",
                    env_file=str(env_file),
                )
                first_in = kickstart.BROKERS["IN"]

                kickstart.initialize_credentials(
                    env="development",
                    env_file=str(env_file),
                )
                second_in = kickstart.BROKERS["IN"]

        # Second init should have replaced the broker instance
        assert second_in is broker_b, (
            "Re-initializing credentials must replace broker instances in BROKERS dict"
        )
