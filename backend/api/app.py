import os
import uuid
import json
import asyncio
import shutil
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.core.config import settings
from backend.core.diagnostics import get_system_diagnostics
from backend.database.manager import DatabaseManager
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.providers.tts import SmartTTSProvider
from backend.media.downloader import download_video_from_url

logger = logging.getLogger("backend.api")

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DatabaseManager()
orchestrator = PipelineOrchestrator(db_manager=db)

# Active websocket connections per project
active_connections: Dict[str, List[WebSocket]] = {}

def broadcast_progress(project_id: str, stage: str, progress: float, message: str):
    data = {
        "project_id": project_id,
        "stage": stage,
        "progress": progress,
        "message": message
    }
    listeners = active_connections.get(project_id, [])
    for ws in list(listeners):
        try:
            asyncio.create_task(ws.send_json(data))
        except Exception:
            pass

orchestrator.progress_callback = broadcast_progress

class URLProjectRequest(BaseModel):
    url: str
    name: str
    source_lang: str = "zh"
    target_lang: str = "en"
    tts_voice: str = "en-US-JennyNeural"
    audio_mode: str = "replace"
    burn_subtitles: bool = False

@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}

@app.get("/api/diagnostics")
def diagnostics():
    return get_system_diagnostics()

@app.get("/api/voices")
def get_voices():
    tts = SmartTTSProvider()
    return tts.get_available_voices()

@app.get("/api/projects")
def list_projects():
    return db.list_projects()

@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    p = db.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    checkpoints = db.get_checkpoints(project_id)
    p["checkpoints"] = checkpoints
    return p

@app.post("/api/projects")
async def create_project(
    video: UploadFile = File(...),
    name: str = Form(...),
    source_lang: str = Form("zh"),
    target_lang: str = Form("en"),
    tts_voice: str = Form("en-US-JennyNeural"),
    audio_mode: str = Form("replace"),
    burn_subtitles: bool = Form(False)
):
    project_id = f"proj_{uuid.uuid4().hex[:10]}"
    project_dir = settings.projects_dir / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    file_ext = Path(video.filename).suffix or ".mp4"
    saved_video_path = project_dir / f"input_video{file_ext}"

    with open(saved_video_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    config = {
        "tts_voice": tts_voice,
        "audio_mode": audio_mode,
        "burn_subtitles": burn_subtitles,
        "original_filename": video.filename
    }

    proj = db.create_project(
        project_id=project_id,
        name=name,
        source_video_path=str(saved_video_path),
        config=config,
        source_lang=source_lang,
        target_lang=target_lang
    )

    return proj

@app.post("/api/projects/from-url")
def create_project_from_url(req: URLProjectRequest):
    project_id = f"proj_{uuid.uuid4().hex[:10]}"
    project_dir = settings.projects_dir / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    try:
        download_info = download_video_from_url(req.url, project_dir)
        saved_video_path = download_info["file_path"]
    except Exception as e:
        shutil.rmtree(project_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(e))

    config = {
        "tts_voice": req.tts_voice,
        "audio_mode": req.audio_mode,
        "burn_subtitles": req.burn_subtitles,
        "source_url": req.url
    }

    proj = db.create_project(
        project_id=project_id,
        name=req.name,
        source_video_path=saved_video_path,
        config=config,
        source_lang=req.source_lang,
        target_lang=req.target_lang
    )

    return proj

def run_project_background(project_id: str):
    try:
        orchestrator.run_pipeline(project_id)
    except Exception as e:
        logger.error(f"Background execution error for project {project_id}: {e}")

@app.post("/api/projects/{project_id}/start")
def start_project(project_id: str, background_tasks: BackgroundTasks):
    p = db.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    background_tasks.add_task(run_project_background, project_id)
    return {"status": "started", "project_id": project_id}

@app.post("/api/projects/{project_id}/resume")
def resume_project(project_id: str, background_tasks: BackgroundTasks):
    p = db.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    background_tasks.add_task(run_project_background, project_id)
    return {"status": "resumed", "project_id": project_id}

@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str):
    p = db.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    # Delete project directory
    project_dir = settings.projects_dir / project_id
    if project_dir.exists():
        shutil.rmtree(project_dir, ignore_errors=True)

    db.delete_project(project_id)
    return {"status": "deleted", "project_id": project_id}

@app.get("/api/projects/{project_id}/files/{filename}")
def download_project_file(project_id: str, filename: str):
    project_dir = settings.projects_dir / project_id
    file_path = project_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.get("/api/storage")
def storage_info():
    def get_dir_size(path: Path) -> int:
        if not path.exists():
            return 0
        total = 0
        for p in path.glob("**/*"):
            if p.is_file():
                total += p.stat().st_size
        return total

    models_size = get_dir_size(settings.models_dir)
    projects_size = get_dir_size(settings.projects_dir)
    temp_size = get_dir_size(settings.temp_dir)

    disk = get_system_diagnostics()

    return {
        "models_size_mb": round(models_size / (1024 * 1024), 2),
        "projects_size_mb": round(projects_size / (1024 * 1024), 2),
        "temp_size_mb": round(temp_size / (1024 * 1024), 2),
        "disk_free_gb": disk["disk_free_gb"],
        "disk_total_gb": disk["disk_total_gb"]
    }

@app.post("/api/storage/clean-temp")
def clean_temp_storage():
    shutil.rmtree(settings.temp_dir, ignore_errors=True)
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    return {"status": "temp_cleaned"}

@app.get("/api/logs")
def get_logs(limit: int = 100, project_id: Optional[str] = None):
    return db.get_logs(limit=limit, project_id=project_id)

@app.websocket("/ws/progress/{project_id}")
async def websocket_progress(websocket: WebSocket, project_id: str):
    await websocket.accept()
    if project_id not in active_connections:
        active_connections[project_id] = []
    active_connections[project_id].append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections[project_id].remove(websocket)

# Serve built frontend static files if present
frontend_dist = settings.data_dir.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
