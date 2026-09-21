import os
from typing import List
from backend.providers.base import Segment

def format_timestamp_srt(seconds: float) -> str:
    millis = int(round((seconds - int(seconds)) * 1000))
    seconds = int(seconds)
    minutes = seconds // 60
    hours = minutes // 60
    minutes = minutes % 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

def format_timestamp_vtt(seconds: float) -> str:
    millis = int(round((seconds - int(seconds)) * 1000))
    seconds = int(seconds)
    minutes = seconds // 60
    hours = minutes // 60
    minutes = minutes % 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"

class SubtitleGenerator:
    @staticmethod
    def generate_srt(segments: List[Segment], output_path: str, use_translation: bool = True) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        lines = []
        for idx, seg in enumerate(segments, 1):
            text = seg.translated_text if (use_translation and seg.translated_text) else seg.text
            start_str = format_timestamp_srt(seg.start)
            end_str = format_timestamp_srt(seg.end)
            lines.append(f"{idx}\n{start_str} --> {end_str}\n{text}\n")

        content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    @staticmethod
    def generate_vtt(segments: List[Segment], output_path: str, use_translation: bool = True) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        lines = ["WEBVTT\n"]
        for idx, seg in enumerate(segments, 1):
            text = seg.translated_text if (use_translation and seg.translated_text) else seg.text
            start_str = format_timestamp_vtt(seg.start)
            end_str = format_timestamp_vtt(seg.end)
            lines.append(f"{idx}\n{start_str} --> {end_str}\n{text}\n")

        content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path
