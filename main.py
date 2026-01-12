"""
Main FastAPI application for YouTube Video Downloader.
"""

# -----------------------------------------------------------------------------
# Dependency Self-Check & Auto-Upgrade (MUST RUN BEFORE IMPORTS)
# -----------------------------------------------------------------------------
import sys
import subprocess

def check_dependencies():
    """Ensure critical dependencies like yt-dlp are up-to-date before loading them."""
    try:
        # Check yt-dlp version or just force upgrade occasionally
        # For this user context, we force check/upgrade on startup to fix the current broken state
        # We can optimize this later to check versions first
        print(f"Bootstrapping: Checking dependencies using {sys.executable}...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--upgrade", "yt-dlp",
            "--disable-pip-version-check",
            "--no-warn-script-location"
        ])
        print("Bootstrapping: Dependencies are up-to-date.")
    except Exception as e:
        print(f"Bootstrapping Warning: Failed to auto-upgrade dependencies: {e}")

# Run the check
if __name__ == "__main__":
    check_dependencies()
# note: if running via uvicorn directly, this might be skipped, but user uses `python main.py`
# We also invoke it at module level just to be safe if it doesn't hurt? 
# No, module level side effects are bad locally if importing. 
# But for this standalone app, it's safer to do it in main block, BUT we need to defer imports?
# Actually, if we just put it at module level guarded by a simple check or just keep it simple.
# The issue is syntax: imports are usually at top.
# WE WILL KEEP IT SIMPLE: imports will stay, but we will wrap the MAIN execution logic.
# WAIT. If we import `download.downloader` at top level, it imports `yt_dlp`.
# So we MUST running the upgrade BEFORE imports if we want to solve the "Upgrade -> Crash" cycle.
# So we have to place this logic BEFORE `from download.downloader ...`

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from config import settings
from utils.logging_config import setup_logging, get_logger
from utils.errors import YouTubeDownloaderError

# Import database
from database import init_db
from models import User

# Import managers
from auth.oauth import OAuthManager
from auth.session import SessionManager
from auth.cookie_manager import CookieManager
from download.downloader import VideoDownloader
from download.queue import DownloadQueue

# Import routes
from routes import video, auth_routes, user_routes, admin_routes

# Setup logging
setup_logging(settings.log_level, settings.log_file)
logger = get_logger(__name__)

# Global instances
oauth_manager: OAuthManager = None
session_manager: SessionManager = None
cookie_manager: CookieManager = None
downloader: VideoDownloader = None
download_queue: DownloadQueue = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting YouTube Video Downloader application...")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized")
        
        # Create necessary directories
        settings.create_directories()
        logger.info("Created necessary directories")

        # Ensure default settings
        from models.settings import ensure_default_settings
        from database import SessionLocal
        db = SessionLocal()
        try:
             ensure_default_settings(db)
        finally:
             db.close()
        logger.info("Checked default settings")
        
        # Initialize managers
        global session_manager, cookie_manager, oauth_manager, downloader, download_queue
        
        # Session manager
        session_manager = SessionManager()
        logger.info("Initialized session manager")
        
        # Cookie manager
        if settings.is_encryption_configured:
            cookie_manager = CookieManager(settings.cookie_encryption_key)
            logger.info("Initialized cookie manager")
        else:
            logger.warning("Cookie encryption key not configured - authenticated downloads disabled")
        
        # OAuth manager
        if settings.is_oauth_configured:
            oauth_manager = OAuthManager(
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                redirect_uri=settings.oauth_redirect_uri,
                scopes=settings.oauth_scopes
            )
            logger.info("Initialized OAuth manager")
        else:
            logger.warning("OAuth not configured - authentication disabled")
        
        # Video downloader
        downloader = VideoDownloader(
            output_dir=settings.download_output_dir,
            temp_dir=settings.download_temp_dir,
            max_retries=settings.max_retries,
            timeout=settings.download_timeout_seconds
        )
        logger.info("Initialized video downloader")
        
        # Download queue
        download_queue = DownloadQueue(
            downloader=downloader,
            max_concurrent=settings.max_concurrent_downloads_per_user
        )
        
        # Start queue workers
        await download_queue.start_workers()
        logger.info("Started download queue workers")
        
        # Initialize route dependencies
        # Initialize route dependencies
        # if oauth_manager and session_manager and cookie_manager:
        #     auth.init_auth_routes(oauth_manager, session_manager, cookie_manager)
        #     logger.info("Initialized auth routes")
        
        video.init_video_routes(download_queue, downloader, session_manager, cookie_manager)
        logger.info("Initialized video routes")
        
        # Start background cleanup tasks
        asyncio.create_task(periodic_cleanup())
        
        logger.info("Application startup complete")
        
        yield
        
        # Shutdown
        logger.info("Shutting down application...")
        
        # Stop download workers
        if download_queue:
            await download_queue.stop_workers()
            logger.info("Stopped download workers")
        
        logger.info("Application shutdown complete")
    
    except Exception as e:
        logger.error(f"Error during application lifecycle: {e}")
        raise


