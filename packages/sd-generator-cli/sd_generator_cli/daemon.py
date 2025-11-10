"""
Daemon process management for SD Generator services.

This module handles launching, stopping, and monitoring background services:
- Automatic1111 WebUI (Windows from WSL)
- Backend FastAPI server
- Frontend Vite dev server

Processes are launched in background with PID files for management.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Tuple

from rich.console import Console

console = Console()

# PID file locations
PID_DIR = Path.home() / ".sdgen" / "pids"
PID_FILES = {
    "a1111": PID_DIR / "automatic1111.pid",
    "backend": PID_DIR / "backend.pid",
    "frontend": PID_DIR / "frontend.pid",
    "watchdog": PID_DIR / "watchdog.pid",
}

# Log file locations
LOG_DIR = Path.home() / ".sdgen" / "logs"
LOG_FILES = {
    "a1111": LOG_DIR / "automatic1111.log",
    "backend": LOG_DIR / "backend.log",
    "frontend": LOG_DIR / "frontend.log",
    "watchdog": LOG_DIR / "watchdog.log",
}


def ensure_dirs():
    """Ensure PID and log directories exist."""
    PID_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def write_pid(service: str, pid: int):
    """
    Write PID to file.

    Args:
        service: Service name (a1111, backend, frontend)
        pid: Process ID
    """
    ensure_dirs()
    PID_FILES[service].write_text(str(pid))


def read_pid(service: str) -> Optional[int]:
    """
    Read PID from file.

    Args:
        service: Service name

    Returns:
        PID or None if not found
    """
    try:
        pid_text = PID_FILES[service].read_text().strip()
        return int(pid_text)
    except (FileNotFoundError, ValueError):
        return None


def delete_pid(service: str):
    """
    Delete PID file.

    Args:
        service: Service name
    """
    try:
        PID_FILES[service].unlink()
    except FileNotFoundError:
        pass


def is_process_running(pid: int) -> bool:
    """
    Check if process is running.

    Args:
        pid: Process ID

    Returns:
        True if running, False otherwise
    """
    try:
        os.kill(pid, 0)  # Signal 0 checks if process exists
        return True
    except (OSError, ProcessLookupError):
        return False


def get_service_status(service: str) -> Tuple[bool, Optional[int]]:
    """
    Get status of a service.

    Args:
        service: Service name

    Returns:
        Tuple of (is_running, pid)
    """
    pid = read_pid(service)
    if pid is None:
        return False, None

    running = is_process_running(pid)
    if not running:
        # Clean up stale PID file
        delete_pid(service)
        return False, None

    return True, pid


def stop_service(service: str, timeout: int = 5) -> bool:
    """
    Stop a service gracefully.

    Args:
        service: Service name
        timeout: Timeout in seconds

    Returns:
        True if stopped successfully
    """
    running, pid = get_service_status(service)

    if not running:
        return True

    # Type narrow: pid must be int here since running is True
    assert pid is not None

    try:
        # Try graceful shutdown first (SIGTERM)
        os.kill(pid, signal.SIGTERM)

        # Wait for process to die
        for _ in range(timeout * 10):
            if not is_process_running(pid):
                delete_pid(service)
                return True
            time.sleep(0.1)

        # Force kill if still alive
        console.print(f"[yellow]Force killing {service} (PID {pid})...[/yellow]")
        os.kill(pid, signal.SIGKILL)
        time.sleep(0.5)
        delete_pid(service)
        return True

    except ProcessLookupError:
        # Already dead
        delete_pid(service)
        return True
    except Exception as e:
        console.print(f"[red]Error stopping {service}: {e}[/red]")
        return False


def find_webui_package() -> Optional[Path]:
    """
    Find the sd-generator-webui package location.

    Priority:
    1. Python import (pip install)
    2. Monorepo structure (for development)

    Returns:
        Path to webui package or None if not found
    """
    # 1. Try to import the webui package (pip install)
    try:
        import sd_generator_webui  # type: ignore[import-untyped]
        webui_path = Path(sd_generator_webui.__file__).parent.parent.parent
        return webui_path
    except ImportError:
        pass

    # 2. Fallback: check monorepo structure
    cli_path = Path(__file__).parent.parent.parent
    webui_path = cli_path.parent / "sd-generator-webui"
    if webui_path.exists():
        return webui_path

    return None


def is_automatic1111_running(api_url: str) -> bool:
    """
    Check if Automatic1111 API is responding.

    Args:
        api_url: URL of the Automatic1111 API

    Returns:
        True if API responds
    """
    try:
        import requests
        response = requests.get(f"{api_url}/sdapi/v1/options", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def is_backend_running(port: int = 8000) -> bool:
    """
    Check if backend API is responding via HTTP.

    Args:
        port: Backend port (default: 8000)

    Returns:
        True if backend responds
    """
    try:
        import requests
        response = requests.get(f"http://localhost:{port}/docs", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def is_frontend_running(port: int = 5173) -> bool:
    """
    Check if frontend dev server is responding via HTTP.

    Args:
        port: Frontend port (default: 5173)

    Returns:
        True if frontend responds
    """
    try:
        import requests
        response = requests.get(f"http://localhost:{port}", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def start_automatic1111_windows(bat_path: str, api_url: str) -> Optional[int]:
    """
    Launch Automatic1111 on Windows from WSL.

    Args:
        bat_path: Path to webui.bat (WSL or Windows format)
        api_url: API URL for health check

    Returns:
        PID or None if error
    """
    try:
        # Check if already running
        if is_automatic1111_running(api_url):
            console.print("[yellow]⚠ Automatic1111 already running[/yellow]")
            return None

        # Convert WSL path to Windows path if needed
        if bat_path.startswith("/mnt/"):
            result = subprocess.run(
                ["wslpath", "-w", bat_path],
                capture_output=True,
                text=True,
                check=True
            )
            win_path = result.stdout.strip()
        else:
            win_path = bat_path

        # Check if file exists
        check_cmd = ["cmd.exe", "/c", "if", "exist", win_path, "echo", "EXISTS"]
        result = subprocess.run(check_cmd, capture_output=True, text=True)

        if "EXISTS" not in result.stdout:
            console.print(f"[red]✗ File not found: {win_path}[/red]")
            return None

        # Launch in background
        ensure_dirs()
        log_file = open(LOG_FILES["a1111"], "w")

        cmd = ["cmd.exe", "/c", "start", "/min", win_path]
        proc = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )

        # We can't get the real PID of the Windows process easily from WSL
        # So we just store a marker PID
        write_pid("a1111", 999999)  # Marker PID

        console.print(f"[green]✓ Automatic1111 started[/green]")
        console.print(f"[dim]Log: {LOG_FILES['a1111']}[/dim]")

        return 999999

    except Exception as e:
        console.print(f"[red]✗ Error starting Automatic1111: {e}[/red]")
        return None


def start_backend(backend_port: int, webui_path: Path, no_reload: bool = False, dev_mode: bool = False) -> Optional[int]:
    """
    Start FastAPI backend in background.

    Args:
        backend_port: Port to run on
        webui_path: Path to webui package
        no_reload: Disable auto-reload
        dev_mode: Force dev mode (separate frontend server)

    Returns:
        PID or None if error
    """
    backend_dir = webui_path / "backend"

    cmd = [
        "poetry", "run", "uvicorn",
        "sd_generator_webui.main:app",
        "--host", "0.0.0.0",  # nosec B104 - Intentional for local dev (allows WSL <-> Windows access)
        "--port", str(backend_port),
    ]

    if not no_reload:
        cmd.append("--reload")

    # Set env vars based on dev mode
    # Pass config file path to backend so it can find sdgen_config.json
    config_path = str(Path.cwd() / "sdgen_config.json")

    if dev_mode:
        # DEV MODE: Tell backend to not serve frontend (API only)
        env_vars = {
            **os.environ,
            "PATH": f"{os.environ.get('HOME')}/.local/bin:{os.environ.get('PATH')}",
            "SD_GENERATOR_DEV_MODE": "1",
            "SDGEN_CONFIG_PATH": config_path
        }
    else:
        # PRODUCTION MODE: Backend serves built frontend
        env_vars = {
            **os.environ,
            "PATH": f"{os.environ.get('HOME')}/.local/bin:{os.environ.get('PATH')}",
            "SDGEN_CONFIG_PATH": config_path
        }

    ensure_dirs()
    log_file = open(LOG_FILES["backend"], "w")

    proc = subprocess.Popen(
        cmd,
        cwd=backend_dir,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=env_vars
    )

    write_pid("backend", proc.pid)

    mode_str = "DEV" if dev_mode else "PRODUCTION"
    console.print(f"[green]✓ Backend started on http://0.0.0.0:{backend_port}[/green]")
    console.print(f"[dim]Mode: {mode_str} | PID: {proc.pid} | Log: {LOG_FILES['backend']}[/dim]")

    return proc.pid


def start_frontend(frontend_port: int, webui_path: Path, dev_mode: bool = False) -> Optional[int]:
    """
    Start Vite frontend in background (DEV MODE ONLY).

    In production mode, frontend is served by FastAPI backend from built static files.

    Args:
        frontend_port: Port to run on
        webui_path: Path to webui package
        dev_mode: Enable dev mode (separate frontend server)

    Returns:
        PID or None if error or production mode
    """
    # Check if we're in dev mode
    if not dev_mode:
        console.print("[yellow]⚠ Production mode: Frontend servi par le backend (pas de Vite séparé)[/yellow]")
        return None

    frontend_dir = webui_path / "front"

    # Check if frontend directory exists (dev mode)
    if not frontend_dir.exists():
        console.print(f"[red]✗ Frontend directory not found: {frontend_dir}[/red]")
        return None

    cmd = ["npm", "run", "serve", "--", "--port", str(frontend_port), "--host"]

    ensure_dirs()
    log_file = open(LOG_FILES["frontend"], "w")

    proc = subprocess.Popen(
        cmd,
        cwd=frontend_dir,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )

    write_pid("frontend", proc.pid)

    console.print(f"[green]✓ Frontend (DEV) started on http://localhost:{frontend_port}[/green]")
    console.print(f"[dim]PID: {proc.pid} | Log: {LOG_FILES['frontend']}[/dim]")

    return proc.pid


def start_watchdog(sessions_dir: Path, db_path: Optional[Path] = None) -> Optional[int]:
    """
    Start watchdog service in background.

    Args:
        sessions_dir: Directory containing session folders (e.g., ./apioutput)
        db_path: Optional database path (defaults to sessions_dir/../.sdgen/sessions.db)

    Returns:
        PID or None if error
    """
    # Verify watchdog package is installed
    try:
        import sd_generator_watchdog  # noqa: F401
    except ImportError:
        console.print("[red]✗ sd-generator-watchdog package not installed[/red]")
        console.print("[dim]  Run: poetry install (from project root)[/dim]")
        return None

    # Use same Python as current process (from venv)
    cmd = [sys.executable, "-m", "sd_generator_watchdog.cli", "run", "--sessions-dir", str(sessions_dir)]

    if db_path:
        cmd.extend(["--db-path", str(db_path)])

    ensure_dirs()
    log_file = open(LOG_FILES["watchdog"], "w")

    proc = subprocess.Popen(
        cmd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )

    write_pid("watchdog", proc.pid)

    console.print(f"[green]✓ Watchdog service started[/green]")
    console.print(f"[dim]Watching: {sessions_dir} | PID: {proc.pid} | Log: {LOG_FILES['watchdog']}[/dim]")

    return proc.pid


def get_all_services_status() -> Dict[str, Tuple[bool, Optional[int]]]:
    """
    Get status of all services.

    Returns:
        Dict mapping service name to (is_running, pid)
    """
    return {
        service: get_service_status(service)
        for service in ["a1111", "backend", "frontend"]
    }


def stop_all_services(timeout: int = 5) -> bool:
    """
    Stop all services.

    Args:
        timeout: Timeout per service in seconds

    Returns:
        True if all stopped successfully
    """
    all_stopped = True

    for service in ["frontend", "backend", "a1111"]:
        running, pid = get_service_status(service)
        if running:
            console.print(f"[cyan]Stopping {service}...[/cyan]")
            if not stop_service(service, timeout):
                all_stopped = False

    return all_stopped
