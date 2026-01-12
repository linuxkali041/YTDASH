"""
Application settings model for dynamic configuration.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import json


class AppSetting(Base):
    """Application settings stored in database."""
    
    __tablename__ = "app_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)  # JSON string
    category = Column(String(50), nullable=False)  # e.g., "download", "system", "ui"
    description = Column(Text, nullable=True)
    value_type = Column(String(20), default="string")  # string, integer, boolean, json
    
    # Audit
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<AppSetting(key='{self.key}', category='{self.category}')>"
    
    def get_value(self):
        """Get the parsed value based on type."""
        if self.value_type == "integer":
            return int(self.value)
        elif self.value_type == "boolean":
            return self.value.lower() in ('true', '1', 'yes')
        elif self.value_type == "json":
            return json.loads(self.value)
        else:
            return self.value
    
    def set_value(self, value):
        """Set value with automatic type conversion."""
        if self.value_type == "json":
            self.value = json.dumps(value)
        else:
            self.value = str(value)
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.get_value(),
            'category': self.category,
            'description': self.description,
            'value_type': self.value_type,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by
        }


# Default settings to be inserted on first run
DEFAULT_SETTINGS = [
    {
        'key': 'max_concurrent_downloads_global',
        'value': '10',
        'category': 'download',
        'description': 'Maximum concurrent downloads across all users',
        'value_type': 'integer'
    },
    {
        'key': 'max_concurrent_downloads_per_user',
        'value': '3',
        'category': 'download',
        'description': 'Maximum concurrent downloads per user',
        'value_type': 'integer'
    },
    {
        'key': 'max_download_size_mb',
        'value': '2048',
        'category': 'download',
        'description': 'Maximum download size in MB',
        'value_type': 'integer'
    },
    {
        'key': 'download_timeout_seconds',
        'value': '3600',
        'category': 'download',
        'description': 'Download timeout in seconds',
        'value_type': 'integer'
    },
    {
        'key': 'default_storage_quota_gb',
        'value': '10',
        'category': 'users',
        'description': 'Default storage quota per user in GB',
        'value_type': 'integer'
    },
    {
        'key': 'registration_enabled',
        'value': 'true',
        'category': 'system',
        'description': 'Allow new user registration',
        'value_type': 'boolean'
    },
    {
        'key': 'maintenance_mode',
        'value': 'false',
        'category': 'system',
        'description': 'Enable maintenance mode',
        'value_type': 'boolean'
    },
    {
        'key': 'site_name',
        'value': 'YouTube Video Downloader',
        'category': 'ui',
        'description': 'Website name',
        'value_type': 'string'
    },
    {
        'key': 'require_email_verification',
        'value': 'false',
        'category': 'system',
        'description': 'Require email verification for new accounts',
        'value_type': 'boolean'
    },
    {
        'key': 'max_retries',
        'value': '3',
        'category': 'download',
        'description': 'Maximum retry attempts for failed downloads',
        'value_type': 'integer'
    },
    {
        'key': 'youtube_cookies',
        'value': '',
        'category': 'download',
        'description': 'Global YouTube Cookies (Netscape Format)',
        'value_type': 'text'
    }
]

def ensure_default_settings(db_session):
    """Ensure all default settings exist in the database."""
    try:
        count = 0
        for default in DEFAULT_SETTINGS:
            existing = db_session.query(AppSetting).filter(AppSetting.key == default['key']).first()
            if not existing:
                setting = AppSetting(
                    key=default['key'],
                    value=default['value'],
                    category=default['category'],
                    description=default['description'],
                    value_type=default['value_type']
                )
                db_session.add(setting)
                count += 1
            else:
                 # Check if type needs update for existing keys (specifically youtube_cookies)
                 if existing.key == 'youtube_cookies' and existing.value_type != 'text':
                      existing.value_type = 'text'
                      count += 1

        if count > 0:
            db_session.commit()
            print(f"Added/Updated {count} default settings.")
    except Exception as e:
        print(f"Error ensuring default settings: {e}")
        db_session.rollback()
