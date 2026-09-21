import os
import pytest
import subprocess
from fastapi.testclient import TestClient
from backend.api.app import app

client = TestClient(app)

@pytest.fixture
def dummy_video(tmp_path):
    v_path = tmp_path / "test_input.mp4"
    # Create simple 1s mp4 file using ffmpeg
    from backend.media.ffmpeg import MediaEngine
    engine = MediaEngine()
    cmd = [
        engine.ffmpeg_path, "-y",
        "-f", "lavfi", "-i", "color=c=red:s=160x120:d=1",
        "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono:d=1",
        str(v_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return str(v_path)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_diagnostics():
    response = client.get("/api/diagnostics")
    assert response.status_code == 200
    assert "os" in response.json()
    assert "ffmpeg" in response.json()

def test_storage_and_voices():
    r_voices = client.get("/api/voices")
    assert r_voices.status_code == 200
    assert isinstance(r_voices.json(), list)

    r_storage = client.get("/api/storage")
    assert r_storage.status_code == 200
    assert "models_size_mb" in r_storage.json()

def test_project_crud(dummy_video):
    with open(dummy_video, "rb") as f:
        response = client.post(
            "/api/projects",
            files={"video": ("test_input.mp4", f, "video/mp4")},
            data={
                "name": "API Test Project",
                "source_lang": "zh",
                "target_lang": "en",
                "tts_voice": "en-US-JennyNeural",
                "audio_mode": "replace"
            }
        )
    assert response.status_code == 200
    p = response.json()
    project_id = p["id"]
    assert p["name"] == "API Test Project"

    # Get project
    r_get = client.get(f"/api/projects/{project_id}")
    assert r_get.status_code == 200
    assert r_get.json()["id"] == project_id

    # List projects
    r_list = client.get("/api/projects")
    assert r_list.status_code == 200
    assert len(r_list.json()) >= 1

    # Delete project
    r_del = client.delete(f"/api/projects/{project_id}")
    assert r_del.status_code == 200
    assert r_del.json()["status"] == "deleted"
