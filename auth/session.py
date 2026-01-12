"""
Session management for user authentication.
Tracks active user sessions and maps them to encrypted cookies.
"""

import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta
from utils.logging_config import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Manages user sessions."""
    
    def __init__(self):
        """Initialize session manager."""
        # Session storage {session_id: session_data}
        self._sessions: Dict[str, Dict] = {}
    
    def create_session(
        self,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        timeout_hours: int = 24
    ) -> str:
        """
        Create a new session.
        
        Args:
            user_id: User identifier (from OAuth)
            user_email: User email
            timeout_hours: Session timeout in hours
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        now = datetime.utcnow()
        self._sessions[session_id] = {
            'session_id': session_id,
            'user_id': user_id,
            'user_email': user_email,
            'created_at': now,
            'last_activity': now,
            'expires_at': now + timedelta(hours=timeout_hours),
            'authenticated': bool(user_id),
            'active_downloads': []
        }
        
        logger.info(f"Created session {session_id} for user {user_email or 'anonymous'}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found/expired
        """
        if session_id not in self._sessions:
            return None
        
        session = self._sessions[session_id]
        
        # Check if expired
        if session['expires_at'] < datetime.utcnow():
            logger.info(f"Session {session_id} expired")
            self.delete_session(session_id)
            return None
        
        # Update last activity
        session['last_activity'] = datetime.utcnow()
        
        return session
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            **kwargs: Fields to update
            
        Returns:
            True if updated, False if not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.update(kwargs)
        session['last_activity'] = datetime.utcnow()
        
        logger.debug(f"Updated session {session_id}")
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self._sessions:
            user_email = self._sessions[session_id].get('user_email', 'anonymous')
            del self._sessions[session_id]
            logger.info(f"Deleted session {session_id} for user {user_email}")
            return True
        return False
    
    def is_authenticated(self, session_id: str) -> bool:
        """
        Check if session is authenticated.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if authenticated, False otherwise
        """
        session = self.get_session(session_id)
        return session.get('authenticated', False) if session else False
    
    def add_download(self, session_id: str, download_id: str) -> bool:
        """
        Add download to session's active downloads.
        
        Args:
            session_id: Session identifier
            download_id: Download identifier
            
        Returns:
            True if added, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        if download_id not in session['active_downloads']:
            session['active_downloads'].append(download_id)
            logger.debug(f"Added download {download_id} to session {session_id}")
        
        return True
    
    def remove_download(self, session_id: str, download_id: str) -> bool:
        """
        Remove download from session's active downloads.
        
        Args:
            session_id: Session identifier
            download_id: Download identifier
            
        Returns:
            True if removed, False if not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        if download_id in session['active_downloads']:
            session['active_downloads'].remove(download_id)
            logger.debug(f"Removed download {download_id} from session {session_id}")
        
        return True
    
    def get_active_download_count(self, session_id: str) -> int:
        """
        Get number of active downloads for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Number of active downloads
        """
        session = self.get_session(session_id)
        return len(session['active_downloads']) if session else 0
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        expired_sessions = [
            sid for sid, session in self._sessions.items()
            if session['expires_at'] < now
        ]
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def get_session_count(self) -> int:
        """Get number of active sessions."""
        return len(self._sessions)
