"""
Secure cookie encryption and storage manager.
Uses Fernet symmetric encryption to protect YouTube session cookies.
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from cryptography.fernet import Fernet, InvalidToken
import json
import base64
from utils.errors import EncryptionError, ConfigurationError
from utils.logging_config import get_logger

logger = get_logger(__name__)


class CookieManager:
    """Manages encryption, decryption, and storage of user cookies."""
    
    def __init__(self, encryption_key: str):
        """
        Initialize cookie manager.
        
        Args:
            encryption_key: Base64-encoded Fernet encryption key
            
        Raises:
            ConfigurationError: If encryption key is invalid
        """
        if not encryption_key:
            raise ConfigurationError("Cookie encryption key not configured")
        
        try:
            # Validate and initialize Fernet cipher
            self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise ConfigurationError(f"Invalid encryption key: {e}")
        
        # In-memory cookie storage {session_id: encrypted_cookies}
        self._cookie_store: Dict[str, bytes] = {}
        
        # Cookie metadata {session_id: {created_at, last_accessed, expires_at}}
        self._metadata: Dict[str, Dict] = {}
    
    def encrypt_cookies(self, cookies: Dict[str, str]) -> bytes:
        """
        Encrypt cookies dictionary.
        
        Args:
            cookies: Dictionary of cookie names and values
            
        Returns:
            Encrypted cookies as bytes
            
        Raises:
            EncryptionError: If encryption fails
        """
        try:
            # Convert cookies to JSON string
            cookie_json = json.dumps(cookies)
            
            # Encrypt
            encrypted = self.cipher.encrypt(cookie_json.encode('utf-8'))
            
            logger.debug(f"Encrypted {len(cookies)} cookies")
            return encrypted
        except Exception as e:
            logger.error(f"Cookie encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt cookies: {e}")
    
    def decrypt_cookies(self, encrypted_cookies: bytes) -> Dict[str, str]:
        """
        Decrypt cookies.
        
        Args:
            encrypted_cookies: Encrypted cookies bytes
            
        Returns:
            Decrypted cookies dictionary
            
        Raises:
            EncryptionError: If decryption fails
        """
        try:
            # Decrypt
            decrypted = self.cipher.decrypt(encrypted_cookies)
            
            # Parse JSON
            cookies = json.loads(decrypted.decode('utf-8'))
            
            logger.debug(f"Decrypted {len(cookies)} cookies")
            return cookies
        except InvalidToken:
            logger.error("Invalid encryption token - cookies may be corrupted")
            raise EncryptionError("Invalid encryption token")
        except Exception as e:
            logger.error(f"Cookie decryption failed: {e}")
            raise EncryptionError(f"Failed to decrypt cookies: {e}")
    
    def store_cookies(
        self,
        session_id: str,
        cookies: Dict[str, str],
        expires_in_hours: int = 24
    ) -> None:
        """
        Encrypt and store cookies for a session.
        
        Args:
            session_id: Unique session identifier
            cookies: Cookies to store
            expires_in_hours: Hours until cookies expire
        """
        try:
            # Encrypt cookies
            encrypted = self.encrypt_cookies(cookies)
            
            # Store encrypted cookies
            self._cookie_store[session_id] = encrypted
            
            # Store metadata
            now = datetime.utcnow()
            self._metadata[session_id] = {
                'created_at': now,
                'last_accessed': now,
                'expires_at': now + timedelta(hours=expires_in_hours)
            }
            
            logger.info(f"Stored cookies for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to store cookies for session {session_id}: {e}")
            raise
    
    def retrieve_cookies(self, session_id: str) -> Optional[Dict[str, str]]:
        """
        Retrieve and decrypt cookies for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Decrypted cookies or None if not found/expired
        """
        # Check if session exists
        if session_id not in self._cookie_store:
            logger.debug(f"No cookies found for session {session_id}")
            return None
        
        # Check if expired
        metadata = self._metadata.get(session_id)
        if metadata and metadata['expires_at'] < datetime.utcnow():
            logger.info(f"Cookies expired for session {session_id}")
            self.delete_cookies(session_id)
            return None
        
        try:
            # Decrypt and return
            cookies = self.decrypt_cookies(self._cookie_store[session_id])
            
            # Update last accessed time
            if metadata:
                metadata['last_accessed'] = datetime.utcnow()
            
            logger.debug(f"Retrieved cookies for session {session_id}")
            return cookies
        except Exception as e:
            logger.error(f"Failed to retrieve cookies for session {session_id}: {e}")
            return None
    
    def delete_cookies(self, session_id: str) -> bool:
        """
        Delete cookies for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self._cookie_store:
            del self._cookie_store[session_id]
            if session_id in self._metadata:
                del self._metadata[session_id]
            logger.info(f"Deleted cookies for session {session_id}")
            return True
        return False
    
    def is_expired(self, session_id: str) -> bool:
        """
        Check if cookies are expired.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if expired or not found, False otherwise
        """
        metadata = self._metadata.get(session_id)
        if not metadata:
            return True
        return metadata['expires_at'] < datetime.utcnow()
    
    def needs_refresh(self, session_id: str, threshold_hours: int = 6) -> bool:
        """
        Check if cookies should be refreshed.
        
        Args:
            session_id: Session identifier
            threshold_hours: Refresh if expiring within this many hours
            
        Returns:
            True if should refresh, False otherwise
        """
        metadata = self._metadata.get(session_id)
        if not metadata:
            return True
        
        time_until_expiry = metadata['expires_at'] - datetime.utcnow()
        return time_until_expiry < timedelta(hours=threshold_hours)
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired cookies.
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        expired_sessions = [
            sid for sid, meta in self._metadata.items()
            if meta['expires_at'] < now
        ]
        
        for session_id in expired_sessions:
            self.delete_cookies(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def get_session_count(self) -> int:
        """Get number of active sessions."""
        return len(self._cookie_store)
