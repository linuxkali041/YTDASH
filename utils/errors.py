"""
Custom exception classes for the YouTube Downloader application.
"""


class YouTubeDownloaderError(Exception):
    """Base exception class for all application errors."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DownloadError(YouTubeDownloaderError):
    """Raised when a download operation fails."""
    
    def __init__(self, message: str, url: str = None, status_code: int = 500):
        self.url = url
        super().__init__(message, status_code)


class AuthenticationError(YouTubeDownloaderError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", status_code: int = 401):
        super().__init__(message, status_code)


class RateLimitError(YouTubeDownloaderError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None, status_code: int = 429):
        self.retry_after = retry_after
        super().__init__(message, status_code)


class CaptchaRequiredError(YouTubeDownloaderError):
    """Raised when CAPTCHA verification is required."""
    
    def __init__(self, message: str = "CAPTCHA verification required", status_code: int = 403):
        super().__init__(message, status_code)


class InvalidURLError(YouTubeDownloaderError):
    """Raised when an invalid YouTube URL is provided."""
    
    def __init__(self, message: str = "Invalid YouTube URL", url: str = None, status_code: int = 400):
        self.url = url
        super().__init__(message, status_code)


class VideoUnavailableError(YouTubeDownloaderError):
    """Raised when a video is unavailable or private."""
    
    def __init__(self, message: str = "Video unavailable", url: str = None, status_code: int = 404):
        self.url = url
        super().__init__(message, status_code)


class QueueFullError(YouTubeDownloaderError):
    """Raised when the download queue is full."""
    
    def __init__(self, message: str = "Download queue is full", status_code: int = 503):
        super().__init__(message, status_code)


class EncryptionError(YouTubeDownloaderError):
    """Raised when encryption/decryption fails."""
    
    def __init__(self, message: str = "Encryption/decryption failed", status_code: int = 500):
        super().__init__(message, status_code)


class ConfigurationError(YouTubeDownloaderError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str = "Configuration error", status_code: int = 500):
        super().__init__(message, status_code)
