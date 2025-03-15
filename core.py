import os
import sys
import json
import logging
from typing import Dict, List, Optional, Tuple, Union
import yt_dlp
import shutil
import re
import time
from datetime import datetime
from tqdm import tqdm

# Create a global tqdm instance to track progress
progress_bar = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('yt_downloader')

class YouTubeDownloader:
    """Core functionality for YouTube downloader."""
    
    def __init__(self, output_dir: str = "./downloads"):
        """
        Initialize the YouTube downloader.
        
        Args:
            output_dir: Directory where downloads will be saved
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self) -> None:
        """Ensure the output directory exists."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")

    def _file_exists(self, file_path: str) -> bool:
        """
        Check if a file already exists.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file exists, False otherwise
        """
        return os.path.isfile(file_path)       
    
    def _get_video_formats(self, url: str) -> List[Dict]:
        """
        Get available formats for a video.
        
        Args:
            url: YouTube video URL
            
        Returns:
            List of available formats
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'dump_single_json': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                return formats
        except Exception as e:
            logger.error(f"Error getting video formats: {str(e)}")
            return []
    
    def list_formats(self, url: str) -> List[Dict[str, Union[str, int]]]:
        """
        List available formats for a video in a simplified format.
        
        Args:
            url: YouTube video URL
            
        Returns:
            List of dictionaries with format information
        """
        formats = self._get_video_formats(url)
        simplified_formats = []
        
        for fmt in formats:
            format_info = {
                'format_id': fmt.get('format_id', 'unknown'),
                'ext': fmt.get('ext', 'unknown'),
                'resolution': fmt.get('resolution', 'unknown'),
                'fps': fmt.get('fps', 'N/A'),
                'vcodec': fmt.get('vcodec', 'none'),
                'acodec': fmt.get('acodec', 'none'),
                'filesize': fmt.get('filesize', 'unknown'),
                'type': 'audio only' if fmt.get('vcodec') == 'none' else 
                       'video only' if fmt.get('acodec') == 'none' else 'video+audio'
            }
            simplified_formats.append(format_info)
        
        return simplified_formats
    
    def download_video(self, url: str, format_id: Optional[str] = None, 
                       audio_only: bool = False, output_template: str = "%(title)s.%(ext)s") -> str:
        """
        Download a single video from YouTube.
        
        Args:
            url: YouTube video URL
            format_id: Format ID to download (None for best)
            audio_only: If True, download audio only
            output_template: Output filename template
            
        Returns:
            Path to downloaded file
        """
        output_path = os.path.join(self.output_dir, output_template)
        
        ydl_opts = {
            'outtmpl': output_path,
            'logger': logger,
            'progress_hooks': [self._progress_hook],
        }
        
        if audio_only:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        elif format_id:
            ydl_opts['format'] = format_id
        else:
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best'
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)
                
                # If audio only, the extension will be changed by the postprocessor
                if audio_only:
                    file_base = os.path.splitext(downloaded_file)[0]
                    downloaded_file = f"{file_base}.mp3"
                
                return downloaded_file
        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            raise

    def _search_youtube_music(self, title: str) -> str:
        """
        Search for a track on YouTube Music by title.
        
        Args:
            title: Title of the track to search for
            
        Returns:
            URL of the first search result, or None if no results found
        """
        logger.info(f"Searching YouTube Music for: {title}")
        search_query = f"ytsearch:'{title}'"
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                if info and 'entries' in info and len(info['entries']) > 0:
                    result = info['entries'][0]
                    video_id = result.get('id')
                    if video_id:
                        url = f"https://www.youtube.com/watch?v={video_id}"
                        logger.info(f"Found match: {result.get('title')} ({url})")
                        return url
        except Exception as e:
            logger.error(f"Error during YouTube Music search: {str(e)}")
        
        logger.error(f"No matches found for: {title}")
        return None
    
    def download_playlist(self, url: str, audio_only: bool = False, 
                  format_id: Optional[str] = None, 
                  start_index: Optional[int] = None,
                  end_index: Optional[int] = None,
                  specific_index: Optional[int] = None,
                  skip_existing: bool = True) -> List[str]:
        """
        Download a playlist from YouTube.
        
        Args:
            url: YouTube playlist URL
            audio_only: If True, download audio only
            format_id: Format ID to download (None for best)
            start_index: Start downloading from this index (1-based, inclusive)
            end_index: Download until this index (1-based, inclusive)
            specific_index: Download only this specific item in the playlist
            skip_existing: If True, skip files that already exist
            
        Returns:
            List of paths to downloaded files
        """
        # Get the playlist info first to have titles for potential fallback
        playlist_info = self.get_info(url)
        
        # Custom error handler for yt-dlp
        def error_handler(e):
            if not audio_only:
                return  # Only apply fallback for audio-only mode
            
            # Check if this is a "video unavailable" error
            if isinstance(e, yt_dlp.utils.DownloadError) and "Video unavailable" in str(e):
                # Extract the video ID from the error message
                error_msg = str(e)
                video_id_match = re.search(r'\[youtube\] ([a-zA-Z0-9_-]+):', error_msg)
                if not video_id_match:
                    return  # Can't extract video ID
                    
                video_id = video_id_match.group(1)
                
                # Find the corresponding title in the playlist
                video_title = None
                video_index = None
                for i, video in enumerate(playlist_info['videos']):
                    if video['id'] == video_id:
                        video_title = video['title']
                        video_index = i + 1  # 1-based index
                        break
                
                if not video_title:
                    return  # Can't find the title
                    
                logger.info(f"Video unavailable: {video_title} - Attempting fallback search")
                
                # Search for the track on YouTube Music
                fallback_url = self._search_youtube_music(video_title)
                if fallback_url:
                    try:
                        # Create output template for this file to keep playlist numbering
                        playlist_folder = os.path.abspath(os.path.join(self.output_dir, playlist_info['title']))
                        os.makedirs(playlist_folder, exist_ok=True)

                        
                        output_template = os.path.join(playlist_folder, f"{video_index:03d} - %(title)s.%(ext)s")
                        print(self.output_dir)
                        # Download the fallback track
                        downloaded_file = self.download_video(
                            fallback_url, 
                            audio_only=True,
                            output_template=output_template
                        )
                        
                        if downloaded_file:
                            logger.info(f"Successfully downloaded fallback for: {video_title}")

                            # Add manually to archive.txt
                            archive_path = os.path.join(self.output_dir, "archive.txt")
                            with open(archive_path, "a") as archive_file:
                                archive_file.write(f"youtube {video_id}\n")
                            
                            return downloaded_file

                    except Exception as fallback_error:
                        logger.error(f"Fallback download failed: {str(fallback_error)}")
        
        # Force noplaylist=False to ensure playlist extraction
        ydl_opts = {
            'outtmpl': os.path.join(self.output_dir, '%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s'),
            'logger': logger,
            'progress_hooks': [self._progress_hook],
            'ignoreerrors': True,  # Change to False to catch errors
            'noplaylist': False,   # Ensure playlists are processed as playlists
            'extract_flat': False,  # Force full extraction
            'match_filter': None,  # Custom match filter instead of ignoreerrors
        }

        # Add skip_existing option
        if skip_existing:
            ydl_opts['download_archive'] = os.path.join(self.output_dir, 'archive.txt')
        
        # Convert YouTube Music URLs to standard YouTube URLs if needed
        if 'music.youtube.com' in url:
            logger.info("Detected YouTube Music URL, extracting playlist info...")
            # Keep the playlist ID, which should work with both YouTube and YouTube Music
            ydl_opts['compat_opts'] = ['no-youtube-unavailable-videos']
        
        # Handle playlist indices
        if specific_index is not None:
            ydl_opts['playliststart'] = specific_index
            ydl_opts['playlistend'] = specific_index
            logger.info(f"Downloading only playlist item #{specific_index}")
        else:
            # Handle start and end indices
            if start_index is not None:
                ydl_opts['playliststart'] = start_index
                logger.info(f"Starting from playlist item #{start_index}")
            
            if end_index is not None:
                ydl_opts['playlistend'] = end_index
                logger.info(f"Ending at playlist item #{end_index}")
        
        if audio_only:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        elif format_id:
            ydl_opts['format'] = format_id
        else:
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best'
        
        downloaded_files = []
        
        try:
            class YoutubeDLWithFallback(yt_dlp.YoutubeDL):
                def report_error(self, message, tb=None):
                    # Override the error reporting to add our custom fallback
                    super().report_error(message, tb)
                    
                    # If we're in audio-only mode, try the fallback
                    if audio_only and "Video unavailable" in message:
                        fallback_file = error_handler(yt_dlp.utils.DownloadError(message))
                        if fallback_file:
                            downloaded_files.append(fallback_file)
            
            with YoutubeDLWithFallback(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if 'entries' in info:
                    valid_index = 1  # Tracks valid numbering
                    for entry in info['entries']:
                        if not entry:
                            continue  # Skip missing entries

                        try:
                            output_template = os.path.join(self.output_dir, f"{valid_index:03d} - %(title)s.%(ext)s")
                            file_path = self.download_video(entry['url'], audio_only=audio_only, output_template=output_template)

                            if file_path:
                                downloaded_files.append(file_path)
                                valid_index += 1  # Increment only for successfully downloaded files

                        except Exception as e:
                            logger.error(f"Skipping {entry.get('title', 'Unknown Video')} due to error: {str(e)}")
                        
                return downloaded_files
        except Exception as e:
            logger.error(f"Playlist download failed: {str(e)}")
            raise

    def get_info(self, url: str) -> Dict:
        """
        Get information about a video or playlist.
        
        Args:
            url: YouTube URL
            
        Returns:
            Dictionary with video/playlist information
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': 'in_playlist',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Determine if it's a playlist
                if 'entries' in info:
                    # It's a playlist
                    playlist_info = {
                        'type': 'playlist',
                        'title': info.get('title', 'Unknown Playlist'),
                        'id': info.get('id', 'Unknown ID'),
                        'uploader': info.get('uploader', 'Unknown Uploader'),
                        'video_count': len(info['entries']),
                        'videos': []
                    }
                    
                    for entry in info['entries']:
                        if entry:
                            video_info = {
                                'title': entry.get('title', 'Unknown Title'),
                                'id': entry.get('id', 'Unknown ID'),
                                'duration': entry.get('duration', 'Unknown Duration'),
                                'uploader': entry.get('uploader', 'Unknown Uploader'),
                            }
                            playlist_info['videos'].append(video_info)
                            
                    return playlist_info
                else:
                    # It's a single video
                    video_info = {
                        'type': 'video',
                        'title': info.get('title', 'Unknown Title'),
                        'id': info.get('id', 'Unknown ID'),
                        'duration': info.get('duration', 'Unknown Duration'),
                        'uploader': info.get('uploader', 'Unknown Uploader'),
                        'view_count': info.get('view_count', 'Unknown Views'),
                        'upload_date': info.get('upload_date', 'Unknown Upload Date'),
                        'thumbnail': info.get('thumbnail', 'No thumbnail'),
                        'description': info.get('description', 'No description'),
                    }
                    return video_info
        except Exception as e:
            logger.error(f"Error getting info: {str(e)}")
            raise

    def _progress_hook(self, d: Dict) -> None:
        """Progress hook for yt-dlp with tqdm progress bar."""
        global progress_bar
        
        if d['status'] == 'downloading':
            filename = os.path.basename(d.get('filename', 'unknown'))
            
            if progress_bar is None:
                total = d.get('total_bytes', d.get('total_bytes_estimate', 0))
                progress_bar = tqdm(
                    total=total, unit='B', unit_scale=True, desc=filename, dynamic_ncols=True
                )

            downloaded = d.get('downloaded_bytes', 0)
            progress_bar.n = downloaded
            progress_bar.refresh()

        elif d['status'] == 'finished':
            if progress_bar is not None:
                progress_bar.close()
                progress_bar = None
            print(f"✓ Downloaded: {os.path.basename(d.get('filename', 'file'))}")

    