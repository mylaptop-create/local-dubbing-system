# Local Chinese Video to English Translation & Dubbing System

A lightweight, local-first application that automatically processes Chinese-speaking videos and produces English translations, English subtitles, English speech/dubbing, and final dubbed videos with timeline synchronization.

## Features

- **Local & Privacy-First**: All core media processing, transcription, translation, and rendering execute locally on your machine.
- **Modular Pipeline**: Clean abstraction layers for Speech-to-Text (`TranscriptionProvider`), Neural Translation (`TranslationProvider`), and Text-to-Speech (`TTSProvider`).
- **Checkpoint Persistence**: Built-in SQLite database tracks stage checkpoints (`MEDIA_ANALYSIS`, `AUDIO_EXTRACTION`, `TRANSCRIPTION`, `TRANSLATION`, `SUBTITLE_GENERATION`, `TTS`, `AUDIO_ASSEMBLY`, `VIDEO_RENDERING`, `COMPLETE`). Projects can be paused or resumed anytime without re-processing completed stages.
- **Audio Synchronization & Ducking**: Automatically aligns generated English speech clips to original segment timestamps with natural tempo adjustments (`atempo`), gap preservation, and dual audio mode support (replace or ducking background audio).
- **Modern Desktop Web UI**: Responsive React + TypeScript + Tailwind CSS interface featuring drag-and-drop uploads, real-time WebSocket progress updates, project manager, system diagnostics, storage cleanup, and artifact downloads.
- **Cross-Platform**: Supports Windows, Linux, and macOS with automated single-command setup and start scripts.

## System Requirements

- **GPU**: Recommended NVIDIA RTX 4070 (8GB VRAM) or any CUDA GPU. Automatic fallback to CPU / Apple Silicon (MPS) if GPU is unavailable.
- **RAM**: 8GB+ (16GB - 32GB recommended)
- **Python**: Python 3.9+
- **FFmpeg**: Automatically detected from system `PATH` or bundled binaries via `imageio-ffmpeg`.

## Quick Start

### Step 1: Setup

On Linux / macOS:
```bash
./setup.sh
```

On Windows (Command Prompt):
```cmd
setup.bat
```

On Windows (PowerShell):
```powershell
.\setup.ps1
```

### Step 2: Launch Web UI

On Linux / macOS:
```bash
./start.sh
```

On Windows:
```cmd
start.bat
```

Then open your browser at **http://127.0.0.1:7860**.

---

## CLI Commands

You can also operate the system from the command line:

```bash
# Check system diagnostics (GPU, RAM, FFmpeg, Python)
python3 -m backend.cli doctor

# View application status and project counts
python3 -m backend.cli status

# List all local projects
python3 -m backend.cli project list

# Resume a paused or failed project
python3 -m backend.cli project resume <project_id>

# Run pipeline benchmark
python3 -m backend.cli benchmark
```

---

## Architecture

```
local-dubbing-system/
├── backend/
│   ├── api/            # FastAPI REST & WebSocket endpoints
│   ├── core/           # Configuration and system diagnostics
│   ├── database/       # SQLite manager & checkpoint persistence
│   ├── media/          # FFmpeg engine, alignment, and subtitles
│   ├── pipeline/       # Pipeline Orchestrator
│   └── providers/      # Speech, translation, and TTS provider abstractions
├── frontend/           # React + TypeScript + Tailwind CSS UI
├── data/               # Persistent SQLite database & project output storage
├── tests/              # Comprehensive pytest test suite
├── setup.sh / start.sh # Cross-platform launcher scripts
└── pyproject.toml
```

---

## License

MIT License.
