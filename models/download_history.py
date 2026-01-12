"""
Download history model for tracking user downloads.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, BigInteger, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from download.models import DownloadStatus
import enum


class Download(Base):
    """Download history and tracking."""
    
    __tablename__ = "downloads"
    
    id = Column(Integer, primary_key=True, index=True)
    download_id = Column(String(100), unique=True, index=True, nullable=False)  # UUID
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Video info
    youtube_url = Column(String(500), nullable=False)
    video_id = Column(String(20), nullable=True)
    video_title = Column(String(500), nullable=True)
    video_duration = Column(Integer, nullable=True)  # seconds
    
    # Download options
    format_type = Column(String(20), nullable=False)  # video, audio
    quality = Column(String(20), nullable=True)
    format_id = Column(String(50), nullable=True)
    
    # File info
    file_path = Column(String(1000), nullable=True)
    file_size = Column(BigInteger, nullable=True)  # bytes
    file_name = Column(String(500), nullable=True)
    
    # Status and progress
    status = Column(SQLEnum(DownloadStatus), default=DownloadStatus.PENDING, nullable=False)
    progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="downloads")
    
    def __repr__(self):
        return f"<Download(id={self.id}, user_id={self.user_id}, video_title='{self.video_title}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'download_id': self.download_id,
            'user_id': self.user_id,
            'youtube_url': self.youtube_url,
            'video_id': self.video_id,
            'video_title': self.video_title,
            'video_duration': self.video_duration,
            'format_type': self.format_type,
            'quality': self.quality,
            'file_size': self.file_size,
            'file_name': self.file_name,
            'status': self.status.value,
            'progress': self.progress,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
