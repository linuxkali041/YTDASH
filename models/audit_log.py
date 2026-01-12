"""
Audit log model for tracking admin and user actions.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import json


class AuditLog(Base):
    """Audit log for tracking actions."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Action details
    action = Column(String(100), nullable=False, index=True)  # e.g., "user_created", "setting_updated"
    resource_type = Column(String(50), nullable=True)  # e.g., "user", "setting", "download"
    resource_id = Column(Integer, nullable=True)
    
    # Additional details
    details = Column(Text, nullable=True)  # JSON string with additional info
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"
    
    def get_details(self):
        """Parse details JSON."""
        if self.details:
            try:
                return json.loads(self.details)
            except:
                return {}
        return {}
    
    def set_details(self, details_dict):
        """Set details from dictionary."""
        self.details = json.dumps(details_dict)
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.get_details(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'username': self.user.username if self.user else 'System'
        }