# Custom 404 handler
async def not_found_handler(request, exc):
    return FileResponse(Path(__file__).parent / "static" / "404.html", status_code=404)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Download YouTube videos with authentication support",
    lifespan=lifespan,
    exception_handlers={404: not_found_handler}
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)  # New authentication system
app.include_router(user_routes.router)  # User credential management
app.include_router(admin_routes.router)  # Admin control panel
app.include_router(video.router)  # Existing video routes

# Keep old OAuth routes for backward compatibility (if configured)
# Keep old OAuth routes for backward compatibility (if configured)
# if settings.is_oauth_configured:
#     app.include_router(auth.router)

# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Root endpoint - serve index.html
@app.get("/")
async def root():
    """Serve the main application page."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "YouTube Video Downloader API", "version": settings.app_version}


# Login and register pages
@app.get("/login")
async def login_page():
    """Serve the login page."""
    login_path = static_dir / "login.html"
    if login_path.exists():
        return FileResponse(login_path)
    return {"message": "Login page not found"}


@app.get("/register")
async def register_page():
    """Serve the registration page."""
    register_path = static_dir / "register.html"
    if register_path.exists():
        return FileResponse(register_path)
    return {"message": "Registration page not found"}


@app.get("/profile")
async def profile_page():
    """Serve the user profile page."""
    profile_path = static_dir / "profile.html"
    if profile_path.exists():
        return FileResponse(profile_path)
    return {"message": "Profile page not found"}


# Admin dashboard
@app.get("/admin")
async def admin_dashboard():
    """Serve the admin dashboard."""
    admin_path = static_dir / "admin" / "index.html"
    if admin_path.exists():
        return FileResponse(admin_path)
    return {"message": "Admin dashboard not found"}


# Admin subpages
@app.get("/admin/users.html")
async def admin_users():
    """Serve the admin users page."""
    users_path = static_dir / "admin" / "users.html"
    if users_path.exists():
        return FileResponse(users_path)
    return {"message": "Admin users page not found"}


@app.get("/admin/settings.html")
async def admin_settings():
    """Serve the admin settings page."""
    settings_path = static_dir / "admin" / "settings.html"
    if settings_path.exists():
        return FileResponse(settings_path)
    return {"message": "Admin settings page not found"}


@app.get("/admin/downloads.html")
async def admin_downloads():
    """Serve the admin downloads page."""
    downloads_path = static_dir / "admin" / "downloads.html"
    if downloads_path.exists():
        return FileResponse(downloads_path)
    return {"message": "Admin downloads page not found"}


@app.get("/admin/logs.html")
async def admin_logs():
    """Serve the admin logs page."""
    logs_path = static_dir / "admin" / "logs.html"
    if logs_path.exists():
        return FileResponse(logs_path)
    return {"message": "Admin logs page not found"}


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "oauth_configured": settings.is_oauth_configured,
        "encryption_configured": settings.is_encryption_configured
    }


# Global exception handler
@app.exception_handler(YouTubeDownloaderError)
async def youtube_downloader_exception_handler(request, exc: YouTubeDownloaderError):
    """Handle custom application exceptions."""
    return HTTPException(
        status_code=exc.status_code,
        detail=exc.message
    )


async def periodic_cleanup():
    """Background task for periodic cleanup."""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            
            # Cleanup expired sessions
            if session_manager:
                session_manager.cleanup_expired()
            
            # Cleanup expired cookies
            if cookie_manager:
                cookie_manager.cleanup_expired()
            
            # Cleanup old downloads
            if download_queue:
                download_queue.cleanup_old_downloads(max_age_hours=24)
            
            logger.info("Periodic cleanup completed")
        
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")


if __name__ == "__main__":
    import uvicorn
    
    # Run the bootstrap check again just in case (fast check)
    check_dependencies()
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
