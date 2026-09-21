import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
PROJECTS_DIR = DATA_DIR / "projects"
TEMP_DIR = DATA_DIR / "temp"

# Ensure core directories exist
for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR, PROJECTS_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class AppSettings(BaseModel):
    app_name: str = "Local Video Dubbing System"
    host: str = "127.0.0.1"
    port: int = 7860
    debug: bool = False

    # Storage
    data_dir: Path = DATA_DIR
    models_dir: Path = MODELS_DIR
    logs_dir: Path = LOGS_DIR
    projects_dir: Path = PROJECTS_DIR
    temp_dir: Path = TEMP_DIR

    # Default Provider Settings
    transcription_provider: str = "whisper"
    translation_provider: str = "opus_mt" # or "mock" / "local"
    tts_provider: str = "edge_tts"

    # Performance profile: "fast", "balanced", "quality"
    performance_profile: str = "balanced"
    device: str = "auto"  # "auto", "cuda", "cpu", "mps"

settings = AppSettings()
