#!/usr/bin/env bash
set -e

echo "=========================================="
echo " Setting up Local Video Dubbing System "
echo "=========================================="

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

echo "Installing/updating Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -e .

echo "Checking system dependencies..."
python3 -c "from backend.core.diagnostics import get_system_diagnostics; diag = get_system_diagnostics(); print('FFmpeg status:', diag['ffmpeg']); print('GPU status:', diag['gpu'])"

echo "Setup completed successfully!"
