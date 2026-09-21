import os
import pytest
import subprocess
import numpy as np
from scipy.io import wavfile
from backend.media.ffmpeg import MediaEngine, FFmpegError

@pytest.fixture
def temp_media_dir(tmp_path):
    d = tmp_path / "media_test"
    d.mkdir()
    return d

@pytest.fixture
def synthetic_video(temp_media_dir):
    engine = MediaEngine()
    video_path = str(temp_media_dir / "input.mp4")
    # Create 3-second synthetic video with silent audio track using FFmpeg lavfi
    cmd = [
        engine.ffmpeg_path,
        "-y",
        "-f", "lavfi", "-i", "color=c=blue:s=320x240:r=25:d=3",
        "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono:d=3",
        "-c:v", "libx264", "-c:a", "aac",
        video_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return video_path

def test_media_engine_probe(synthetic_video):
    engine = MediaEngine()
    info = engine.probe(synthetic_video)
    assert info["has_video"] is True
    assert info["has_audio"] is True
    assert info["duration"] > 2.5

def test_extract_audio(synthetic_video, temp_media_dir):
    engine = MediaEngine()
    out_wav = str(temp_media_dir / "extracted.wav")
    engine.extract_audio(synthetic_video, out_wav)
    assert os.path.exists(out_wav)
    assert os.path.getsize(out_wav) > 0

def test_mix_audio_replace(synthetic_video, temp_media_dir):
    engine = MediaEngine()

    # Generate 3 seconds synthetic audio
    dubbed_wav = str(temp_media_dir / "dubbed.wav")
    sr = 16000
    t = np.linspace(0, 3, 3 * sr, endpoint=False)
    sig = (0.5 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    wavfile.write(dubbed_wav, sr, sig)

    mixed_wav = str(temp_media_dir / "mixed.wav")
    engine.mix_audio(synthetic_video, dubbed_wav, mixed_wav, mode="replace")
    assert os.path.exists(mixed_wav)

def test_render_final_video(synthetic_video, temp_media_dir):
    engine = MediaEngine()
    dubbed_wav = str(temp_media_dir / "dubbed.wav")
    sr = 16000
    t = np.linspace(0, 3, 3 * sr, endpoint=False)
    sig = (0.5 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    wavfile.write(dubbed_wav, sr, sig)

    out_mp4 = str(temp_media_dir / "final.mp4")
    engine.render_final_video(synthetic_video, dubbed_wav, out_mp4)
    assert os.path.exists(out_mp4)
