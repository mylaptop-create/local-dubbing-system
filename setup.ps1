echo "=========================================="
echo " Setting up Local Video Dubbing System "
echo "=========================================="

if (-Not (Test-Path -Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

& .\venv\Scripts\Activate.ps1

Write-Host "Installing/updating Python dependencies..."
python -m pip install --upgrade pip
python -m pip install -e .

Write-Host "Checking system dependencies..."
python -c "from backend.core.diagnostics import get_system_diagnostics; diag = get_system_diagnostics(); print('FFmpeg status:', diag['ffmpeg']); print('GPU status:', diag['gpu'])"

Write-Host "Setup completed successfully!"
