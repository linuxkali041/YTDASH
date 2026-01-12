"""
Pydantic models for download operations.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class DownloadStatus(str, Enum):
    """Download status enumeration."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FormatType(str, Enum):
    """Format type enumeration."""
    VIDEO = "video"
    AUDIO = "audio"
    BOTH = "both"


class VideoInfoRequest(BaseModel):
    """Request model for video info."""
    url: str = Field(..., description="YouTube video URL")
    session_id: Optional[str] = Field(None, description="Session ID for authenticated requests")


class FormatOption(BaseModel):
    """Video format option."""
    format_id: str = Field(..., description="Format identifier")
    ext: str = Field(..., description="File extension (mp4, webm, m4a, etc.)")
    resolution: Optional[str] = Field(None, description="Video resolution (1080p, 720p, etc.)")
    fps: Optional[float] = Field(None, description="Frames per second")
    vcodec: Optional[str] = Field(None, description="Video codec")
    acodec: Optional[str] = Field(None, description="Audio codec")
    abr: Optional[float] = Field(None, description="Audio bitrate in kbps")
    filesize: Optional[float] = Field(None, description="File size in bytes")
    filesize_approx: Optional[float] = Field(None, description="Approximate file size in bytes")
    format_note: Optional[str] = Field(None, description="Format description")
    
    @property
    def filesize_display(self) -> str:
        """Get human-readable file size."""
        size = self.filesize or self.filesize_approx
        if not size:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class VideoInfoResponse(BaseModel):
    """Response model for video info."""
    video_id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Video title")
    duration: int = Field(..., description="Duration in seconds")
    thumbnail: str = Field(..., description="Thumbnail URL")
    uploader: Optional[str] = Field(None, description="Channel name")
    view_count: Optional[int] = Field(None, description="View count")
    like_count: Optional[int] = Field(None, description="Like count")
    description: Optional[str] = Field(None, description="Video description")
    upload_date: Optional[str] = Field(None, description="Upload date (YYYYMMDD)")
    formats: List[FormatOption] = Field(default_factory=list, description="Available formats")
    
    @property
    def duration_display(self) -> str:
        """Get human-readable duration."""
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


class DownloadRequest(BaseModel):
    """Request model for download."""
    url: str = Field(..., description="YouTube video URL")
    format_type: FormatType = Field(FormatType.VIDEO, description="Download type (video/audio/both)")
    format_id: Optional[str] = Field(None, description="Specific format ID to download")
    quality: Optional[str] = Field("best", description="Quality preference (best, 1080p, 720p, etc.)")
    audio_format: Optional[str] = Field("best", description="Audio format (best, m4a, mp3, etc.)")
    video_codec: Optional[str] = Field(None, description="Preferred video codec (h264, vp9, av1)")
    audio_codec: Optional[str] = Field(None, description="Preferred audio codec (aac, opus, mp3)")
    session_id: Optional[str] = Field(None, description="Session ID for authenticated requests")
    
    @validator('quality')
    def validate_quality(cls, v):
        """Validate quality value."""
        valid_qualities = ['best', 'worst', '2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p']
        if v not in valid_qualities:
            raise ValueError(f"Invalid quality. Must be one of: {', '.join(valid_qualities)}")
        return v


class DownloadResponse(BaseModel):
    """Response model for download initiation."""
    download_id: str = Field(..., description="Unique download identifier")
    status: DownloadStatus = Field(..., description="Download status")
    message: str = Field(..., description="Status message")


