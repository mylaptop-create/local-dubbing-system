import sys
import os
import platform
import shutil
import psutil
from typing import Dict, Any, Optional

def detect_ffmpeg() -> Dict[str, Any]:
    # Check system PATH first
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return {"available": True, "path": ffmpeg_path, "type": "system"}

    # Check imageio-ffmpeg fallback
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return {"available": True, "path": exe, "type": "imageio_ffmpeg"}
    except ImportError:
        pass

    return {"available": False, "path": None, "type": "none"}

def detect_gpu() -> Dict[str, Any]:
    gpu_info = {
        "available": False,
        "name": None,
        "vram_mb": 0,
        "vram_gb": 0.0,
        "type": "none",
        "cuda_available": False,
    }

    # Try torch CUDA if torch is available
    try:
        import torch
        if torch.cuda.is_available():
            gpu_info["available"] = True
            gpu_info["cuda_available"] = True
            gpu_info["type"] = "cuda"
            gpu_info["name"] = torch.cuda.get_device_name(0)
            total_mem = torch.cuda.get_device_properties(0).total_memory
            gpu_info["vram_mb"] = int(total_mem / (1024 * 1024))
            gpu_info["vram_gb"] = round(total_mem / (1024 ** 3), 2)
            return gpu_info
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            gpu_info["available"] = True
            gpu_info["type"] = "mps"
            gpu_info["name"] = "Apple Silicon GPU (MPS)"
            return gpu_info
    except Exception:
        pass

    # Try nvidia-smi command if torch CUDA is not active
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        try:
            import subprocess
            out = subprocess.check_output(
                [nvidia_smi, "--query-gpu=gpu_name,memory.total", "--format=csv,noheader,nounits"],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            if out:
                parts = [p.strip() for p in out.splitlines()[0].split(",")]
                if len(parts) >= 2:
                    gpu_info["available"] = True
                    gpu_info["name"] = parts[0]
                    vram_mb = int(parts[1])
                    gpu_info["vram_mb"] = vram_mb
                    gpu_info["vram_gb"] = round(vram_mb / 1024, 2)
                    gpu_info["type"] = "nvidia"
        except Exception:
            pass

    return gpu_info

def get_system_diagnostics() -> Dict[str, Any]:
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(os.getcwd())
    ffmpeg_info = detect_ffmpeg()
    gpu_info = detect_gpu()

    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(logical=True),
        "ram_total_gb": round(ram.total / (1024 ** 3), 2),
        "ram_available_gb": round(ram.available / (1024 ** 3), 2),
        "ram_percent": ram.percent,
        "disk_total_gb": round(disk.total / (1024 ** 3), 2),
        "disk_free_gb": round(disk.free / (1024 ** 3), 2),
        "gpu": gpu_info,
        "ffmpeg": ffmpeg_info,
    }
