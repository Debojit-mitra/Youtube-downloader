import os
import sys
import argparse
import textwrap
import logging
from typing import List, Optional

from core import YouTubeDownloader, logger

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="YouTube Downloader - Download videos and playlists from YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
        Examples:
          # Download a single video in best quality
          python yt_downloader_cli.py -u https://www.youtube.com/watch?v=dQw4w9WgXcQ
          
          # Download audio only
          python yt_downloader_cli.py -u https://www.youtube.com/watch?v=dQw4w9WgXcQ --audio-only
          
          # List available formats
          python yt_downloader_cli.py -u https://www.youtube.com/watch?v=dQw4w9WgXcQ --list-formats
          
          # Download with specific format
          python yt_downloader_cli.py -u https://www.youtube.com/watch?v=dQw4w9WgXcQ -f 22
          
          # Download a playlist
          python yt_downloader_cli.py -u https://www.youtube.com/playlist?list=PLExample --playlist
          
          # Download a playlist as audio only
          python yt_downloader_cli.py -u https://www.youtube.com/playlist?list=PLExample --playlist --audio-only
          
          # Download a specific item from a playlist (e.g., item #237)
          python yt_downloader_cli.py -u https://www.youtube.com/playlist?list=PLExample --playlist --item 237 --audio-only
          
          # Download a playlist starting from a specific item
          python yt_downloader_cli.py -u https://www.youtube.com/playlist?list=PLExample --playlist --start 50
          
          # Download a range of items from a playlist
          python yt_downloader_cli.py -u https://www.youtube.com/playlist?list=PLExample --playlist --start 50 --end 60
          
          # Get info about a video or playlist
          python yt_downloader_cli.py -u https://www.youtube.com/watch?v=dQw4w9WgXcQ --info
        ''')
    )
    
    parser.add_argument("-u", "--url", type=str, help="URL of the YouTube video or playlist")
    parser.add_argument("-o", "--output-dir", type=str, default="./downloads",
                      help="Directory to save the downloaded files (default: ./downloads)")
    
    # Actions
    action_group = parser.add_argument_group("Actions")
    action_group.add_argument("--list-formats", action="store_true", 
                            help="List available formats for the video")
    action_group.add_argument("--info", action="store_true",
                            help="Get information about the video or playlist")
    action_group.add_argument("--playlist", action="store_true",
                            help="Download as playlist")
                            
    # Options
    options_group = parser.add_argument_group("Options")
    options_group.add_argument("-f", "--format", type=str,
                             help="Format code to download (use --list-formats to see available formats)")
    options_group.add_argument("--audio-only", action="store_true",
                             help="Download audio only")
    options_group.add_argument("-v", "--verbose", action="store_true",
                             help="Increase output verbosity")
    options_group.add_argument("--skip-existing", action="store_true", default=True,
                            help="Skip files that already exist (default: True)")
    options_group.add_argument("--no-skip-existing", dest="skip_existing", action="store_false",
                            help="Do not skip files that already exist")
                             
    # Playlist options
    playlist_group = parser.add_argument_group("Playlist Options")
    playlist_group.add_argument("--item", type=int,
                              help="Download only the specified item number from the playlist (1-based)")
    playlist_group.add_argument("--start", type=int,
                              help="Start downloading from this item number (1-based)")
    playlist_group.add_argument("--end", type=int,
                              help="Download until this item number (1-based)")
    
    args = parser.parse_args()
    
    # URL is required unless help is requested
    if not args.url and len(sys.argv) > 1 and not ("-h" in sys.argv or "--help" in sys.argv):
        parser.error("URL is required")
    
    # Validate playlist options
    if args.item and (args.start or args.end):
        parser.error("Cannot use --item with --start or --end")
    
    if args.start and args.end and args.start > args.end:
        parser.error("Start index must be less than or equal to end index")
    
    if (args.item or args.start or args.end) and not args.playlist:
        parser.error("Playlist options require --playlist flag")
        
    return args

def list_formats(downloader: YouTubeDownloader, url: str) -> None:
    """List available formats for a video."""
    print(f"Available formats for {url}:")
    print("{:<10} {:<8} {:<12} {:<6} {:<25}".format(
        "Format ID", "Ext", "Resolution", "FPS", "Type"))
    print("-" * 80)
    
    formats = downloader.list_formats(url)
    for fmt in formats:
        print("{:<10} {:<8} {:<12} {:<6} {:<25}".format(
            fmt['format_id'],
            fmt['ext'],
            fmt['resolution'],
            fmt['fps'],
            fmt['type']
        ))

def show_info(downloader: YouTubeDownloader, url: str) -> None:
    """Show information about a video or playlist."""
    info = downloader.get_info(url)
    
    if info['type'] == 'video':
        print("\n===== VIDEO INFORMATION =====")
        print(f"Title: {info['title']}")
        print(f"ID: {info['id']}")
        print(f"Uploader: {info['uploader']}")
        print(f"Duration: {info['duration']} seconds")
        print(f"View Count: {info['view_count']}")
        print(f"Upload Date: {info['upload_date']}")
        print("\nDescription:")
        
        # Print description with line wrapping
        if info['description']:
            wrapper = textwrap.TextWrapper(width=80, initial_indent="  ", subsequent_indent="  ")
            print(wrapper.fill(info['description']))
        else:
            print("  No description available")
    else:
        print("\n===== PLAYLIST INFORMATION =====")
        print(f"Title: {info['title']}")
        print(f"ID: {info['id']}")
        print(f"Uploader: {info['uploader']}")
        print(f"Video Count: {info['video_count']}")
        
        print("\nVideos in playlist:")
        for i, video in enumerate(info['videos'], 1):
            print(f"{i}. {video['title']} (ID: {video['id']})")
            if i >= 10 and len(info['videos']) > 15:
                remaining = len(info['videos']) - i
                print(f"... and {remaining} more videos")
                break

def main() -> None:
    """Main function to run the CLI."""
    args = parse_arguments()
    
    # Set up logging verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    downloader = YouTubeDownloader(output_dir=args.output_dir)
    
    try:
        if args.list_formats:
            list_formats(downloader, args.url)
        elif args.info:
            show_info(downloader, args.url)
        elif args.playlist:
            print(f"Downloading playlist: {args.url}")
            print(f"{'Audio only mode' if args.audio_only else 'Video mode'}")
            
            # Handle playlist options
            if args.item:
                print(f"Downloading only item #{args.item}")
                files = downloader.download_playlist(
                    args.url, 
                    audio_only=args.audio_only,
                    format_id=args.format,
                    specific_index=args.item,
                    skip_existing=args.skip_existing
                )
            else:
                if args.start:
                    print(f"Starting from item #{args.start}")
                if args.end:
                    print(f"Ending at item #{args.end}")
                
                files = downloader.download_playlist(
                    args.url, 
                    audio_only=args.audio_only,
                    format_id=args.format,
                    start_index=args.start,
                    end_index=args.end,
                    skip_existing=args.skip_existing
                )
            
            print(f"\nSuccessfully downloaded {len(files)} files from the playlist")
            for file in files[:5]:
                print(f"- {os.path.basename(file)}")
            if len(files) > 5:
                print(f"... and {len(files) - 5} more files")
        else:
            print(f"Downloading: {args.url}")
            print(f"{'Audio only mode' if args.audio_only else 'Video mode'}")
            
            if args.format:
                print(f"Using format: {args.format}")
                
            file_path = downloader.download_video(
                args.url,
                format_id=args.format,
                audio_only=args.audio_only
            )
            print(f"\nDownload complete: {os.path.basename(file_path)}")
            print(f"Saved to: {file_path}")
    
    except KeyboardInterrupt:
        print("\nDownload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()