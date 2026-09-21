import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.core.config import settings

logger = logging.getLogger(__name__)

DB_PATH = settings.data_dir / "app.db"

def init_db(db_path: Path = DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Projects table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        source_video_path TEXT NOT NULL,
        source_lang TEXT DEFAULT 'zh',
        target_lang TEXT DEFAULT 'en',
        status TEXT NOT NULL,
        current_stage TEXT NOT NULL,
        progress_pct REAL DEFAULT 0.0,
        config_json TEXT NOT NULL,
        segments_json TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Stage checkpoints table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_checkpoints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        stage TEXT NOT NULL,
        status TEXT NOT NULL,
        output_files_json TEXT NOT NULL,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
    )
    """)

    # System logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT,
        level TEXT NOT NULL,
        stage TEXT,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def create_project(
        self,
        project_id: str,
        name: str,
        source_video_path: str,
        config: Dict[str, Any],
        source_lang: str = "zh",
        target_lang: str = "en"
    ) -> Dict[str, Any]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO projects (id, name, source_video_path, source_lang, target_lang, status, current_stage, progress_pct, config_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                name,
                source_video_path,
                source_lang,
                target_lang,
                "CREATED",
                "MEDIA_ANALYSIS",
                0.0,
                json.dumps(config)
            )
        )
        conn.commit()
        conn.close()
        return self.get_project(project_id)

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        res = dict(row)
        res["config"] = json.loads(res["config_json"])
        res["segments"] = json.loads(res["segments_json"])
        return res

    def list_projects(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        conn.close()
        projects = []
        for r in rows:
            p = dict(r)
            p["config"] = json.loads(p["config_json"])
            p["segments"] = json.loads(p["segments_json"])
            projects.append(p)
        return projects

    def update_project_status(
        self,
        project_id: str,
        status: str,
        current_stage: str,
        progress_pct: float,
        segments: Optional[List[Dict[str, Any]]] = None
    ):
        conn = self._get_connection()
        cursor = conn.cursor()
        if segments is not None:
            cursor.execute(
                """
                UPDATE projects
                SET status = ?, current_stage = ?, progress_pct = ?, segments_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, current_stage, progress_pct, json.dumps(segments), project_id)
            )
        else:
            cursor.execute(
                """
                UPDATE projects
                SET status = ?, current_stage = ?, progress_pct = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, current_stage, progress_pct, project_id)
            )
        conn.commit()
        conn.close()

    def record_checkpoint(
        self,
        project_id: str,
        stage: str,
        status: str,
        output_files: Dict[str, str],
        error_message: Optional[str] = None
    ):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO project_checkpoints (project_id, stage, status, output_files_json, error_message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (project_id, stage, status, json.dumps(output_files), error_message)
        )
        conn.commit()
        conn.close()

    def get_checkpoints(self, project_id: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM project_checkpoints WHERE project_id = ? ORDER BY id ASC",
            (project_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        checkpoints = []
        for r in rows:
            c = dict(r)
            c["output_files"] = json.loads(c["output_files_json"])
            checkpoints.append(c)
        return checkpoints

    def delete_project(self, project_id: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM project_checkpoints WHERE project_id = ?", (project_id,))
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        conn.close()

    def add_log(self, level: str, message: str, project_id: Optional[str] = None, stage: Optional[str] = None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO system_logs (project_id, level, stage, message) VALUES (?, ?, ?, ?)",
            (project_id, level, stage, message)
        )
        conn.commit()
        conn.close()

    def get_logs(self, limit: int = 100, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        if project_id:
            cursor.execute(
                "SELECT * FROM system_logs WHERE project_id = ? ORDER BY id DESC LIMIT ?",
                (project_id, limit)
            )
        else:
            cursor.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
