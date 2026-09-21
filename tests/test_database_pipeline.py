import os
import pytest
import subprocess
from backend.database.manager import DatabaseManager
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.media.ffmpeg import MediaEngine

@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test.db"
    return DatabaseManager(db_path=db_file)

@pytest.fixture
def synthetic_video(tmp_path):
    engine = MediaEngine()
    video_path = str(tmp_path / "sample_zh.mp4")
    cmd = [
        engine.ffmpeg_path,
        "-y",
        "-f", "lavfi", "-i", "color=c=black:s=320x240:r=25:d=4",
        "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono:d=4",
        "-c:v", "libx264", "-c:a", "aac",
        video_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return video_path

def test_database_persistence(test_db):
    p = test_db.create_project(
        project_id="proj_001",
        name="Test Project",
        source_video_path="/path/to/video.mp4",
        config={"audio_mode": "replace"}
    )
    assert p["id"] == "proj_001"
    assert p["status"] == "CREATED"

    test_db.update_project_status("proj_001", "PROCESSING", "TRANSCRIPTION", 35.0)
    p_updated = test_db.get_project("proj_001")
    assert p_updated["status"] == "PROCESSING"
    assert p_updated["current_stage"] == "TRANSCRIPTION"

def test_pipeline_execution_and_checkpoint_resume(test_db, synthetic_video, tmp_path):
    # Setup test project directory
    p = test_db.create_project(
        project_id="proj_pipeline_test",
        name="Pipeline Resume Test",
        source_video_path=synthetic_video,
        config={"audio_mode": "replace", "tts_voice": "en-US-JennyNeural"}
    )

    orchestrator = PipelineOrchestrator(db_manager=test_db)
    res = orchestrator.run_pipeline("proj_pipeline_test")

    assert res["status"] == "COMPLETED"
    assert res["progress_pct"] == 100.0

    checkpoints = test_db.get_checkpoints("proj_pipeline_test")
    completed_stages = [c["stage"] for c in checkpoints if c["status"] == "COMPLETED"]
    assert "TRANSCRIPTION" in completed_stages
    assert "VIDEO_RENDERING" in completed_stages

    # Verify resume: rerunning pipeline uses existing checkpoints
    res_rerun = orchestrator.run_pipeline("proj_pipeline_test")
    assert res_rerun["status"] == "COMPLETED"
