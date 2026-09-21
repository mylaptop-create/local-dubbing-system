import os
import pytest
from backend.providers.base import Segment
from backend.providers.tts import SyntheticOfflineTTSProvider, SmartTTSProvider
from backend.media.alignment import AudioAligner
from backend.media.subtitles import SubtitleGenerator, format_timestamp_srt, format_timestamp_vtt

def test_synthetic_tts(tmp_path):
    tts = SyntheticOfflineTTSProvider()
    voices = tts.get_available_voices()
    assert len(voices) > 0

    out_wav = str(tmp_path / "tts_out.wav")
    tts.generate_speech("Hello world, testing speech synthesis.", out_wav)
    assert os.path.exists(out_wav)
    assert os.path.getsize(out_wav) > 0

def test_audio_alignment(tmp_path):
    tts = SyntheticOfflineTTSProvider()
    seg = Segment(id=1, start=1.0, end=4.0, text="Test segment alignment")
    raw_tts = str(tmp_path / "raw_tts.wav")
    tts.generate_speech(seg.text, raw_tts)

    aligner = AudioAligner()
    aligned_wav = str(tmp_path / "aligned_seg1.wav")
    res = aligner.align_segment_audio(seg, raw_tts, aligned_wav)

    assert os.path.exists(aligned_wav)
    assert res["segment_id"] == 1
    assert res["adjusted_speed_ratio"] > 0

def test_full_audio_assembly(tmp_path):
    tts = SyntheticOfflineTTSProvider()
    aligner = AudioAligner()

    seg1 = Segment(id=0, start=1.0, end=3.0, text="First sentence")
    seg2 = Segment(id=1, start=4.0, end=6.0, text="Second sentence")

    audio1 = str(tmp_path / "seg1.wav")
    audio2 = str(tmp_path / "seg2.wav")
    tts.generate_speech(seg1.text, audio1)
    tts.generate_speech(seg2.text, audio2)

    seg1.audio_path = audio1
    seg2.audio_path = audio2

    full_audio = str(tmp_path / "full_assembled.wav")
    aligner.assemble_full_audio([seg1, seg2], total_media_duration=7.0, output_audio_path=full_audio)

    assert os.path.exists(full_audio)
    assert os.path.getsize(full_audio) > 0

def test_subtitles_generation(tmp_path):
    segments = [
        Segment(id=0, start=1.234, end=3.567, text="大家好", translated_text="Hello everyone"),
        Segment(id=1, start=4.0, end=6.5, text="谢谢", translated_text="Thank you")
    ]

    srt_path = str(tmp_path / "test.srt")
    vtt_path = str(tmp_path / "test.vtt")

    SubtitleGenerator.generate_srt(segments, srt_path, use_translation=True)
    SubtitleGenerator.generate_vtt(segments, vtt_path, use_translation=True)

    assert os.path.exists(srt_path)
    assert os.path.exists(vtt_path)

    srt_content = open(srt_path, "r", encoding="utf-8").read()
    assert "Hello everyone" in srt_content
    assert "00:00:01,234 --> 00:00:03,567" in srt_content
