"""
Configuration management for YouTube Downloader application.
Uses pydantic-settings for environment variable loading and validation.
"""

from pathlib import Path
from typing import List, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application Settings
    app_name: str = "YouTube Video Downloader"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security
    cookie_encryption_key: str = Field(
        default="",
        description="Fernet encryption key for cookie storage. Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
    )
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for session management"
    )
    
    # Database
    database_url: str = Field(
        default="sqlite:///./youtube_downloader.db",
        description="Database URL (SQLite or PostgreSQL)"
    )
    
    # OAuth Configuration
    google_client_id: str = Field(
        default="",
        description="Google OAuth Client ID from Google Cloud Console"
    )
    google_client_secret: str = Field(
        default="",
        description="Google OAuth Client Secret from Google Cloud Console"
    )
    oauth_redirect_uri: str = Field(
        default="http://localhost:8000/api/auth/callback",
        description="OAuth redirect URI (must match Google Cloud Console settings)"
    )
    oauth_scopes: Any = Field(
        default=["openid", "https://www.googleapis.com/auth/youtube.readonly"],
        description="OAuth scopes to request"
    )
    
    # CORS Configuration
    allowed_origins: Any = Field(
        default=["http://localhost:8000", "http://127.0.0.1:8000"],
        description="Allowed CORS origins"
    )
    
    # Download Settings
    download_output_dir: Path = Field(
        default=Path("downloads"),
        description="Directory for downloaded videos"
    )
    download_temp_dir: Path = Field(
        default=Path("temp"),
        description="Directory for temporary download files"
    )
    max_concurrent_downloads_per_user: int = Field(
        default=3,
        description="Maximum concurrent downloads per user"
    )
    max_download_size_mb: int = Field(
        default=2048,
        description="Maximum download size in MB (2GB default)"
    )
    download_timeout_seconds: int = Field(
        default=3600,
        description="Download timeout in seconds (1 hour default)"
    )
    
    # Retry Settings
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for failed downloads"
    )
    retry_delay_seconds: int = Field(
        default=2,
        description="Initial delay between retries (exponential backoff)"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_file: Path = Field(
        default=Path("logs/app.log"),
        description="Log file path"
    )
    
    # Session Settings
    session_timeout_hours: int = Field(
        default=24,
        description="Session timeout in hours"
    )
    cookie_refresh_threshold_hours: int = Field(
        default=6,
        description="Refresh cookies if expiring within this many hours"
    )
    
    @validator("download_output_dir", "download_temp_dir", "log_file", pre=True)
    def ensure_path(cls, v):
        """Convert string to Path object."""
        if isinstance(v, str):
            return Path(v)
        return v
    
    @validator("allowed_origins", "oauth_scopes", pre=True)
    def parse_list(cls, v):
        """Parse comma-separated string into list."""
        if isinstance(v, str):
            # Handle empty string
            if not v or v.strip() == "":
                return []
            # Remove quotes if present
            v = v.strip('"').strip("'")
            # Split by comma
            return [item.strip() for item in v.split(",") if item.strip()]
        return v if v is not None else []
    
    def create_directories(self):
        """Create necessary directories if they don't exist."""
        self.download_output_dir.mkdir(parents=True, exist_ok=True)
        self.download_temp_dir.mkdir(parents=True, exist_ok=True)
        if self.log_file.parent:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_oauth_configured(self) -> bool:
        """Check if OAuth credentials are configured."""
        return bool(self.google_client_id and self.google_client_secret)
    
    @property
    def is_encryption_configured(self) -> bool:
        """Check if cookie encryption is configured."""
        return bool(self.cookie_encryption_key)


# Global settings instance
settings = Settings()
