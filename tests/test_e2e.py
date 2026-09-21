import os
import pytest
import subprocess
from backend.database.manager import DatabaseManager
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.media.ffmpeg import MediaEngine

def test_full_e2e_pipeline(tmp_path):
    db_file = tmp_path / "e2e.db"
    db = DatabaseManager(db_path=db_file)
    engine = MediaEngine()

    # Synthetic Chinese course sample video
    video_path = str(tmp_path / "chinese_course_sample.mp4")
    cmd = [
        engine.ffmpeg_path,
        "-y",
        "-f", "lavfi", "-i", "color=c=blue:s=320x240:r=25:d=5",
        "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono:d=5",
        "-c:v", "libx264", "-c:a", "aac",
        video_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    proj = db.create_project(
        project_id="proj_e2e_001",
        name="Chinese Course Demo",
        source_video_path=video_path,
        config={"audio_mode": "replace", "tts_voice": "en-US-JennyNeural", "burn_subtitles": False}
    )

    orchestrator = PipelineOrchestrator(db_manager=db)
    result = orchestrator.run_pipeline("proj_e2e_001")

    assert result["status"] == "COMPLETED"
    assert result["progress_pct"] == 100.0

    proj_dir = tmp_path / "projects" / "proj_e2e_001" # Or wherever settings saved it
    # Check outputs generated
    checkpoints = db.get_checkpoints("proj_e2e_001")
    stages = [c["stage"] for c in checkpoints if c["status"] == "COMPLETED"]
    assert "MEDIA_ANALYSIS" in stages
    assert "TRANSCRIPTION" in stages
    assert "TRANSLATION" in stages
    assert "SUBTITLE_GENERATION" in stages
    assert "TTS" in stages
    assert "AUDIO_ASSEMBLY" in stages
    assert "VIDEO_RENDERING" in stages
