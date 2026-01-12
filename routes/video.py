"""
Video operation API routes.
"""

from fastapi import APIRouter, HTTPException, Query, Path, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional
from pathlib import Path as FilePath
import os
from download.models import (
    VideoInfoRequest, VideoInfoResponse,
    DownloadRequest, DownloadResponse, DownloadStatus,
    ProgressUpdate, DownloadStatusResponse,
    PlaylistInfoRequest, PlaylistInfoResponse,
    PlaylistDownloadRequest, PlaylistDownloadResponse,
    PlaylistProgressUpdate,
    FormatType
)
from download.downloader import VideoDownloader
from download.queue import DownloadQueue
from auth.session import SessionManager
from auth.cookie_manager import CookieManager
from utils.logging_config import get_logger
from utils.errors import InvalidURLError, VideoUnavailableError, DownloadError, RateLimitError
import uuid

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["video"])


# Dependency containers (will be injected at startup)
download_queue: Optional[DownloadQueue] = None
downloader: Optional[VideoDownloader] = None
session_manager: Optional[SessionManager] = None
cookie_manager: Optional[CookieManager] = None


def init_video_routes(
    queue: DownloadQueue,
    dl: VideoDownloader,
    sessions: SessionManager,
    cookies: CookieManager
):
    """Initialize route dependencies."""
    global download_queue, downloader, session_manager, cookie_manager
    download_queue = queue
    downloader = dl
    session_manager = sessions
    cookie_manager = cookies


