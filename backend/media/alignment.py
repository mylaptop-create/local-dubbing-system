import os
import math
import logging
from typing import List, Dict, Any, Optional
from backend.providers.base import Segment
from backend.media.ffmpeg import MediaEngine

logger = logging.getLogger(__name__)

class AudioAligner:
    def __init__(self, media_engine: Optional[MediaEngine] = None):
        self.media_engine = media_engine or MediaEngine()

    def _get_duration(self, audio_path: str) -> float:
        if not os.path.exists(audio_path):
            return 0.0
        try:
            info = self.media_engine.probe(audio_path)
            return info.get("duration", 0.0)
        except Exception:
            return 0.0

    def align_segment_audio(
        self,
        segment: Segment,
        tts_audio_path: str,
        output_path: str,
        max_speed_ratio: float = 1.35,
        min_speed_ratio: float = 0.8
    ) -> Dict[str, Any]:
        """
        Aligns a single TTS audio clip to the segment timeline window [start, end].
        Adjusts tempo (using FFmpeg atempo) if TTS is slightly longer/shorter than segment target.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        target_duration = max(0.5, segment.end - segment.start)
        actual_duration = self._get_duration(tts_audio_path)

        if actual_duration <= 0:
            raise ValueError(f"Invalid TTS audio generated at {tts_audio_path}")

        speed_factor = actual_duration / target_duration

        # Clamp speed factor to keep speech natural
        clamped_speed = max(min_speed_ratio, min(max_speed_ratio, speed_factor))

        filter_chain = []
        if abs(clamped_speed - 1.0) > 0.05:
            # atempo filter accepts values between 0.5 and 2.0
            filter_chain.append(f"atempo={clamped_speed:.3f}")

        # Construct FFmpeg command
        cmd = [self.media_engine.ffmpeg_path, "-y", "-i", tts_audio_path]
        if filter_chain:
            cmd.extend(["-filter:a", ",".join(filter_chain)])

        cmd.extend([
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            output_path
        ])

        self.media_engine._run_cmd(cmd)
        final_duration = self._get_duration(output_path)

        return {
            "segment_id": segment.id,
            "target_duration": target_duration,
            "original_tts_duration": actual_duration,
            "adjusted_speed_ratio": clamped_speed,
            "final_duration": final_duration,
            "output_path": output_path
        }

    def assemble_full_audio(
        self,
        segments: List[Segment],
        total_media_duration: float,
        output_audio_path: str
    ) -> str:
        """
        Assembles individual segment audio clips into a single seamlessly timeline-aligned wav file.
        Inserts silence padding for gaps between segments to prevent overlap.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_audio_path)), exist_ok=True)

        filter_inputs = []
        filter_complex_parts = []

        current_time = 0.0

        # Prepare silent audio generator if needed
        # We construct an FFmpeg command with delay/apad or concat
        inputs_cmd = [self.media_engine.ffmpeg_path, "-y"]

        concat_labels = []

        for idx, seg in enumerate(segments):
            if not seg.audio_path or not os.path.exists(seg.audio_path):
                continue

            # Gap silence before this segment
            gap = seg.start - current_time
            if gap > 0.05:
                filter_inputs.append(f"-f lavfi -i anullsrc=r=16000:cl=mono:d={gap:.3f}")
                filter_complex_parts.append(f"[{len(filter_inputs)-1}:a]")
                concat_labels.append(f"[{len(filter_inputs)-1}:a]")

            inputs_cmd.extend(["-i", seg.audio_path])
            input_idx = len(filter_inputs)
            filter_inputs.append(f"-i {seg.audio_path}")
            concat_labels.append(f"[{input_idx}:a]")

            seg_dur = self._get_duration(seg.audio_path)
            current_time = seg.start + seg_dur

        # Remaining tail silence to match full media length
        tail_gap = total_media_duration - current_time
        if tail_gap > 0.05:
            filter_inputs.append(f"-f lavfi -i anullsrc=r=16000:cl=mono:d={tail_gap:.3f}")
            concat_labels.append(f"[{len(filter_inputs)-1}:a]")

        if not concat_labels:
            # If no audio segments, generate pure silence of total duration
            cmd = [
                self.media_engine.ffmpeg_path,
                "-y",
                "-f", "lavfi",
                "-i", f"anullsrc=r=16000:cl=mono:d={max(1.0, total_media_duration):.3f}",
                "-acodec", "pcm_s16le",
                output_audio_path
            ]
            self.media_engine._run_cmd(cmd)
            return output_audio_path

        # Build full concat command
        concat_str = "".join(concat_labels) + f"concat=n={len(concat_labels)}:v=0:a=1[outa]"

        full_cmd = [self.media_engine.ffmpeg_path, "-y"]

        # Parse filter_inputs into command args
        for fi in filter_inputs:
            parts = fi.split()
            if parts[0] == "-f":
                full_cmd.extend(["-f", parts[1], "-i", parts[3]])
            elif parts[0] == "-i":
                full_cmd.extend(["-i", parts[1]])

        full_cmd.extend([
            "-filter_complex", concat_str,
            "-map", "[outa]",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            output_audio_path
        ])

        self.media_engine._run_cmd(full_cmd)
        return output_audio_path
