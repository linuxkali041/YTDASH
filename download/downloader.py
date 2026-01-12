"""
Core download functionality using yt-dlp.
Handles video metadata extraction, downloading, and progress tracking.
"""

import asyncio
import time
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional, Callable, List
import yt_dlp
from .models import (
    VideoInfoResponse, FormatOption, DownloadRequest,
    ProgressUpdate, DownloadStatus, FormatType
)
from utils.errors import DownloadError, InvalidURLError, VideoUnavailableError, RateLimitError
from utils.validators import sanitize_filename, validate_youtube_url
from utils.logging_config import get_logger

logger = get_logger(__name__)


class VideoDownloader:
    """Handles video downloading using yt-dlp."""
    
    def __init__(
        self,
        output_dir: Path,
        temp_dir: Path,
        max_retries: int = 3,
        timeout: int = 3600
    ):
        """
        Initialize video downloader.
        
        Args:
            output_dir: Directory for completed downloads
            temp_dir: Directory for temporary files
            max_retries: Maximum retry attempts
            timeout: Download timeout in seconds
        """
        self.output_dir = output_dir
        self.temp_dir = temp_dir
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"VideoDownloader initialized (output: {output_dir}, temp: {temp_dir})")
    
    def _create_cookie_file(self, cookie_content: str) -> str:
        """
        Create a temporary Netscape cookie file from content.
        
        Args:
            cookie_content: Raw Netscape cookie file content
            
        Returns:
            Path to the temporary file
        """
        if not cookie_content:
            return None
            
        fd, path = tempfile.mkstemp(suffix='.txt', dir=str(self.temp_dir), text=True)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(cookie_content)
            return path
        except Exception as e:
            logger.error(f"Failed to create cookie file: {e}")
            if os.path.exists(path):
                try:
                    os.unlink(path)
                except:
                    pass
            raise
    

    
    def _get_base_ydl_opts(self, cookies: Optional[str] = None) -> Dict:
        """
        Get base yt-dlp options.
        
        Args:
            cookies: Optional cookie content string
            
        Returns:
            yt-dlp options dictionary
        """
        opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'socket_timeout': 30,
            'retries': self.max_retries,
            'fragment_retries': self.max_retries,
            'skip_unavailable_fragments': True,
            'keepvideo': False,
            'noprogress': False,
            'no_color': True,
            # Add user agent to avoid bot detection
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        return opts
    
    async def get_video_info(
        self,
        url: str,
        cookies: Optional[str] = None
    ) -> VideoInfoResponse:
        """
        Extract video metadata.
        
        Args:
            url: YouTube video URL
            cookies: Optional cookies for authenticated requests
            
        Returns:
            VideoInfoResponse with metadata and available formats
            
        Raises:
            InvalidURLError: If URL is invalid
            VideoUnavailableError: If video is unavailable
            DownloadError: If extraction fails
        """
        # Validate URL
        try:
            url = validate_youtube_url(url)
        except InvalidURLError as e:
            logger.error(f"Invalid URL: {url}")
            raise
        
        # Configure yt-dlp options
        ydl_opts = self._get_base_ydl_opts(cookies)
        ydl_opts.update({
            'skip_download': True,
            'quiet': True,
            'ignore_no_formats_error': True,
            'allow_unplayable_formats': True,
        })
        
        cookie_file = None
        if cookies:
            try:
                cookie_file = self._create_cookie_file(cookies)
                ydl_opts['cookiefile'] = cookie_file
            except Exception as e:
                logger.warning(f"Failed to process cookies: {e}")
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                self._extract_info_sync,
                url,
                ydl_opts
            )
            
            # Parse and return info
            if not info:
                raise DownloadError(f"Failed to extract video info (result is None/Empty)", url=url)
                
            return self._parse_video_info(info)
            
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            
            if 'Sign in to confirm' in error_msg:
                raise DownloadError("YouTube requires authentication (Sign-in to confirm you're not a bot). Please update your cookies.", url=url)
            elif 'This video is unavailable' in error_msg or 'Private video' in error_msg:
                logger.error(f"Video unavailable: {url}")
                raise VideoUnavailableError(f"Video unavailable: {error_msg}", url=url)
            elif 'HTTP Error 429' in error_msg or 'Too Many Requests' in error_msg:
                logger.error(f"Rate limited: {url}")
                raise RateLimitError("YouTube rate limit exceeded")
            else:
                logger.error(f"Download error for {url}: {error_msg}")
                raise DownloadError(f"Failed to get video info: {error_msg}", url=url)
        
        except Exception as e:
            logger.error(f"Unexpected error getting video info for {url}: {e}")
            raise DownloadError(f"Failed to get video info: {e}", url=url)
            
        finally:
            # Cleanup cookie file
            if cookie_file and os.path.exists(cookie_file):
                try:
                    os.unlink(cookie_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temp cookie file: {e}")
            

    
    def _extract_info_sync(self, url: str, ydl_opts: Dict) -> Dict:
        """
        Synchronous wrapper for yt-dlp extraction.
        
        Args:
            url: Video URL
            ydl_opts: yt-dlp options
            
        Returns:
            Video info dictionary
        """
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    
    def _parse_video_info(self, info: Dict) -> VideoInfoResponse:
        """
        Parse yt-dlp info dict into VideoInfoResponse.
        
        Args:
            info: yt-dlp info dictionary
            
        Returns:
            VideoInfoResponse
        """
        # Extract formats
        formats = []
        if 'formats' in info:
            for fmt in info['formats']:
                # Skip formats without proper ID
                if not fmt.get('format_id'):
                    continue
                
                formats.append(FormatOption(
                    format_id=fmt['format_id'],
                    ext=fmt.get('ext', 'unknown'),
                    resolution=fmt.get('resolution'),
                    fps=fmt.get('fps'),
                    vcodec=fmt.get('vcodec'),
                    acodec=fmt.get('acodec'),
                    abr=fmt.get('abr'),
                    filesize=fmt.get('filesize'),
                    filesize_approx=fmt.get('filesize_approx'),
                    format_note=fmt.get('format_note')
                ))
        
        return VideoInfoResponse(
            video_id=info['id'],
            title=info['title'],
            duration=info.get('duration', 0),
            thumbnail=info.get('thumbnail', ''),
            uploader=info.get('uploader'),
            view_count=info.get('view_count'),
            like_count=info.get('like_count'),
            description=info.get('description'),
            upload_date=info.get('upload_date'),
            formats=formats
        )
    
    async def download_video(
        self,
        request: DownloadRequest,
        progress_callback: Optional[Callable[[ProgressUpdate], None]] = None,
        download_id: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None
    ) -> Path:
        """
        Download video.
        
        Args:
            request: Download request with options
            progress_callback: Optional callback for progress updates
            download_id: Download identifier for progress tracking
            cookies: Optional cookies for authenticated requests
            
        Returns:
            Path to downloaded file
            
        Raises:
            DownloadError: If download fails
        """
        # Validate URL
        url = validate_youtube_url(request.url)
        
        # Build format selector
        format_selector = self._build_format_selector(request)
        
        # Sanitize output template
        output_template = str(self.output_dir / '%(title)s.%(ext)s')
        
        # Configure yt-dlp options
        ydl_opts = self._get_base_ydl_opts(cookies)
        ydl_opts.update({
            'format': format_selector,
            'outtmpl': output_template,
            'merge_output_format': 'mp4' if request.format_type != FormatType.AUDIO else None,
            'postprocessors': [],
        })
        
        # Add audio extraction if needed
        if request.format_type == FormatType.AUDIO:
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': request.audio_format if request.audio_format != 'best' else 'm4a',
                'preferredquality': '192',
            })
        
        # Add progress hook
        if progress_callback and download_id:
            ydl_opts['progress_hooks'] = [
                lambda d: self._progress_hook(d, progress_callback, download_id)
            ]
            
        cookie_file = None
        if cookies:
            try:
                cookie_file = self._create_cookie_file(cookies)
                ydl_opts['cookiefile'] = cookie_file
            except Exception as e:
                logger.warning(f"Failed to process cookies: {e}")
        
        try:
            # Run download in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._download_sync,
                url,
                ydl_opts
            )
            
            # Get output file path
            output_file = Path(result['filepath']) if 'filepath' in result else None
            
            if not output_file or not output_file.exists():
                raise DownloadError("Download completed but file not found", url=url)
            
            logger.info(f"Download completed: {output_file}")
            return output_file
            
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            logger.error(f"Download failed for {url}: {error_msg}")
            
            if progress_callback and download_id:
                progress_callback(ProgressUpdate(
                    download_id=download_id,
                    status=DownloadStatus.FAILED,
                    error=error_msg
                ))
            
            raise DownloadError(f"Download failed: {error_msg}", url=url)
        
        except Exception as e:
            logger.error(f"Unexpected download error for {url}: {e}")
            
            if progress_callback and download_id:
                progress_callback(ProgressUpdate(
                    download_id=download_id,
                    status=DownloadStatus.FAILED,
                    error=str(e)
                ))
            
            raise DownloadError(f"Download failed: {e}", url=url)
            
        finally:
            # Cleanup cookie file
            if cookie_file and os.path.exists(cookie_file):
                try:
                    os.unlink(cookie_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temp cookie file: {e}")
    
    def _download_sync(self, url: str, ydl_opts: Dict) -> Dict:
        """
        Synchronous download wrapper.
        
        Args:
            url: Video URL
            ydl_opts: yt-dlp options
            
        Returns:
            Download result info
        """
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Get the actual file path
            if 'requested_downloads' in info and info['requested_downloads']:
                filepath = info['requested_downloads'][0].get('filepath')
            else:
                filepath = ydl.prepare_filename(info)
            
            return {
                'info': info,
                'filepath': filepath
            }
    
    def _build_format_selector(self, request: DownloadRequest) -> str:
        """
        Build yt-dlp format selector string.
        
        Args:
            request: Download request
            
        Returns:
            Format selector string
        """
        if request.format_id:
            # Use specific format ID
            return request.format_id
        
        if request.format_type == FormatType.AUDIO:
            # Audio only
            return 'bestaudio/best'
        
        # Build video format selector based on quality and codec preferences
        quality_map = {
            'best': 'best',
            'worst': 'worst',
            '2160p': 'bestvideo[height<=2160]+bestaudio/best',
            '1440p': 'bestvideo[height<=1440]+bestaudio/best',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best',
            '720p': 'bestvideo[height<=720]+bestaudio/best',
            '480p': 'bestvideo[height<=480]+bestaudio/best',
            '360p': 'bestvideo[height<=360]+bestaudio/best',
            '240p': 'bestvideo[height<=240]+bestaudio/best',
            '144p': 'bestvideo[height<=144]+bestaudio/best',
        }
        
        format_str = quality_map.get(request.quality, 'best')
        
        # Add codec preference if specified
        if request.video_codec and request.quality != 'best':
            format_str = f'bestvideo[height<={request.quality[:-1]}][vcodec*={request.video_codec}]+bestaudio/best'
        
        return format_str
    
    def _progress_hook(
        self,
        data: Dict,
        callback: Callable[[ProgressUpdate], None],
        download_id: str
    ):
        """
        Progress hook for yt-dlp.
        
        Args:
            data: Progress data from yt-dlp
            callback: Progress callback function
            download_id: Download identifier
        """
        status = data.get('status')
        
        if status == 'downloading':
            downloaded = data.get('downloaded_bytes', 0)
            total = data.get('total_bytes') or data.get('total_bytes_estimate')
            speed = data.get('speed')
            eta = data.get('eta')
            
            progress = (downloaded / total * 100) if total else 0
            
            callback(ProgressUpdate(
                download_id=download_id,
                status=DownloadStatus.DOWNLOADING,
                progress=progress,
                downloaded_bytes=downloaded,
                total_bytes=total,
                speed=speed,
                eta=eta,
                filename=data.get('filename')
            ))
        
        elif status == 'finished':
            callback(ProgressUpdate(
                download_id=download_id,
                status=DownloadStatus.PROCESSING,
                progress=100.0,
                filename=data.get('filename')
            ))
    
    async def get_playlist_info(
        self,
        url: str,
        cookies: Optional[str] = None
    ):
        """
        Extract playlist metadata and video list.
        
        Args:
            url: YouTube playlist URL
            cookies: Optional cookies for authenticated requests
            
        Returns:
            PlaylistInfoResponse with metadata and video list
            
        Raises:
            InvalidURLError: If URL is invalid
            DownloadError: If extraction fails
        """
        from .models import PlaylistInfoResponse, PlaylistVideoInfo
        
        # Configure yt-dlp options for playlist extraction
        ydl_opts = self._get_base_ydl_opts(cookies)
        ydl_opts.update({
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'quiet': True,
        })
        
        cookie_file = None
        if cookies:
            try:
                cookie_file = self._create_cookie_file(cookies)
                ydl_opts['cookiefile'] = cookie_file
            except Exception as e:
                logger.warning(f"Failed to process cookies: {e}")
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                self._extract_info_sync,
                url,
                ydl_opts
            )
            
            # Parse playlist info
            if not info:
                raise DownloadError(f"Failed to extract playlist info", url=url)
            
            # Check if it's actually a playlist
            if '_type' not in info or info['_type'] != 'playlist':
                raise InvalidURLError("URL does not appear to be a playlist")
            
            # Extract video information
            videos = []
            if 'entries' in info:
                for entry in info['entries']:
                    if not entry:  # Skip None entries (unavailable videos)
                        continue
                    
                    videos.append(PlaylistVideoInfo(
                        video_id=entry.get('id', ''),
                        title=entry.get('title', 'Unknown'),
                        duration=entry.get('duration'),
                        thumbnail=entry.get('thumbnail'),
                        url=entry.get('url', f"https://www.youtube.com/watch?v={entry.get('id')}")
                    ))
            
            return PlaylistInfoResponse(
                playlist_id=info.get('id', ''),
                title=info.get('title', 'Unknown Playlist'),
                uploader=info.get('uploader') or info.get('channel'),
                video_count=len(videos),
                description=info.get('description'),
                videos=videos
            )
            
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            logger.error(f"Failed to extract playlist info for {url}: {error_msg}")
            raise DownloadError(f"Failed to get playlist info: {error_msg}", url=url)
        
        except Exception as e:
            logger.error(f"Unexpected error getting playlist info for {url}: {e}")
            raise DownloadError(f"Failed to get playlist info: {e}", url=url)
        
        finally:
            # Cleanup cookie file
            if cookie_file and os.path.exists(cookie_file):
                try:
                    os.unlink(cookie_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temp cookie file: {e}")

