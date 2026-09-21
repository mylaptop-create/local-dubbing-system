#!/usr/bin/env bash
source venv/bin/activate 2>/dev/null || true
python3 -m backend.cli start
