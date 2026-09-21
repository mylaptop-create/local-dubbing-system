@echo off
echo ==========================================
echo  Setting up Local Video Dubbing System
echo ==========================================

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing/updating Python dependencies...
python -m pip install --upgrade pip
python -m pip install -e .

echo Checking system dependencies...
python -c "from backend.core.diagnostics import get_system_diagnostics; diag = get_system_diagnostics(); print('FFmpeg status:', diag['ffmpeg']); print('GPU status:', diag['gpu'])"

echo Setup completed successfully!
