import sys
import argparse
import time
import json
import urllib.request
import urllib.error
from backend.core.diagnostics import get_system_diagnostics
from backend.database.manager import DatabaseManager
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.core.config import settings

def main():
    parser = argparse.ArgumentParser(prog="app", description="Local Video Dubbing System CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # app start
    subparsers.add_parser("start", help="Start backend server")

    # app doctor
    subparsers.add_parser("doctor", help="Run system diagnostics")

    # app status
    subparsers.add_parser("status", help="Show system and server status")

    # app logs
    subparsers.add_parser("logs", help="View recent application logs")

    # app project
    project_parser = subparsers.add_parser("project", help="Manage projects")
    proj_sub = project_parser.add_subparsers(dest="proj_command")
    proj_sub.add_parser("list", help="List all projects")

    resume_p = proj_sub.add_parser("resume", help="Resume project")
    resume_p.add_argument("project_id", type=str, help="Project ID")

    del_p = proj_sub.add_parser("delete", help="Delete project")
    del_p.add_argument("project_id", type=str, help="Project ID")

    # app benchmark
    subparsers.add_parser("benchmark", help="Run system benchmark test")

    args = parser.parse_args()

    if args.command == "doctor":
        diag = get_system_diagnostics()
        print("\n=== SYSTEM DIAGNOSTICS ===")
        print(f"OS: {diag['os']} ({diag['os_release']})")
        print(f"CPU Cores: {diag['cpu_count']}")
        print(f"RAM: {diag['ram_available_gb']} GB available / {diag['ram_total_gb']} GB total")
        print(f"Disk Free: {diag['disk_free_gb']} GB")
        print(f"GPU: {diag['gpu']['name'] if diag['gpu']['available'] else 'None detected'}")
        print(f"FFmpeg: {diag['ffmpeg']['path'] if diag['ffmpeg']['available'] else 'Not found'}\n")

    elif args.command == "start":
        import uvicorn
        print(f"Starting {settings.app_name} on http://{settings.host}:{settings.port} ...")
        uvicorn.run("backend.api.app:app", host=settings.host, port=settings.port, reload=False)

    elif args.command == "status":
        print("\n=== APPLICATION STATUS ===")
        try:
            req = urllib.request.urlopen(f"http://{settings.host}:{settings.port}/api/health", timeout=2)
            res = json.loads(req.read().decode())
            print(f"Server Status: Running ({res['status']})")
        except Exception:
            print("Server Status: Not running")

        db = DatabaseManager()
        projects = db.list_projects()
        print(f"Total Projects: {len(projects)}\n")

    elif args.command == "logs":
        db = DatabaseManager()
        logs = db.get_logs(limit=20)
        print("\n=== RECENT LOGS ===")
        for l in logs:
            print(f"[{l['created_at']}] [{l['level']}] {l['message']}")
        print("")

    elif args.command == "project":
        db = DatabaseManager()
        if args.proj_command == "list":
            projects = db.list_projects()
            print("\n=== PROJECTS ===")
            for p in projects:
                print(f"ID: {p['id']} | Name: {p['name']} | Status: {p['status']} ({p['progress_pct']}%) | Stage: {p['current_stage']}")
            print("")
        elif args.proj_command == "resume":
            print(f"Resuming project {args.project_id}...")
            orchestrator = PipelineOrchestrator(db_manager=db)
            res = orchestrator.run_pipeline(args.project_id)
            print(f"Project status: {res['status']}")
        elif args.proj_command == "delete":
            db.delete_project(args.project_id)
            print(f"Project {args.project_id} deleted successfully.")

    elif args.command == "benchmark":
        print("\n=== RUNNING PIPELINE BENCHMARK ===")
        diag = get_system_diagnostics()
        print(f"Diagnostics: OS={diag['os']}, GPU={diag['gpu']['available']}, RAM={diag['ram_total_gb']}GB")
        start_t = time.time()
        # Benchmark dummy pipeline run
        from backend.media.ffmpeg import MediaEngine
        engine = MediaEngine()
        dur = round(time.time() - start_t, 3)
        print(f"FFmpeg engine initialized in {dur} seconds.")
        print("Benchmark completed successfully.\n")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
