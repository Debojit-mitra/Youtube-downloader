import os
import sys
import time
import questionary
from questionary import Style
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich import box
import textwrap
import argparse

# Import the core functionality
from core import YouTubeDownloader, logger

# Custom styles for questionary
custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'fg:yellow bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:cyan bold'),
    ('selected', 'fg:green'),
    ('separator', 'fg:yellow'),
    ('instruction', 'fg:magenta'),
    ('text', 'fg:white'),
    ('disabled', 'fg:grey'),
])

# Initialize rich console
console = Console()

class InteractiveYouTubeDownloader:
    """Interactive CLI for YouTube Downloader by Bunny."""
    
    def __init__(self):
        """Initialize the interactive CLI."""
        self.downloader = None
        self.output_dir = "./downloads"
    
    def _print_header(self):
        """Print the program header."""
        console.print(Panel.fit(
            "[bold cyan]YouTube Downloader by Bunny[/bold cyan] - [yellow]Interactive CLI[/yellow]",
            padding=(1, 10),
            border_style="bright_blue"
        ))
    
    def _setup_downloader(self):
        """Set up the downloader with user-specified output directory."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.downloader = YouTubeDownloader(output_dir=self.output_dir)
    
    def _get_url(self) -> str:
        """Get URL from user."""
        return questionary.text(
            "Enter YouTube URL:",
            validate=lambda text: len(text) > 0 and ("youtube.com" in text or "youtu.be" in text),
            style=custom_style
        ).ask()
    
    def _determine_content_type(self, url: str) -> str:
        """Determine if URL is a video or playlist."""
        with console.status("[cyan]Analyzing URL...[/cyan]"):
            info = self.downloader.get_info(url)
            return info["type"]

    def _format_seconds(self, seconds: Any) -> str:
        """Format seconds to HH:MM:SS."""
        if not isinstance(seconds, (int, float)):
            return "Unknown"
        
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def _display_video_info(self, url: str) -> Dict:
        """Display information about the video."""
        with console.status("[cyan]Fetching video information...[/cyan]"):
            info = self.downloader.get_info(url)
        
        if info['type'] == 'video':
            # Format duration
            duration = self._format_seconds(info['duration'])
            
            # Format upload date
            upload_date = info.get('upload_date', 'Unknown')
            if len(upload_date) == 8:  # Format YYYYMMDD to YYYY-MM-DD
                upload_date = f"{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
            
            console.print(Panel(
                f"[bold yellow]Title:[/bold yellow] {info['title']}\n"
                f"[bold yellow]Channel:[/bold yellow] {info['uploader']}\n"
                f"[bold yellow]Duration:[/bold yellow] {duration}\n"
                f"[bold yellow]Upload Date:[/bold yellow] {upload_date}\n"
                f"[bold yellow]Views:[/bold yellow] {info.get('view_count', 'Unknown')}",
                title="[bold cyan]Video Information[/bold cyan]",
                border_style="bright_blue",
                expand=False
            ))
            
            # Show truncated description if available
            if info.get('description'):
                desc = info['description']
                if len(desc) > 300:
                    desc = desc[:300] + "..."
                
                wrapped_desc = textwrap.fill(desc, width=80, 
                                            initial_indent="  ", 
                                            subsequent_indent="  ")
                console.print(Panel(
                    wrapped_desc,
                    title="[bold cyan]Description[/bold cyan]",
                    border_style="bright_blue",
                    expand=False
                ))
        
        return info
    
    def _display_playlist_info(self, url: str) -> Dict:
        """Display information about the playlist."""
        with console.status("[cyan]Fetching playlist information...[/cyan]"):
            info = self.downloader.get_info(url)
        
        if info['type'] == 'playlist':
            console.print(Panel(
                f"[bold yellow]Title:[/bold yellow] {info['title']}\n"
                f"[bold yellow]Channel:[/bold yellow] {info['uploader']}\n"
                f"[bold yellow]Video Count:[/bold yellow] {info['video_count']}",
                title="[bold cyan]Playlist Information[/bold cyan]",
                border_style="bright_blue",
                expand=False
            ))
            
            # Show list of videos (limited to 10)
            table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
            table.add_column("#", style="dim", width=4)
            table.add_column("Title", style="bright_white")
            
            video_count = min(10, len(info['videos']))
            for i, video in enumerate(info['videos'][:video_count], 1):
                table.add_row(str(i), video['title'])
            
            if len(info['videos']) > 10:
                table.add_row("...", f"...and {len(info['videos']) - 10} more videos")
            
            console.print(table)
        
        return info
    
    def _choose_format(self, url: str) -> Optional[str]:
        """Let user choose download format."""
        with console.status("[cyan]Fetching available formats...[/cyan]"):
            formats = self.downloader.list_formats(url)
        
        # Filter and group formats
        video_audio_formats = [f for f in formats if f['type'] == 'video+audio']
        video_only_formats = [f for f in formats if f['type'] == 'video only']
        audio_only_formats = [f for f in formats if f['type'] == 'audio only']
        
        # Prepare for display
        format_table = Table(title="Available Formats", show_header=True, header_style="bold cyan", box=box.ROUNDED)
        format_table.add_column("ID", style="cyan")
        format_table.add_column("Type", style="green")
        format_table.add_column("Resolution", style="yellow")
        format_table.add_column("Extension", style="magenta")
        format_table.add_column("FPS", style="blue")
        format_table.add_column("Size", style="red")
        
        # Add combined video+audio formats
        if video_audio_formats:
            format_table.add_row("", "[bold]Video + Audio[/bold]", "", "", "", "")
            for fmt in video_audio_formats:
                size = fmt.get('filesize', 'unknown')
                if isinstance(size, int):
                    size = f"{size / 1024 / 1024:.1f} MB"
                format_table.add_row(
                    fmt['format_id'],
                    "Video+Audio",
                    fmt['resolution'],
                    fmt['ext'],
                    str(fmt['fps']),
                    str(size)
                )
        
        # Add video-only formats
        if video_only_formats:
            format_table.add_row("", "[bold]Video Only[/bold]", "", "", "", "")
            for fmt in video_only_formats:  # add video_only_formats[:5]: to Limit display
                size = fmt.get('filesize', 'unknown')
                if isinstance(size, int):
                    size = f"{size / 1024 / 1024:.1f} MB"
                format_table.add_row(
                    fmt['format_id'],
                    "Video Only",
                    fmt['resolution'],
                    fmt['ext'],
                    str(fmt['fps']),
                    str(size)
                )
            # if len(video_only_formats) > 5:
            #     format_table.add_row("...", f"...and {len(video_only_formats) - 5} more formats", "", "", "", "")
        
        # Add audio-only formats
        if audio_only_formats:
            format_table.add_row("", "[bold]Audio Only[/bold]", "", "", "", "")
            for fmt in audio_only_formats:  # add audio_only_formats[:5]: to Limit display
                size = fmt.get('filesize', 'unknown')
                if isinstance(size, int):
                    size = f"{size / 1024 / 1024:.1f} MB"
                format_table.add_row(
                    fmt['format_id'],
                    "Audio Only",
                    "N/A",
                    fmt['ext'],
                    "N/A",
                    str(size)
                )
            # if len(audio_only_formats) > 5:
            #     format_table.add_row("...", f"...and {len(audio_only_formats) - 5} more formats", "", "", "", "")
        
        console.print(format_table)
        
        # Let user choose download option
        options = [
            {"name": "Best quality (video + audio)", "value": "best"},
            {"name": "Audio only (MP3)", "value": "audio"},
            {"name": "Choose specific format (by ID) (you can also combined video + audio like 247+140)", "value": "custom"}
        ]
        
        choice = questionary.select(
            "Select download format:",
            choices=options,
            style=custom_style
        ).ask()
        
        if choice == "custom":
            format_id = questionary.text(
                "Enter format ID:",
                validate=lambda text: len(text) > 0,
                style=custom_style
            ).ask()
            return format_id
        elif choice == "audio":
            return None  # Will use audio_only flag
        else:
            return None  # Will use default best quality
    
    def _configure_playlist_download(self) -> Dict:
        """Configure playlist download options."""
        # Ask for download range
        range_options = [
            {"name": "Download entire playlist", "value": "all"},
            {"name": "Download specific item", "value": "item"},
            {"name": "Download range of items", "value": "range"}
        ]
        
        range_choice = questionary.select(
            "What would you like to download?",
            choices=range_options,
            style=custom_style
        ).ask()
        
        options = {}
        
        if range_choice == "item":
            item = questionary.text(
                "Enter item number to download:",
                validate=lambda text: text.isdigit() and int(text) > 0,
                style=custom_style
            ).ask()
            options["specific_index"] = int(item)
        elif range_choice == "range":
            start = questionary.text(
                "Enter start item number:",
                validate=lambda text: text.isdigit() and int(text) > 0,
                style=custom_style
            ).ask()
            end = questionary.text(
                "Enter end item number:",
                validate=lambda text: text.isdigit() and int(text) > int(start),
                style=custom_style
            ).ask()
            options["start_index"] = int(start)
            options["end_index"] = int(end)
        
        # Ask for format type
        format_options = [
            {"name": "Best quality (video + audio)", "value": "best"},
            {"name": "Audio only (MP3)", "value": "audio"}
        ]
        
        format_choice = questionary.select(
            "Select download format:",
            choices=format_options,
            style=custom_style
        ).ask()
        
        options["audio_only"] = format_choice == "audio"
        
        # Ask about skipping existing files
        options["skip_existing"] = questionary.confirm(
            "Skip files that already exist?",
            default=True,
            style=custom_style
        ).ask()
        
        return options
    
    def _download_video(self, url: str, format_id: Optional[str], audio_only: bool):
        """Download a single video with progress tracking."""
        console.print(f"\n[bold cyan]Downloading video...[/bold cyan]")
        
        try:
            file_path = self.downloader.download_video(
                url,
                format_id=format_id,
                audio_only=audio_only
            )
            
            console.print(f"\n[bold green]Download complete![/bold green]")
            console.print(f"[yellow]Saved to:[/yellow] {file_path}")
            
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
    
    def _download_playlist(self, url: str, options: Dict):
        """Download a playlist with progress tracking."""
        console.print(f"\n[bold cyan]Downloading playlist...[/bold cyan]")
        console.print(f"This may take some time depending on the playlist size.")
        
        try:
            files = self.downloader.download_playlist(
                url,
                audio_only=options.get("audio_only", False),
                format_id=options.get("format_id"),
                start_index=options.get("start_index"),
                end_index=options.get("end_index"),
                specific_index=options.get("specific_index"),
                skip_existing=options.get("skip_existing", True)
            )
            
            console.print(f"\n[bold green]Download complete![/bold green]")
            console.print(f"[yellow]Successfully downloaded {len(files)} files[/yellow]")
            
            # Show sample of downloaded files
            if files:
                table = Table(title="Downloaded Files", show_header=True, header_style="bold cyan", box=box.ROUNDED)
                table.add_column("File", style="bright_white")
                
                for file in files[:5]:
                    table.add_row(os.path.basename(file))
                
                if len(files) > 5:
                    table.add_row(f"...and {len(files) - 5} more files")
                
                console.print(table)
            
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
    
    def _choose_output_directory(self):
        """Let user choose or create output directory."""
        default_dir = os.path.abspath("./downloads")
        
        dir_options = [
            {"name": f"Use default ({default_dir})", "value": default_dir},
            {"name": "Enter custom directory", "value": "custom"}
        ]
        
        dir_choice = questionary.select(
            "Where would you like to save downloads?",
            choices=dir_options,
            style=custom_style
        ).ask()
        
        if dir_choice == "custom":
            custom_dir = questionary.text(
                "Enter directory path:",
                default=default_dir,
                style=custom_style
            ).ask()
            
            # Create directory if it doesn't exist
            if not os.path.exists(custom_dir):
                try:
                    os.makedirs(custom_dir)
                    console.print(f"[green]Created directory:[/green] {custom_dir}")
                except Exception as e:
                    console.print(f"[red]Error creating directory:[/red] {str(e)}")
                    console.print(f"[yellow]Using default directory instead:[/yellow] {default_dir}")
                    return default_dir
            
            return custom_dir
        else:
            return default_dir
    
    def _show_main_menu(self):
        """Show the main menu."""
        options = [
            {"name": "Download video/playlist", "value": "download"},
            {"name": "Get video/playlist info", "value": "info"},
            {"name": "Change output directory", "value": "dir"},
            {"name": "Exit", "value": "exit"}
        ]
        
        choice = questionary.select(
            "What would you like to do?",
            choices=options,
            style=custom_style
        ).ask()
        
        return choice
    
    def _handle_download(self):
        """Handle the download option."""
        url = self._get_url()
        
        # Determine content type (video or playlist)
        content_type = self._determine_content_type(url)
        
        if content_type == "video":
            # Display video info
            self._display_video_info(url)
            
            # Let user choose format
            format_id = self._choose_format(url)
            audio_only = False
            
            if format_id == "audio":
                format_id = None
                audio_only = True
            
            # Download video
            self._download_video(url, format_id, audio_only)
        else:
            # Display playlist info
            self._display_playlist_info(url)
            
            # Configure playlist download
            options = self._configure_playlist_download()
            
            # Download playlist
            self._download_playlist(url, options)
    
    def _handle_info(self):
        """Handle the info option."""
        url = self._get_url()
        
        # Determine content type (video or playlist)
        content_type = self._determine_content_type(url)
        
        if content_type == "video":
            self._display_video_info(url)
        else:
            self._display_playlist_info(url)
        
        # Pause to let user read info
        questionary.press_any_key_to_continue(
            message="Press any key to continue...",
            style=custom_style
        ).ask()
    
    def _handle_change_dir(self):
        """Handle changing the output directory."""
        new_dir = self._choose_output_directory()
        self.output_dir = new_dir
        self._setup_downloader()
        console.print(f"[green]Output directory changed to:[/green] {new_dir}")
    
    def run(self):
        """Run the interactive CLI."""
        try:
            self._print_header()
            self.output_dir = self._choose_output_directory()
            self._setup_downloader()
            
            while True:
                console.rule("[bold cyan]YouTube Downloader by Bunny[/bold cyan]")
                choice = self._show_main_menu()
                
                if choice == "download":
                    self._handle_download()
                elif choice == "info":
                    self._handle_info()
                elif choice == "dir":
                    self._handle_change_dir()
                elif choice == "exit":
                    console.print("[bold yellow]Thank you for using YouTube Downloader by Bunny![/bold yellow]")
                    break
                
                # Add a small delay for better UX
                time.sleep(0.5)
        
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Program interrupted. Exiting...[/bold yellow]")
        except Exception as e:
            console.print(f"\n[bold red]An error occurred:[/bold red] {str(e)}")
            console.print_exception()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Interactive YouTube Downloader CLI"
    )
    parser.add_argument(
        "-u", "--url", 
        help="YouTube URL to download (skips URL prompt)"
    )
    parser.add_argument(
        "-o", "--output-dir", 
        help="Output directory for downloads"
    )
    parser.add_argument(
        "-a", "--audio-only", 
        action="store_true",
        help="Download as audio only (MP3)"
    )
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    
    # Check for required packages
    required_packages = ["questionary", "rich", "tqdm"]
    missing_packages = []
    
    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing_packages.append(pkg)
    
    if missing_packages:
        print("Missing required packages. Please install:")
        print(f"pip install {' '.join(missing_packages)}")
        return
    
    # Create and run the interactive CLI
    cli = InteractiveYouTubeDownloader()
    
    # Handle direct command line arguments if provided
    if args.url:
        cli.output_dir = args.output_dir if args.output_dir else "./downloads"
        cli._setup_downloader()
        
        try:
            content_type = cli._determine_content_type(args.url)
            
            if content_type == "video":
                cli._display_video_info(args.url)
                cli._download_video(args.url, None, args.audio_only)
            else:
                cli._display_playlist_info(args.url)
                options = {"audio_only": args.audio_only, "skip_existing": True}
                cli._download_playlist(args.url, options)
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
    else:
        # Run in interactive mode
        cli.run()

if __name__ == "__main__":
    main()