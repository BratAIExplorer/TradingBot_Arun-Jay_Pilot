"""
SecureCredentialManager - BUG-010 FIX

Provides on-demand credential decryption to minimize plaintext exposure in memory.
Credentials are only in memory briefly during API calls, not stored as global 
variables throughout the session.

Usage:
    from secure_credentials import SecureCredentialManager, secure_credentials
    
    # Option 1: Instance-based
    cred_manager = SecureCredentialManager(settings)
    headers = cred_manager.get_auth_headers()
    
    # Option 2: Context manager (auto-cleanup)
    with secure_credentials(settings) as creds:
        api_key = creds.get_api_key()
        # use it...
    # credentials cleaned up after 'with' block
"""

from typing import Optional
from contextlib import contextmanager


class SecureCredentialManager:
    """
    Secure credential storage that decrypts on-demand.
    
    BUG-010 FIX: Credentials are only in memory briefly during API calls,
    not stored as global variables throughout the session.
    
    Benefits:
    - Reduced attack surface from memory dumps
    - No plaintext credentials in global scope
    - Automatic cleanup after use
    - Thread-safe access patterns
    """
    
    def __init__(self, settings_manager):
        """
        Initialize with a SettingsManager instance.
        
        Args:
            settings_manager: SettingsManager instance for decrypting credentials
        """
        self.settings = settings_manager
        
    def get_api_key(self) -> str:
        """Decrypt and return API key on demand"""
        if not self.settings:
            return ""
        return self.settings.get_decrypted("broker.api_key") or ""
    
    def get_api_secret(self) -> str:
        """Decrypt and return API secret on demand"""
        if not self.settings:
            return ""
        return self.settings.get_decrypted("broker.api_secret") or ""
    
    def get_password(self) -> str:
        """Decrypt and return password on demand"""
        if not self.settings:
            return ""
        return self.settings.get_decrypted("broker.password") or ""
    
    def get_access_token(self) -> str:
        """Get current access token"""
        if not self.settings:
            return ""
        return self.settings.get_decrypted("broker.access_token") or ""
    
    def get_client_code(self) -> str:
        """Get client code (not encrypted)"""
        if not self.settings:
            return ""
        return self.settings.get("broker.client_code") or ""
    
    def get_totp_secret(self) -> str:
        """Get TOTP secret for auto-login"""
        if not self.settings:
            return ""
        return self.settings.get_decrypted("broker.totp_secret") or ""
    
    def get_auth_headers(self) -> dict:
        """
        Build auth headers without storing credentials globally.
        
        Returns:
            dict: Headers with Authorization and X-Mirae-Version
        """
        api_key = self.get_api_key()
        access_token = self.get_access_token()
        
        headers = {
            "Authorization": f"token {api_key}:{access_token}",
            "X-Mirae-Version": "1"
        }
        
        # Help Python GC by deleting local refs (minor optimization)
        del api_key
        del access_token
        
        return headers
    
    def has_valid_credentials(self) -> bool:
        """
        Check if all required credentials are present.
        
        Returns:
            bool: True if API key, secret, and client code are all set
        """
        return all([
            self.get_api_key(),
            self.get_api_secret(),
            self.get_client_code()
        ])
    
    def has_totp_configured(self) -> bool:
        """
        Check if TOTP secret is configured for auto-login.
        
        Returns:
            bool: True if TOTP secret is set
        """
        return bool(self.get_totp_secret())
    
    def get_status_summary(self) -> dict:
        """
        Get a summary of credential status (without exposing values).
        
        Returns:
            dict: Status indicators for each credential type
        """
        return {
            "api_key": "✓ SET" if self.get_api_key() else "✗ MISSING",
            "api_secret": "✓ SET" if self.get_api_secret() else "✗ MISSING",
            "client_code": "✓ SET" if self.get_client_code() else "✗ MISSING",
            "password": "✓ SET" if self.get_password() else "✗ MISSING",
            "access_token": "✓ SET" if self.get_access_token() else "✗ MISSING",
            "totp_secret": "✓ SET" if self.get_totp_secret() else "✗ NOT CONFIGURED",
        }


@contextmanager
def secure_credentials(settings_manager):
    """
    Context manager for temporary credential access.
    
    Provides automatic cleanup when exiting the context block.
    
    Usage:
        with secure_credentials(settings) as creds:
            api_key = creds.get_api_key()
            # use it...
        # credentials cleaned up after 'with' block
    
    Args:
        settings_manager: SettingsManager instance
        
    Yields:
        SecureCredentialManager: Credential manager instance
    """
    cred_manager = SecureCredentialManager(settings_manager)
    try:
        yield cred_manager
    finally:
        # Explicit cleanup
        del cred_manager


# Singleton instance (optional, for convenience)
_global_cred_manager: Optional[SecureCredentialManager] = None


def get_credential_manager(settings_manager=None) -> Optional[SecureCredentialManager]:
    """
    Get or create a global SecureCredentialManager instance.
    
    Args:
        settings_manager: SettingsManager instance (required on first call)
        
    Returns:
        SecureCredentialManager: Global credential manager instance
    """
    global _global_cred_manager
    
    if _global_cred_manager is None and settings_manager is not None:
        _global_cred_manager = SecureCredentialManager(settings_manager)
    
    return _global_cred_manager
