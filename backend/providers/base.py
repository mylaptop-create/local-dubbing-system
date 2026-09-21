from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Segment(BaseModel):
    id: int
    start: float  # seconds
    end: float    # seconds
    text: str
    translated_text: Optional[str] = None
    audio_path: Optional[str] = None
    speaker: Optional[str] = None

class TranscriptionResult(BaseModel):
    language: str
    duration: float
    segments: List[Segment]
    full_text: str

class TranscriptionProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_local(self) -> bool:
        pass

    @abstractmethod
    def transcribe(self, audio_path: str, language: str = "zh") -> TranscriptionResult:
        pass

class TranslationProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_local(self) -> bool:
        pass

    @abstractmethod
    def translate_segments(self, segments: List[Segment], source_lang: str = "zh", target_lang: str = "en") -> List[Segment]:
        pass

    @abstractmethod
    def translate_text(self, text: str, source_lang: str = "zh", target_lang: str = "en") -> str:
        pass

class TTSVoice(BaseModel):
    id: str
    name: str
    gender: str
    language: str
    provider: str

class TTSProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_local(self) -> bool:
        pass

    @abstractmethod
    def get_available_voices(self) -> List[TTSVoice]:
        pass

    @abstractmethod
    def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str,
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz"
    ) -> str:
        pass
