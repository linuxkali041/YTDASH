"""
Download queue management for concurrent download handling.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional, Callable
from .models import DownloadRequest, DownloadStatus, ProgressUpdate, DownloadStatusResponse
from .downloader import VideoDownloader
from utils.errors import QueueFullError
from utils.logging_config import get_logger
from database import SessionLocal
from models.download_history import Download

logger = get_logger(__name__)


class DownloadQueue:
    """Manages download queue and concurrent downloads."""
    
    def __init__(
        self,
        downloader: VideoDownloader,
        max_concurrent: int = 3
    ):
        """
        Initialize download queue.
        
        Args:
            downloader: VideoDownloader instance
            max_concurrent: Maximum concurrent downloads
        """
        self.downloader = downloader
        self.max_concurrent = max_concurrent
        
        # Queue for pending downloads
        self.queue: asyncio.Queue = asyncio.Queue()
        
        # Active downloads {download_id: task}
        self.active_downloads: Dict[str, asyncio.Task] = {}
        
        # Download metadata {download_id: metadata}
        self.downloads: Dict[str, Dict] = {}
        
        # Progress tracking {download_id: ProgressUpdate}
        self.progress: Dict[str, ProgressUpdate] = {}
        
        # Worker tasks
        self.workers: list = []
        
        logger.info(f"DownloadQueue initialized (max_concurrent: {max_concurrent})")
    
    async def start_workers(self):
        """Start worker tasks to process queue."""
        self.workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_concurrent)
        ]
        logger.info(f"Started {self.max_concurrent} download workers")
    
    async def stop_workers(self):
        """Stop all worker tasks."""
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for cancellation
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        logger.info("Stopped all download workers")
    
    async def _worker(self, worker_id: int):
        """
        Worker task that processes downloads from queue.
        
        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Download worker {worker_id} started")
        
        while True:
            try:
                # Get next download from queue
                download_id, request, cookies = await self.queue.get()
                
                logger.info(f"Worker {worker_id} processing download {download_id}")
                
                # Update status
                self._update_status(download_id, DownloadStatus.DOWNLOADING)
                
                # Perform download
                try:
                    output_file = await self.downloader.download_video(
                        request=request,
                        progress_callback=lambda p: self._update_progress(download_id, p),
                        download_id=download_id,
                        cookies=cookies
                    )
                    
                    # Update as completed
                    self._update_status(download_id, DownloadStatus.COMPLETED)
                    self.downloads[download_id]['output_file'] = str(output_file)
                    # Try to extract filename from path for display
                    self.downloads[download_id]['file_name'] = output_file.name if output_file else None
                    self.downloads[download_id]['completed_at'] = datetime.utcnow().isoformat()
                    
                    logger.info(f"Download {download_id} completed: {output_file}")
                    
                    # Save to history
                    self._save_history(download_id, request)
                
                except Exception as e:
                    # Update as failed
                    self._update_status(download_id, DownloadStatus.FAILED)
                    self.downloads[download_id]['error'] = str(e)
                    self.downloads[download_id]['completed_at'] = datetime.utcnow().isoformat()
                    
                    logger.error(f"Download {download_id} failed: {e}")
                    
                    # Save to history (failed)
                    self._save_history(download_id, request)
                
                finally:
                    # Mark task as done
                    self.queue.task_done()
                    
                    # Remove from active downloads
                    if download_id in self.active_downloads:
                        del self.active_downloads[download_id]
            
            except asyncio.CancelledError:
                logger.info(f"Download worker {worker_id} cancelled")
                break
            
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)  # Brief pause before continuing

    def _save_history(self, download_id: str, request: DownloadRequest):
        """Save completed/failed download to database."""
        try:
            metadata = self.downloads.get(download_id)
            if not metadata or not metadata.get('user_id'):
                return # Skip if no metadata or no user_id
            
            # Create DB session
            # Note: We are in a sync method here, but called from async _worker. 
            # SQLAlchemy sync calls are blocking but acceptable for simple inserts?
            # Ideally verify if SessionLocal is async or sync. 
            # In database.py (typically) SessionLocal is sync (scoped_session).
            # Blocking the event loop is bad, but for lightweight insert it might be just "okay" or we should run_in_executor.
            # Given the existing architecture likely uses sync DB, we'll run it in executor to be safe.
            
            def db_op():
                with SessionLocal() as db:
                    # Check if already exists (unlikely given UUID)
                    existing = db.query(Download).filter(Download.download_id == download_id).first()
                    if existing:
                        return # Already saved
                    
                    download_record = Download(
                        download_id=download_id,
                        user_id=metadata['user_id'],
                        youtube_url=request.url,
                        # video_title parsing is hard without extra info, leaving null or using request data if available
                        format_type=request.format_type.value if hasattr(request.format_type, 'value') else request.format_type,
                        quality=request.quality,
                        format_id=request.format_id,
                        status=metadata['status'],
                        error_message=metadata.get('error'),
                        file_path=metadata.get('output_file'),
                        file_name=metadata.get('file_name'),
                        completed_at=datetime.fromisoformat(metadata['completed_at']) if metadata.get('completed_at') else None
                    )
                    db.add(download_record)
                    db.commit()
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.run_in_executor(None, db_op)
            else:
                db_op() # Fallback
                
            logger.info(f"Saved download history for {download_id}")
            
        except Exception as e:
            logger.error(f"Failed to save download history: {e}")

    def add_download(
        self,
        request: DownloadRequest,
        session_id: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
        user_id: Optional[int] = None
    ) -> str:
        """
        Add download to queue.
        
        Args:
            request: Download request
            session_id: Session ID
            cookies: Optional cookies for authenticated download
            user_id: User ID for history logging
            
        Returns:
            Download ID
            
        Raises:
            QueueFullError: If queue is at capacity
        """
        # Generate download ID
        download_id = str(uuid.uuid4())
        
        # Create download metadata
        self.downloads[download_id] = {
            'download_id': download_id,
            'session_id': session_id,
            'user_id': user_id,
            'url': request.url,
            'status': DownloadStatus.PENDING,
            'created_at': datetime.utcnow().isoformat(),
            'completed_at': None,
            'output_file': None,
            'error': None
        }
        
        # Initialize progress
        self.progress[download_id] = ProgressUpdate(
            download_id=download_id,
            status=DownloadStatus.PENDING,
            progress=0.0
        )
        
        # Add to queue
        self.queue.put_nowait((download_id, request, cookies))
        
        logger.info(f"Added download {download_id} to queue for URL: {request.url}")
        return download_id
    
    def get_download_status(self, download_id: str) -> Optional[DownloadStatusResponse]:
        """
        Get download status.
        
        Args:
            download_id: Download identifier
            
        Returns:
            Download status or None if not found
        """
        if download_id not in self.downloads:
            return None
        
        metadata = self.downloads[download_id]
        progress = self.progress.get(download_id)
        
        return DownloadStatusResponse(
            download_id=download_id,
            status=metadata['status'],
            progress=progress,
            created_at=metadata['created_at'],
            completed_at=metadata.get('completed_at')
        )
    
    def get_download_progress(self, download_id: str) -> Optional[ProgressUpdate]:
        """
        Get download progress.
        
        Args:
            download_id: Download identifier
            
        Returns:
            Progress update or None if not found
        """
        return self.progress.get(download_id)
    
    def cancel_download(self, download_id: str) -> bool:
        """
        Cancel a download.
        
        Args:
            download_id: Download identifier
            
        Returns:
            True if cancelled, False if not found or already completed
        """
        if download_id not in self.downloads:
            return False
        
        metadata = self.downloads[download_id]
        
        # Can't cancel if already completed or failed
        if metadata['status'] in [DownloadStatus.COMPLETED, DownloadStatus.FAILED]:
            return False
        
        # Update status
        self._update_status(download_id, DownloadStatus.CANCELLED)
        metadata['completed_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Cancelled download {download_id}")
        return True
    
    def _update_status(self, download_id: str, status: DownloadStatus):
        """
        Update download status.
        
        Args:
            download_id: Download identifier
            status: New status
        """
        if download_id in self.downloads:
            self.downloads[download_id]['status'] = status
        
        if download_id in self.progress:
            self.progress[download_id].status = status
    
    def _update_progress(self, download_id: str, progress: ProgressUpdate):
        """
        Update download progress.
        
        Args:
            download_id: Download identifier
            progress: Progress update
        """
        self.progress[download_id] = progress
        
        # Also update status in metadata
        if download_id in self.downloads:
            self.downloads[download_id]['status'] = progress.status
    
    def get_queue_size(self) -> int:
        """Get number of pending downloads."""
        return self.queue.qsize()
    
    def get_active_count(self) -> int:
        """Get number of active downloads."""
        return len([
            d for d in self.downloads.values()
            if d['status'] == DownloadStatus.DOWNLOADING
        ])
    
    def cleanup_old_downloads(self, max_age_hours: int = 24) -> int:
        """
        Remove old completed/failed downloads from tracking.
        
        Args:
            max_age_hours: Remove downloads older than this many hours
            
        Returns:
            Number of downloads removed
        """
        from datetime import timedelta
        
        threshold = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        old_downloads = [
            download_id for download_id, metadata in self.downloads.items()
            if metadata['status'] in [DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED]
            and metadata.get('completed_at')
            and datetime.fromisoformat(metadata['completed_at']) < threshold
        ]
        
        for download_id in old_downloads:
            del self.downloads[download_id]
            if download_id in self.progress:
                del self.progress[download_id]
        
        if old_downloads:
            logger.info(f"Cleaned up {len(old_downloads)} old downloads")
        
        return len(old_downloads)
