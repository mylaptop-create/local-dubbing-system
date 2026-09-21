import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

def download_video_from_url(url: str, output_dir: Path) -> Dict[str, Any]:
    """Downloads video from YouTube, Bilibili, or other yt-dlp supported platforms."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "downloaded_video.%(ext)s")

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o", output_template,
        url
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        # Find downloaded file in output_dir
        for f in output_dir.glob("downloaded_video.*"):
            return {
                "success": True,
                "file_path": str(f.resolve()),
                "filename": f.name
            }
        raise FileNotFoundError("Downloaded video file was not found in target directory.")
    except Exception as e:
        logger.error(f"yt-dlp video download failed for URL {url}: {e}")
        raise RuntimeError(f"Failed to download video from URL: {e}")
