"""
YouTube credentials model for storing user YouTube account cookies.
"""

from sqlalchemy import Column, Integer, String, Boolean,DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class YouTubeCredential(Base):
    """YouTube account credentials for users."""
    
    __tablename__ = "youtube_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Account info
    account_email = Column(String(255), nullable=False)
    account_name = Column(String(255), nullable=True)
    
    # Encrypted cookies
    encrypted_cookies = Column(Text, nullable=False)  # JSON encrypted with Fernet
    encryption_iv = Column(String(255), nullable=True)  # For additional security if needed
    
    # Validation status
    is_valid = Column(Boolean, default=True)
    last_validated = Column(DateTime(timezone=True), nullable=True)
    validation_error = Column(Text, nullable=True)
    
    # Usage statistics
    downloads_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="youtube_credentials")
    
    def __repr__(self):
        return f"<YouTubeCredential(id={self.id}, user_id={self.user_id}, email='{self.account_email}')>"
    
    def to_dict(self, include_cookies=False):
        """Convert to dictionary for API responses."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'account_email': self.account_email,
            'account_name': self.account_name,
            'is_valid': self.is_valid,
            'last_validated': self.last_validated.isoformat() if self.last_validated else None,
            'downloads_count': self.downloads_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        # Never include encrypted cookies in normal responses
        if include_cookies and self.encrypted_cookies:
            data['has_cookies'] = True
        
        return data