class ProgressUpdate(BaseModel):
    """Progress update model."""
    download_id: str = Field(..., description="Download identifier")
    status: DownloadStatus = Field(..., description="Current status")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Progress percentage (0-100)")
    downloaded_bytes: Optional[float] = Field(0, description="Bytes downloaded")
    total_bytes: Optional[float] = Field(None, description="Total bytes (if known)")
    speed: Optional[float] = Field(None, description="Download speed in bytes/sec")
    eta: Optional[float] = Field(None, description="Estimated time remaining in seconds")
    filename: Optional[str] = Field(None, description="Output filename")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    @property
    def speed_display(self) -> str:
        """Get human-readable download speed."""
        if not self.speed:
            return "Unknown"
        
        speed = self.speed
        for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
            if speed < 1024:
                return f"{speed:.1f} {unit}"
            speed /= 1024
        return f"{speed:.1f} TB/s"
    
    @property
    def eta_display(self) -> str:
        """Get human-readable ETA."""
        if not self.eta:
            return "Unknown"
        
        # Convert to int for display calculations
        eta_int = int(self.eta)
        
        hours = eta_int // 3600
        minutes = (eta_int % 3600) // 60
        seconds = eta_int % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"


class DownloadStatusResponse(BaseModel):
    """Response model for download status check."""
    download_id: str
    status: DownloadStatus
    progress: Optional[ProgressUpdate] = None
    created_at: str
    completed_at: Optional[str] = None


# =============================================================================
# Playlist Models
# =============================================================================

class PlaylistInfoRequest(BaseModel):
    """Request model for playlist info."""
    url: str = Field(..., description="YouTube playlist URL")
    session_id: Optional[str] = Field(None, description="Session ID for authenticated requests")


class PlaylistVideoInfo(BaseModel):
    """Individual video info within a playlist."""
    video_id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Video title")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    thumbnail: Optional[str] = Field(None, description="Thumbnail URL")
    url: str = Field(..., description="Video URL")
    
    @property
    def duration_display(self) -> str:
        """Get human-readable duration."""
        if not self.duration:
            return "Unknown"
        
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


class PlaylistInfoResponse(BaseModel):
    """Response model for playlist info."""
    playlist_id: str = Field(..., description="YouTube playlist ID")
    title: str = Field(..., description="Playlist title")
    uploader: Optional[str] = Field(None, description="Channel name")
    video_count: int = Field(..., description="Number of videos in playlist")
    description: Optional[str] = Field(None, description="Playlist description")
    videos: List[PlaylistVideoInfo] = Field(default_factory=list, description="List of videos in playlist")


class PlaylistDownloadRequest(BaseModel):
    """Request model for playlist download."""
    url: str = Field(..., description="YouTube playlist URL")
    video_ids: Optional[List[str]] = Field(None, description="Specific video IDs to download (None = all)")
    format_type: FormatType = Field(FormatType.VIDEO, description="Download type (video/audio)")
    quality: Optional[str] = Field("best", description="Quality preference")
    audio_format: Optional[str] = Field("best", description="Audio format")
    video_codec: Optional[str] = Field(None, description="Preferred video codec")
    audio_codec: Optional[str] = Field(None, description="Preferred audio codec")
    session_id: Optional[str] = Field(None, description="Session ID for authenticated requests")
    
    @validator('quality')
    def validate_quality(cls, v):
        """Validate quality value."""
        valid_qualities = ['best', 'worst', '2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p']
        if v not in valid_qualities:
            raise ValueError(f"Invalid quality. Must be one of: {', '.join(valid_qualities)}")
        return v


class PlaylistDownloadResponse(BaseModel):
    """Response model for playlist download initiation."""
    playlist_id: str = Field(..., description="Playlist download identifier")
    download_ids: List[str] = Field(..., description="List of individual video download IDs")
    total_videos: int = Field(..., description="Total number of videos to download")
    message: str = Field(..., description="Status message")


class PlaylistProgressUpdate(BaseModel):
    """Aggregate progress for playlist download."""
    playlist_id: str = Field(..., description="Playlist download identifier")
    total_videos: int = Field(..., description="Total videos in download")
    completed_videos: int = Field(0, description="Number of completed videos")
    failed_videos: int = Field(0, description="Number of failed videos")
    downloading_videos: int = Field(0, description="Number of currently downloading videos")
    pending_videos: int = Field(0, description="Number of pending videos")
    overall_progress: float = Field(0.0, ge=0.0, le=100.0, description="Overall progress percentage")
    video_progress: List[ProgressUpdate] = Field(default_factory=list, description="Individual video progress")
