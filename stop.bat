@echo off
taskkill /F /FI "WINDOWTITLE eq backend.cli*" 2>nul
echo Application stopped.