@router.post("/video/info", response_model=VideoInfoResponse)
async def get_video_info(request: VideoInfoRequest):
    """
    Get video metadata and available formats.
    
    Args:
        request: Video info request with URL and optional session ID
        
    Returns:
        Video information including available formats
    """
    if not downloader:
        raise HTTPException(status_code=500, detail="Downloader not initialized")
    
    try:
        # Get cookies if available
        cookies = None
        
        # New Global Cookie Logic
        try:
            from database import SessionLocal
            from models import AppSetting
            
            with SessionLocal() as db:
                cookie_setting = db.query(AppSetting).filter(AppSetting.key == "youtube_cookies").first()
                if cookie_setting and cookie_setting.value:
                    cookies = cookie_setting.value
        except Exception as e:
            logger.error(f"Failed to fetch global cookies: {e}")
        
        # Get video info
        video_info = await downloader.get_video_info(request.url, cookies)
        
        logger.info(f"Retrieved info for video: {video_info.title}")
        return video_info
    
    except InvalidURLError as e:
        logger.warning(f"Invalid URL: {request.url}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except VideoUnavailableError as e:
        logger.warning(f"Video unavailable: {request.url}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except RateLimitError as e:
        logger.warning(f"Rate limited: {request.url}")
        raise HTTPException(status_code=429, detail=str(e))
    
    except DownloadError as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error getting video info: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@router.post("/video/download", response_model=DownloadResponse)
async def initiate_download(request: DownloadRequest):
    """
    Initiate video download.
    
    Args:
        request: Download request with URL and format options
        
    Returns:
        Download ID and status
    """
    if not download_queue or not session_manager:
        raise HTTPException(status_code=500, detail="Download service not initialized")
    
    try:
        # Check if session exists and get download limit
        session_id = request.session_id
        session = None
        if session_id:
            session = session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=401, detail="Invalid session")
            
            # Check concurrent download limit
            active_count = session_manager.get_active_download_count(session_id)
            max_concurrent = 3  # Should come from config
            
            if active_count >= max_concurrent:
                raise HTTPException(
                    status_code=429,
                    detail=f"Maximum concurrent downloads ({max_concurrent}) reached"
                )
        
        # Get cookies if available
        cookies = None
        
        # New Global Cookie Logic
        try:
            from database import SessionLocal
            from models import AppSetting
            
            with SessionLocal() as db:
                cookie_setting = db.query(AppSetting).filter(AppSetting.key == "youtube_cookies").first()
                if cookie_setting and cookie_setting.value:
                    cookies = cookie_setting.value
        except Exception as e:
            logger.error(f"Failed to fetch global cookies: {e}")
        
        # Add to download queue
        user_id = session.get('user_id') if session else None
        
        download_id = download_queue.add_download(
            request=request,
            session_id=session_id,
            cookies=cookies,
            user_id=user_id
        )
        
        # Add to session's active downloads
        if session_id:
            session_manager.add_download(session_id, download_id)
        
        logger.info(f"Download initiated: {download_id} for URL: {request.url}")
        
        return DownloadResponse(
            download_id=download_id,
            status=DownloadStatus.PENDING,
            message="Download queued successfully"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error initiating download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/progress/{download_id}", response_model=ProgressUpdate)
async def get_download_progress(download_id: str = Path(...)):
    """
    Get download progress.
    
    Args:
        download_id: Download identifier
        
    Returns:
        Progress update
    """
    if not download_queue:
        raise HTTPException(status_code=500, detail="Download service not initialized")
    
    progress = download_queue.get_download_progress(download_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail="Download not found")
    
    return progress


@router.get("/download/status/{download_id}", response_model=DownloadStatusResponse)
async def get_download_status(download_id: str = Path(...)):
    """
    Get download status.
    
    Args:
        download_id: Download identifier
        
    Returns:
        Download status with metadata
    """
    if not download_queue:
        raise HTTPException(status_code=500, detail="Download service not initialized")
    
    status = download_queue.get_download_status(download_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Download not found")
    
    return status


@router.delete("/download/{download_id}")
async def cancel_download(
    download_id: str = Path(...),
    session_id: Optional[str] = Query(None)
):
    """
    Cancel a download.
    
    Args:
        download_id: Download identifier
        session_id: Session identifier
        
    Returns:
        Cancellation confirmation
    """
    if not download_queue:
        raise HTTPException(status_code=500, detail="Download service not initialized")
    
    # Cancel download
    cancelled = download_queue.cancel_download(download_id)
    
    if not cancelled:
        raise HTTPException(
            status_code=404,
            detail="Download not found or already completed"
        )
    
    # Remove from session if provided
    if session_id and session_manager:
        session_manager.remove_download(session_id, download_id)
    
    logger.info(f"Download cancelled: {download_id}")
    
    return {
        "success": True,
        "download_id": download_id,
        "message": "Download cancelled successfully"
    }


@router.get("/queue/status")
async def get_queue_status():
    """
    Get queue status.
    
    Returns:
        Queue statistics
    """
    if not download_queue:
        raise HTTPException(status_code=500, detail="Download service not initialized")
    
    return {
        "queue_size": download_queue.get_queue_size(),
        "active_downloads": download_queue.get_active_count()
    }


@router.get("/download/file/{download_id}")
async def serve_downloaded_file(
    download_id: str = Path(...), 
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Serve the downloaded file to the client and delete it afterwards (auto-cleanup).
    
    Args:
        download_id: Download identifier
        background_tasks: FastAPI background tasks handler
        
    Returns:
        FileResponse with the downloaded file
    """
    if not download_queue:
        raise HTTPException(status_code=500, detail="Download service not initialized")
    
    # Get download status to retrieve filename
    progress = download_queue.get_download_progress(download_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Download not found")
        
    if progress.status != DownloadStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Download not yet completed (Status: {progress.status})")
        
    if not progress.filename:
        raise HTTPException(status_code=404, detail="File path not found in download record")
    
    # Check if we can find the file path
    file_path = FilePath(progress.filename)
    if not file_path.exists():
        # Try resolving relative to output dir if absolute path fails
        from config import settings
        file_path = settings.download_output_dir / progress.filename
        
    if not file_path.exists():
        logger.error(f"File not found on disk: {file_path}")
        raise HTTPException(status_code=404, detail="File not found on server")
    
    # Define cleanup function
    import asyncio
    async def cleanup_file(path: FilePath):
        try:
            # Wait for 1 hour before deleting to allow slow downloads and retries
            await asyncio.sleep(3600)
            if path.exists():
                os.unlink(path)
                logger.info(f"Auto-cleanup: Deleted file {path}")
        except Exception as e:
            logger.error(f"Auto-cleanup failed for {path}: {e}")
            
    # Add cleanup task to background response
    if background_tasks is None:
        background_tasks = BackgroundTasks()
        
    background_tasks.add_task(cleanup_file, file_path)
        
    # Valid file found, serve it
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream",
        background=background_tasks
    )


# =============================================================================
# Playlist Endpoints
# =============================================================================

@router.post("/playlist/info")
async def get_playlist_info(request: PlaylistInfoRequest):
    """
    Get playlist metadata and video list.
    
    Args:
        request: Playlist info request with URL and optional session ID
        
    Returns:
        Playlist information including video list
    """
    if not downloader:
        raise HTTPException(status_code=500, detail="Downloader not initialized")
    
    try:
        # Get cookies if available
        cookies = None
        try:
            from database import SessionLocal
            from models import AppSetting
            
            with SessionLocal() as db:
                cookie_setting = db.query(AppSetting).filter(AppSetting.key == "youtube_cookies").first()
                if cookie_setting and cookie_setting.value:
                    cookies = cookie_setting.value
        except Exception as e:
            logger.error(f"Failed to fetch global cookies: {e}")
        
        # Get playlist info
        playlist_info = await downloader.get_playlist_info(request.url, cookies)
        
        logger.info(f"Retrieved info for playlist: {playlist_info.title} ({playlist_info.video_count} videos)")
        return playlist_info
    
    except InvalidURLError as e:
        logger.warning(f"Invalid playlist URL: {request.url}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except DownloadError as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error getting playlist info: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@router.post("/playlist/download")
async def initiate_playlist_download(request: PlaylistDownloadRequest):
    """
    Initiate playlist download.
    
    Args:
        request: Playlist download request with URL and format options
        
    Returns:
        Playlist download ID and list of individual download IDs
    """
    if not download_queue or not downloader:
        raise HTTPException(status_code=500, detail="Download service not initialized")
    
    try:
        # Get cookies if available
        cookies = None
        try:
            from database import SessionLocal
            from models import AppSetting
            
            with SessionLocal() as db:
                cookie_setting = db.query(AppSetting).filter(AppSetting.key == "youtube_cookies").first()
                if cookie_setting and cookie_setting.value:
                    cookies = cookie_setting.value
        except Exception as e:
            logger.error(f"Failed to fetch global cookies: {e}")
        
        # Get playlist info to get video list
        playlist_info = await downloader.get_playlist_info(request.url, cookies)
        
        # Determine which videos to download
        videos_to_download = playlist_info.videos
        if request.video_ids:
            # Filter to only selected videos
            videos_to_download = [v for v in videos_to_download if v.video_id in request.video_ids]
        
        if not videos_to_download:
            raise HTTPException(status_code=400, detail="No videos selected for download")
        
        # Create a playlist ID for tracking
        playlist_id = str(uuid.uuid4())
        
        # Queue individual video downloads
        download_ids = []
        for video in videos_to_download:
            # Create download request for each video
            video_request = DownloadRequest(
                url=video.url,
                format_type=request.format_type,
                quality=request.quality,
                audio_format=request.audio_format,
                video_codec=request.video_codec,
                audio_codec=request.audio_codec,
                session_id=request.session_id
            )
            
            # Add to download queue
            # Extract user_id from session if available
            user_id = None
            if request.session_id and session_manager:
                session = session_manager.get_session(request.session_id)
                if session:
                    user_id = session.get('user_id')

            download_id = download_queue.add_download(
                request=video_request,
                session_id=request.session_id,
                cookies=cookies,
                user_id=user_id
            )
            download_ids.append(download_id)
            
            # Store playlist association (we'll need to track this)
            # For now, we'll use a simple in-memory dict
            if not hasattr(download_queue, 'playlist_downloads'):
                download_queue.playlist_downloads = {}
            
            if playlist_id not in download_queue.playlist_downloads:
                download_queue.playlist_downloads[playlist_id] = {
                    'download_ids': [],
                    'title': playlist_info.title,
                    'total': len(videos_to_download)
                }
            
            download_queue.playlist_downloads[playlist_id]['download_ids'].append(download_id)
        
        logger.info(f"Playlist download initiated: {playlist_id} with {len(download_ids)} videos")
        
        return PlaylistDownloadResponse(
            playlist_id=playlist_id,
            download_ids=download_ids,
            total_videos=len(videos_to_download),
            message=f"Playlist download initiated with {len(videos_to_download)} videos"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error initiating playlist download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/playlist/progress/{playlist_id}")
async def get_playlist_progress(playlist_id: str = Path(...)):
    """
    Get playlist download progress.
    
    Args:
        playlist_id: Playlist download identifier
        
    Returns:
        Aggregate progress for all videos in playlist
    """
    if not download_queue:
        raise HTTPException(status_code=500, detail="Download service not initialized")
    
    # Get playlist info from tracking dict
    if not hasattr(download_queue, 'playlist_downloads'):
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    playlist_data = download_queue.playlist_downloads.get(playlist_id)
    if not playlist_data:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Get progress for each video
    video_progress_list = []
    completed = 0
    failed = 0
    downloading = 0
    pending = 0
    
    for download_id in playlist_data['download_ids']:
        progress = download_queue.get_download_progress(download_id)
        if progress:
            video_progress_list.append(progress)
            
            if progress.status == DownloadStatus.COMPLETED:
                completed += 1
            elif progress.status == DownloadStatus.FAILED:
                failed += 1
            elif progress.status == DownloadStatus.DOWNLOADING:
                downloading += 1
            elif progress.status == DownloadStatus.PENDING:
                pending += 1
    
    # Calculate overall progress
    total = playlist_data['total']
    overall_progress = (completed / total * 100) if total > 0 else 0
    
    return PlaylistProgressUpdate(
        playlist_id=playlist_id,
        total_videos=total,
        completed_videos=completed,
        failed_videos=failed,
        downloading_videos=downloading,
        pending_videos=pending,
        overall_progress=overall_progress,
        video_progress=video_progress_list
    )
