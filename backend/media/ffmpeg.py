import os
import json
import subprocess
import shutil
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from backend.core.diagnostics import detect_ffmpeg

class FFmpegError(Exception):
    pass

class MediaEngine:
    def __init__(self):
        ffmpeg_info = detect_ffmpeg()
        if not ffmpeg_info["available"]:
            raise RuntimeError("FFmpeg executable not found. Please install FFmpeg or imageio-ffmpeg.")

        self.ffmpeg_path = ffmpeg_info["path"]
        # Find ffprobe alongside ffmpeg if possible
        ffmpeg_dir = Path(self.ffmpeg_path).parent
        ffprobe_path = shutil.which("ffprobe") or shutil.which("ffprobe.exe", path=str(ffmpeg_dir))
        if not ffprobe_path:
            # Check same dir as ffmpeg_path
            possible = ffmpeg_dir / ("ffprobe.exe" if os.name == "nt" else "ffprobe")
            if possible.exists():
                ffprobe_path = str(possible)

        self.ffprobe_path = ffprobe_path

    def _run_cmd(self, cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=check)
            return res
        except subprocess.CalledProcessError as e:
            raise FFmpegError(f"FFmpeg command failed with return code {e.returncode}.\nStderr: {e.stderr}") from e

    def probe(self, input_file: str) -> Dict[str, Any]:
        """Inspects media file and returns metadata."""
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Media file not found: {input_file}")

        if self.ffprobe_path and os.path.exists(self.ffprobe_path):
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                input_file
            ]
            try:
                res = self._run_cmd(cmd)
                data = json.loads(res.stdout)

                format_info = data.get("format", {})
                duration = float(format_info.get("duration", 0.0))
                size_bytes = int(format_info.get("size", 0))

                has_video = False
                has_audio = False
                video_info = {}
                audio_info = {}

                for stream in data.get("streams", []):
                    codec_type = stream.get("codec_type")
                    if codec_type == "video" and not has_video:
                        has_video = True
                        video_info = {
                            "codec": stream.get("codec_name"),
                            "width": stream.get("width"),
                            "height": stream.get("height"),
                            "fps": eval(stream.get("r_frame_rate", "0/1")) if "/" in stream.get("r_frame_rate", "") else 0.0
                        }
                    elif codec_type == "audio" and not has_audio:
                        has_audio = True
                        audio_info = {
                            "codec": stream.get("codec_name"),
                            "sample_rate": stream.get("sample_rate"),
                            "channels": stream.get("channels")
                        }

                return {
                    "path": str(Path(input_file).resolve()),
                    "duration": duration,
                    "size_bytes": size_bytes,
                    "has_video": has_video,
                    "has_audio": has_audio,
                    "video": video_info,
                    "audio": audio_info
                }
            except Exception:
                pass

        # Fallback probe using ffmpeg stderr output if ffprobe is unavailable
        cmd = [self.ffmpeg_path, "-i", input_file]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stderr = res.stderr

        duration = 0.0
        for line in stderr.splitlines():
            if "Duration:" in line:
                try:
                    parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
                    duration = float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
                except Exception:
                    pass

        has_video = "Video:" in stderr
        has_audio = "Audio:" in stderr

        return {
            "path": str(Path(input_file).resolve()),
            "duration": duration,
            "size_bytes": os.path.getsize(input_file),
            "has_video": has_video,
            "has_audio": has_audio,
            "video": {},
            "audio": {}
        }

    def extract_audio(self, video_path: str, output_audio_path: str, sample_rate: int = 16000) -> str:
        """Extracts mono PCM WAV audio for transcription/processing."""
        os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", "1",
            output_audio_path
        ]
        self._run_cmd(cmd)
        return output_audio_path

    def mix_audio(
        self,
        original_video_path: str,
        dubbed_audio_path: str,
        output_audio_path: str,
        mode: str = "replace",  # "replace" or "duck" / "keep_bg"
        bg_volume: float = 0.15,
        speech_volume: float = 1.0
    ) -> str:
        """Mixes original background audio with generated English speech audio."""
        os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)

        if mode == "replace":
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", dubbed_audio_path,
                "-acodec", "pcm_s16le",
                output_audio_path
            ]
            self._run_cmd(cmd)
            return output_audio_path

        # Ducking mode / Keep background mode
        filter_complex = f"[0:a]volume={bg_volume}[bg];[1:a]volume={speech_volume}[speech];[bg][speech]amix=inputs=2:duration=first:dropout_transition=2[out]"
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", original_video_path,
            "-i", dubbed_audio_path,
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-acodec", "pcm_s16le",
            output_audio_path
        ]
        self._run_cmd(cmd)
        return output_audio_path

    def render_final_video(
        self,
        video_path: str,
        audio_path: str,
        output_video_path: str,
        subtitle_path: Optional[str] = None,
        burn_subtitles: bool = False
    ) -> str:
        """Renders final video with new audio stream and optional soft/burnt subtitles."""
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)

        if burn_subtitles and subtitle_path and os.path.exists(subtitle_path):
            # Escape path for ffmpeg filter syntax
            escaped_sub_path = str(Path(subtitle_path).resolve()).replace("\\", "/").replace(":", "\\:")
            vf_arg = f"subtitles='{escaped_sub_path}'"
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", video_path,
                "-i", audio_path,
                "-vf", vf_arg,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "22",
                "-c:a", "aac",
                "-b:a", "192k",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                output_video_path
            ]
        else:
            # Stream copy video if possible or fast re-mux
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                output_video_path
            ]

            if subtitle_path and os.path.exists(subtitle_path):
                # Embed soft subtitles into container if srt
                cmd = [
                    self.ffmpeg_path,
                    "-y",
                    "-i", video_path,
                    "-i", audio_path,
                    "-i", subtitle_path,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-c:s", "mov_text" if output_video_path.endswith(".mp4") else "srt",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-map", "2:0",
                    "-shortest",
                    output_video_path
                ]

        self._run_cmd(cmd)
        return output_video_path
