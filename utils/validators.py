"""
Input validation utilities for YouTube Downloader.
"""

import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Optional
from .errors import InvalidURLError


# YouTube URL patterns
YOUTUBE_PATTERNS = [
    r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
    r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})',
    r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
    r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
]


def validate_youtube_url(url: str) -> str:
    """
    Validate and normalize YouTube URL.
    
    Args:
        url: YouTube URL to validate
        
    Returns:
        Normalized YouTube URL
        
    Raises:
        InvalidURLError: If URL is invalid or not a YouTube URL
    """
    if not url or not isinstance(url, str):
        raise InvalidURLError("URL must be a non-empty string", url=url)
    
    url = url.strip()
    
    # Try to match against YouTube patterns
    video_id = None
    for pattern in YOUTUBE_PATTERNS:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break
    
    if not video_id:
        raise InvalidURLError("Not a valid YouTube URL", url=url)
    
    # Return normalized URL
    return f"https://www.youtube.com/watch?v={video_id}"


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL.
    
    Args:
        url: YouTube URL
        
    Returns:
        Video ID or None if not found
    """
    for pattern in YOUTUBE_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    Sanitize filename to prevent path traversal and ensure valid characters.
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        Sanitized filename
    """
    # Remove path separators and other dangerous characters
    unsafe_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(unsafe_chars, '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "download"
    
    # Truncate to max length (preserve extension)
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        available_length = max_length - len(ext) - 1 if ext else max_length
        filename = name[:available_length] + ('.' + ext if ext else '')
    
    return filename


def validate_format(format_id: str) -> bool:
    """
    Validate format ID.
    
    Args:
        format_id: Format identifier
        
    Returns:
        True if valid, False otherwise
    """
    if not format_id or not isinstance(format_id, str):
        return False
    
    # Allow alphanumeric, dash, underscore, and plus
    return bool(re.match(r'^[a-zA-Z0-9_+-]+$', format_id))


def validate_quality(quality: str) -> bool:
    """
    Validate quality selection.
    
    Args:
        quality: Quality identifier (e.g., "1080p", "720p", "best", "worst")
        
    Returns:
        True if valid, False otherwise
    """
    valid_qualities = [
        "best", "worst",
        "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p",
        "bestaudio", "worstaudio"
    ]
    return quality in valid_qualities or bool(re.match(r'^\d+p$', quality))


def validate_download_path(path: Path, base_dir: Path) -> bool:
    """
    Validate that download path is within base directory (prevent path traversal).
    
    Args:
        path: Path to validate
        base_dir: Base directory that path must be within
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Resolve to absolute paths
        abs_path = path.resolve()
        abs_base = base_dir.resolve()
        
        # Check if path is within base directory
        return abs_path.is_relative_to(abs_base)
    except (ValueError, OSError):
        return False


def is_valid_session_id(session_id: str) -> bool:
    """
    Validate session ID format.
    
    Args:
        session_id: Session identifier
        
    Returns:
        True if valid, False otherwise
    """
    if not session_id or not isinstance(session_id, str):
        return False
    
    # Session ID should be alphanumeric and hyphen only (UUID format)
    return bool(re.match(r'^[a-zA-Z0-9-]{8,64}$', session_id))


def validate_codec(codec: str) -> bool:
    """
    Validate video/audio codec.
    
    Args:
        codec: Codec identifier
        
    Returns:
        True if valid, False otherwise
    """
    valid_codecs = [
        "h264", "h265", "vp9", "av1",  # Video codecs
        "aac", "opus", "mp3", "vorbis",  # Audio codecs
        "any"  # Any codec
    ]
    return codec.lower() in valid_codecs
