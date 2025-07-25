# 🎬 YouTube Downloader

![YouTube Downloader - by bunny](https://i.ibb.co/xt90R8zC/image.png)

A powerful and versatile YouTube downloader tool with both command-line and interactive interfaces. Download videos and playlists with ease!

[![GitHub](https://img.shields.io/badge/GitHub-Debojit--mitra-blue?style=flat&logo=github)](https://github.com/Debojit-mitra)

### ⭐ Star this repository if you find it useful! ⭐

## ✨ Features

- 📹 Download single videos in various formats and quality
- 🎵 Extract audio from videos (MP3)
- 📋 Download entire playlists (video/audio/mixed) or specific items
- 📊 List available video formats with detailed information
- 🔍 Get information about videos or playlists before downloading
- 💻 Command-line interface for scripting and automation
- 🖱️ Interactive CLI with user-friendly menus and progress tracking
- 🔄 Fallback mechanism for unavailable videos in playlists

## 🛠️ Installation

### Prerequisites

- Python
- pip

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Debojit-mitra/youtube-downloader.git
   cd youtube-downloader
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Usage
> [!NOTE]  
> Make sure FFMPEG is installed in your machine.
### Command-Line Interface

The basic command-line interface provides straightforward options:

```bash
python yt_downloader_cli.py -u "https://www.youtube.com/watch?v=VIDEO_ID" [options]
```

#### Examples:

1. Download a video in best quality:
   ```bash
   python yt_downloader_cli.py -u "https://www.youtube.com/watch?v=VIDEO_ID"
   ```

2. Download audio only (MP3):
   ```bash
   python yt_downloader_cli.py -u "https://www.youtube.com/watch?v=VIDEO_ID" --audio-only
   ```

3. List available formats:
   ```bash
   python yt_downloader_cli.py -u "https://www.youtube.com/watch?v=VIDEO_ID" --list-formats
   ```

4. Download with specific format:
   ```bash
   python yt_downloader_cli.py -u "https://www.youtube.com/watch?v=VIDEO_ID" -f 22
   ```

5. Download a playlist:
   ```bash
   python yt_downloader_cli.py -u "https://www.youtube.com/playlist?list=PLAYLIST_ID" --playlist
   ```

6. Download a specific item from a playlist:
   ```bash
   python yt_downloader_cli.py -u "https://www.youtube.com/playlist?list=PLAYLIST_ID" --playlist --item 5
   ```

### Interactive CLI

For a more user-friendly experience, use the interactive CLI:

```bash
python yt_downloader_cli_interactive.py
```

The interactive mode provides:
- 🖱️ Easy-to-navigate menus
- 📊 Detailed video information
- 📋 Format selection options
- 📂 Custom download directory selection
- 📊 Progress bars and status updates

You can also start with a URL:

```bash
python yt_downloader_cli_interactive.py -u "https://www.youtube.com/watch?v=VIDEO_ID"
```

## 📋 Command Options

### Basic CLI Options

```
-u, --url          URL of the YouTube video or playlist
-o, --output-dir   Directory to save downloaded files (default: ./downloads)
-f, --format       Format code to download
--audio-only       Download audio only
--list-formats     List available formats for the video
--info             Get information about the video or playlist
--playlist         Download as playlist
--item NUMBER      Download specific item from playlist
--start NUMBER     Start downloading from this item number
--end NUMBER       Download until this item number
--skip-existing    Skip files that already exist (default: True)
--no-skip-existing Do not skip files that already exist
-v, --verbose      Increase output verbosity
```

### Interactive CLI Options

```
-u, --url          YouTube URL to download (skips URL prompt)
-o, --output-dir   Output directory for downloads
-a, --audio-only   Download as audio only (MP3)
```

## 🔧 Core Functionality

The project is organized into three main files:

1. `core.py` - Core functionality and YouTube downloader class
2. `yt_downloader_cli.py` - Command-line interface
3. `yt_downloader_cli_interactive.py` - Interactive interface with rich UI

## 📝 Notes

- Downloaded files are saved in the `./downloads` directory by default
- Playlist downloads create a subdirectory with the playlist name
- The program maintains an archive file to track downloaded videos and avoid duplicates

## 🐛 Troubleshooting

- If you encounter "Video unavailable" errors for playlist items, the tool will attempt to find alternative sources
- Make sure you have the latest version of yt-dlp installed (`pip install -U yt-dlp`)
- Check your internet connection if downloads are failing
- For region-restricted videos, you may need to use a VPN

## 🙏 Acknowledgments

This project would not be possible without these amazing open-source libraries:

- [**yt-dlp**](https://github.com/yt-dlp/yt-dlp) - The core downloader that powers this application
- [tqdm](https://github.com/tqdm/tqdm) - For the progress bar functionality
- [rich](https://github.com/Textualize/rich) - For beautiful terminal formatting in the interactive CLI
- [questionary](https://github.com/tmbo/questionary) - For interactive command-line prompts

Special thanks to the yt-dlp maintainers and contributors for creating such a robust and powerful tool!

## ⚠️ Disclaimer  

This project is for **educational and personal use only**. The developer, is **not responsible** for any misuse of this tool.  

### ❗ Important Notes  
- This software **does not bypass DRM (Digital Rights Management)**.  
- **You are responsible** for ensuring compliance with **YouTube's Terms of Service** and **local laws** before using this tool.  
- **Downloading copyrighted content without permission** may be illegal in your country.  
- The author **assumes no liability** for any legal consequences arising from the use of this software.  

By using this tool, you agree that:  
✅ You will only use it for **personal and educational** purposes.  
✅ You **will not distribute** or sell downloaded content without proper authorization.  
✅ You **take full responsibility** for any actions taken using this software.  

If you do not agree to these terms, **do not use this software**. 🚫  


## 🤝 Contributing

Contributions are welcome! If you find any bugs or have feature requests, please open an issue on GitHub.

## 📜 License

This project is open source and available under the [MIT License](LICENSE).
