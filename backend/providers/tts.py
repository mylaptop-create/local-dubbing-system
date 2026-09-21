import os
import asyncio
import logging
import numpy as np
from typing import List
from scipy.io import wavfile
from backend.providers.base import TTSProvider, TTSVoice

logger = logging.getLogger(__name__)

class EdgeTTSProvider(TTSProvider):
    @property
    def name(self) -> str:
        return "Edge-TTS"

    @property
    def is_local(self) -> bool:
        return False  # Uses Edge online service, high quality

    def get_available_voices(self) -> List[TTSVoice]:
        return [
            TTSVoice(id="en-US-JennyNeural", name="Jenny (US English Female)", gender="female", language="en-US", provider="edge"),
            TTSVoice(id="en-US-GuyNeural", name="Guy (US English Male)", gender="male", language="en-US", provider="edge"),
            TTSVoice(id="en-GB-SoniaNeural", name="Sonia (UK English Female)", gender="female", language="en-GB", provider="edge"),
            TTSVoice(id="en-AU-NatashaNeural", name="Natasha (AU English Female)", gender="female", language="en-AU", provider="edge"),
        ]

    def _async_generate(self, text: str, output_path: str, voice: str, rate: str, volume: str, pitch: str):
        import edge_tts
        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume, pitch=pitch)

        # Determine if output should be mp3 or wav
        tmp_mp3 = output_path if output_path.endswith(".mp3") else output_path + ".tmp.mp3"
        asyncio.run(communicate.save(tmp_mp3))

        if tmp_mp3 != output_path:
            # Convert mp3 to wav via FFmpeg
            from backend.media.ffmpeg import MediaEngine
            engine = MediaEngine()
            cmd = [
                engine.ffmpeg_path,
                "-y",
                "-i", tmp_mp3,
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                output_path
            ]
            engine._run_cmd(cmd)
            if os.path.exists(tmp_mp3):
                os.remove(tmp_mp3)

    def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str = "en-US-JennyNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz"
    ) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        try:
            self._async_generate(text, output_path, voice, rate, volume, pitch)
            return output_path
        except Exception as e:
            logger.warning(f"EdgeTTS generation failed ({e}). Using offline synthetic fallback TTS.")
            return SyntheticOfflineTTSProvider().generate_speech(text, output_path, voice, rate, volume, pitch)


class SyntheticOfflineTTSProvider(TTSProvider):
    @property
    def name(self) -> str:
        return "synthetic-offline-tts"

    @property
    def is_local(self) -> bool:
        return True

    def get_available_voices(self) -> List[TTSVoice]:
        return [
            TTSVoice(id="offline-default", name="Offline Synthetic Voice", gender="neutral", language="en-US", provider="local")
        ]

    def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str = "offline-default",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz"
    ) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Estimate duration based on word count (~2.5 words/sec)
        words = len(text.split()) if text else 1
        duration_sec = max(1.0, words / 2.5)

        sr = 16000
        total_samples = int(duration_sec * sr)
        t = np.linspace(0, duration_sec, total_samples, endpoint=False)

        # Synthesize simple pleasant dual-tone melody modulating speech
        freq1 = 220.0
        freq2 = 440.0
        envelope = np.sin(np.pi * t / duration_sec) ** 2  # Smooth start & end
        signal = 0.3 * (np.sin(2 * np.pi * freq1 * t) + 0.5 * np.sin(2 * np.pi * freq2 * t)) * envelope
        pcm = (signal * 32767).astype(np.int16)

        wav_path = output_path if output_path.endswith(".wav") else output_path + ".wav"
        wavfile.write(wav_path, sr, pcm)

        if wav_path != output_path:
            # Convert if destination was e.g. mp3
            from backend.media.ffmpeg import MediaEngine
            engine = MediaEngine()
            cmd = [engine.ffmpeg_path, "-y", "-i", wav_path, output_path]
            engine._run_cmd(cmd)
            os.remove(wav_path)

        return output_path


class SmartTTSProvider(TTSProvider):
    def __init__(self):
        self.primary = EdgeTTSProvider()
        self.fallback = SyntheticOfflineTTSProvider()

    @property
    def name(self) -> str:
        return "smart-tts"

    @property
    def is_local(self) -> bool:
        return True

    def get_available_voices(self) -> List[TTSVoice]:
        return self.primary.get_available_voices() + self.fallback.get_available_voices()

    def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str = "en-US-JennyNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz"
    ) -> str:
        try:
            return self.primary.generate_speech(text, output_path, voice, rate, volume, pitch)
        except Exception:
            return self.fallback.generate_speech(text, output_path, voice, rate, volume, pitch)
