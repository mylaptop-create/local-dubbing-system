import pytest
import os
from backend.providers.base import Segment
from backend.providers.transcription import SmartTranscriptionProvider, FallbackTranscriptionProvider
from backend.providers.translation import SmartTranslationProvider, OfflineDictTranslationProvider

def test_fallback_transcription(tmp_path):
    # Create empty audio file
    dummy_audio = tmp_path / "dummy.wav"
    dummy_audio.write_bytes(b"RIFF....WAVEfmt ....data....")

    provider = FallbackTranscriptionProvider()
    res = provider.transcribe(str(dummy_audio), language="zh")
    assert res.language == "zh"
    assert len(res.segments) > 0
    assert res.segments[0].text is not None

def test_smart_transcription_fallback(tmp_path):
    dummy_audio = tmp_path / "dummy.wav"
    dummy_audio.write_bytes(b"RIFF....WAVEfmt ....data....")

    provider = SmartTranscriptionProvider(model_size="tiny")
    res = provider.transcribe(str(dummy_audio), language="zh")
    assert len(res.segments) > 0

def test_offline_translation():
    provider = OfflineDictTranslationProvider()
    text = "大家好，欢迎来到这个课程。"
    translated = provider.translate_text(text)
    assert "Hello everyone" in translated

def test_translation_segments():
    provider = SmartTranslationProvider()
    segments = [
        Segment(id=0, start=0.0, end=3.0, text="大家好"),
        Segment(id=1, start=3.0, end=6.0, text="谢谢")
    ]
    res_segments = provider.translate_segments(segments)
    assert res_segments[0].translated_text is not None
    assert "Hello" in res_segments[0].translated_text
    assert "Thank" in res_segments[1].translated_text
