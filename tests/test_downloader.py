import os
import pytest
from fastapi.testclient import TestClient
from backend.api.app import app

client = TestClient(app)

def test_create_project_from_url(monkeypatch, tmp_path):
    # Mock download_video_from_url to avoid external network calls during unit test
    def mock_download(url, output_dir):
        dummy_file = output_dir / "downloaded_video.mp4"
        dummy_file.write_bytes(b"dummy mp4 content")
        return {"success": True, "file_path": str(dummy_file), "filename": "downloaded_video.mp4"}

    monkeypatch.setattr("backend.api.app.download_video_from_url", mock_download)

    payload = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "name": "YouTube Test Project",
        "source_lang": "zh",
        "target_lang": "en",
        "tts_voice": "en-US-JennyNeural",
        "audio_mode": "replace",
        "burn_subtitles": False
    }

    res = client.post("/api/projects/from-url", json=payload)
    assert res.status_code == 200
    p = res.json()
    assert p["name"] == "YouTube Test Project"
    assert p["config"]["source_url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
