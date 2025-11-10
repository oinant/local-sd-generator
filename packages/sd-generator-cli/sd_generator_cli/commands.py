"""
Environment management commands for SD Generator.

Commands:
- start: Start all services (A1111 + backend + frontend)
- stop: Stop all services
- status: Show status of all services
- config: Read/write configuration values
- webui: Subcommands for WebUI only (backend + frontend)
"""

import json
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sd_generator_cli import daemon
from sd_generator_cli.config.global_config import load_global_config

console = Console()


def start_command(
    start_a1111: bool = typer.Option(False, "--start-a1111", help="Start Automatic1111 on Windows (WSL only)"),
    a1111_bat: Optional[str] = typer.Option(None, "--a1111-bat", help="Path to Automatic1111 webui.bat"),
    backend_port: int = typer.Option(8000, "--backend-port", "-bp", help="Backend server port"),
    frontend_port: int = typer.Option(5173, "--frontend-port", "-fp", help="Frontend dev server port"),
    no_frontend: bool = typer.Option(False, "--no-frontend", help="Don't start frontend"),
    no_reload: bool = typer.Option(False, "--no-reload", help="Disable backend auto-reload"),
    dev_mode: bool = typer.Option(False, "--dev-mode", help="Start in dev mode (separate frontend server)"),
):
    """
    Start the complete SD Generator environment.

    Launches services in background (non-blocking):
    - Automatic1111 WebUI (optional, --start-a1111)
    - Backend FastAPI server
    - Frontend Vite dev server (unless --no-frontend)

    Examples:
        sdgen start
        sdgen start --start-a1111
        sdgen start --start-a1111 --a1111-bat /mnt/d/sd/webui.bat
        sdgen start --no-frontend --backend-port 8080
    """
    console.print(Panel.fit(
        "[bold cyan]SD Generator - Starting Environment[/bold cyan]",
        border_style="cyan"
    ))

    try:
        # Load config
        config = load_global_config()
        api_url = config.api_url

        # 1. Start Automatic1111 (if requested)
        if start_a1111:
            console.print("\n[cyan]→ Starting Automatic1111...[/cyan]")

            # a1111_bat must be provided via --a1111-bat flag
            if not a1111_bat:
                console.print("[red]✗ No webui.bat path provided[/red]")
                console.print("[yellow]→ Use --a1111-bat /path/to/webui.bat[/yellow]")
            else:
                daemon.start_automatic1111_windows(a1111_bat, api_url)
                console.print("[dim]Waiting 10s for API startup...[/dim]")
                time.sleep(10)

        # 2. Find WebUI package
        console.print("\n[cyan]→ Locating WebUI package...[/cyan]")
        webui_path = daemon.find_webui_package()

        if not webui_path:
            console.print("[red]✗ WebUI package not found[/red]")
            console.print("[yellow]→ Install with: poetry install (in packages/sd-generator-webui)[/yellow]")
            raise typer.Exit(code=1)

        console.print(f"[green]✓ Found WebUI at: {webui_path}[/green]")

        # 3. Start Backend
        console.print("\n[cyan]→ Starting backend...[/cyan]")
        daemon.start_backend(backend_port, webui_path, no_reload, dev_mode=dev_mode)
        time.sleep(2)  # Give backend time to start

        # 4. Start Frontend (if not disabled and in dev mode)
        if not no_frontend and dev_mode:
            console.print("\n[cyan]→ Starting frontend...[/cyan]")
            daemon.start_frontend(frontend_port, webui_path, dev_mode=True)

        # Display final status
        console.print("\n")
        table = Table(title="Services Started", border_style="green")
        table.add_column("Service", style="cyan")
        table.add_column("URL", style="green")

        if start_a1111 and a1111_bat:
            table.add_row("Automatic1111", api_url)
        table.add_row("Backend API", f"http://localhost:{backend_port}/docs")
        if not no_frontend:
            table.add_row("Frontend", f"http://localhost:{frontend_port}")

        console.print(table)

        # Display auth token if configured
        if config.webui_token:
            console.print(f"\n[yellow]🔑 Auth Token: {config.webui_token}[/yellow]")
            console.print("[dim]   Use this token to authenticate with the WebUI[/dim]")

        console.print("\n[bold green]✓ All services started in background[/bold green]")
        console.print("[dim]Use 'sdgen stop' to stop all services[/dim]")
        console.print("[dim]Use 'sdgen status' to check service status[/dim]\n")

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(code=1)


def stop_command():
    """
    Stop all SD Generator services.

    Stops:
    - Automatic1111 (if managed by sdgen)
    - Backend FastAPI server
    - Frontend Vite dev server

    Examples:
        sdgen stop
    """
    console.print("[cyan]Stopping all services...[/cyan]\n")

    success = daemon.stop_all_services(timeout=5)

    if success:
        console.print("\n[bold green]✓ All services stopped[/bold green]")
    else:
        console.print("\n[yellow]⚠ Some services failed to stop[/yellow]")
        raise typer.Exit(code=1)


def status_command() -> None:
    """
    Show status of all SD Generator services.

    Prerequisites:
    1. Check config file exists and is valid
    2. If OK, display service status table
    3. If KO, show error and exit

    Displays:
    - Automatic1111 status (checks API, not just PID)
    - Backend status
    - Frontend status

    Examples:
        sdgen status
    """
    # STEP 1: Validate config file (mandatory)
    try:
        config = load_global_config()
    except FileNotFoundError:
        console.print(
            "[red]✗ Config file error:[/red] No sdgen_config.json file found.\n"
            "[yellow]→ Please run 'sdgen init' to create config[/yellow]\n"
            "[yellow]→ Or check that you are in the intended folder[/yellow]"
        )
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(
            f"[red]✗ Config file error:[/red] Your sdgen_config.json is not valid.\n"
            f"[yellow]→ Error: {e}[/yellow]\n"
            "[yellow]→ Please fix the config file or run 'sdgen init' to recreate it[/yellow]"
        )
        raise typer.Exit(code=1)

    # STEP 2: Config OK, get service status
    statuses = daemon.get_all_services_status()

    # Check if services are actually responding via HTTP (handles external launches)
    a1111_api_running = daemon.is_automatic1111_running(config.api_url)
    backend_api_running = daemon.is_backend_running(port=8000)  # TODO: Get from config?
    frontend_running = daemon.is_frontend_running(port=5173)   # TODO: Get from config?

    # Build status table
    table = Table(title="Service Status", border_style="cyan")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("PID", style="blue")

    service_names = {
        "a1111": "Automatic1111",
        "backend": "Backend API",
        "frontend": "Frontend"
    }

    for service, (pid_running, pid) in statuses.items():
        name = service_names[service]

        # Check API/HTTP status for each service
        if service == "a1111":
            api_running = a1111_api_running
        elif service == "backend":
            api_running = backend_api_running
        else:  # frontend
            api_running = frontend_running

        # Determine status and PID display
        if api_running:
            # Service responds via HTTP
            status = "[green]Running[/green]"
            if pid:
                # PID exists (launched by sdgen)
                pid_str = str(pid) if pid != 999999 else "N/A (Windows)"
            else:
                # No PID (launched externally)
                pid_str = "External"
        else:
            # Service does not respond
            status = "[red]Stopped[/red]"
            pid_str = "—"

        table.add_row(name, status, pid_str)

    console.print(table)

    # Show log locations
    console.print("\n[dim]Log files: ~/.sdgen/logs/[/dim]")
    console.print("[dim]PID files: ~/.sdgen/pids/[/dim]\n")


def config_command(
    key: Optional[str] = typer.Argument(None, help="Config key to read/write or 'renew-token'"),
    value: Optional[str] = typer.Argument(None, help="Value to set (optional)"),
    list_all: bool = typer.Option(False, "--list", "-l", help="List all config keys"),
) -> None:
    """
    Read or write configuration values.

    Examples:
        sdgen config list              # List all config
        sdgen config api_url           # Read api_url
        sdgen config api_url http://... # Set api_url
        sdgen config renew-token        # Generate new WebUI token
    """
    # Define valid config keys
    VALID_KEYS = ["api_url", "configs_dir", "output_dir", "webui_token"]

    config_path = Path.cwd() / "sdgen_config.json"

    # Check if config file exists
    if not config_path.exists():
        console.print("[red]✗ No config file found.[/red]")
        console.print("[yellow]→ Run 'sdgen init' first.[/yellow]")
        raise typer.Exit(code=1)

    # Load config file
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except json.JSONDecodeError:
        console.print("[red]✗ Config file is invalid.[/red]")
        console.print("[yellow]→ Please fix or recreate with 'sdgen init'.[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗ Error reading config: {e}[/red]")
        raise typer.Exit(code=1)

    # MODE 1: List all keys
    if list_all or key == "list":
        table = Table(title="Configuration", border_style="cyan")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")

        for k in VALID_KEYS:
            v = config_data.get(k)
            display_value = str(v) if v is not None else "[dim]not set[/dim]"
            table.add_row(k, display_value)

        console.print(table)
        console.print()
        return

    # MODE SPECIAL: Renew token
    if key == "renew-token":
        from sd_generator_cli.config.global_config import generate_webui_token

        # Generate new token
        new_token = generate_webui_token()

        # Update config
        config_data["webui_token"] = new_token

        # Save updated config
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                f.write('\n')

            console.print(f"[green]✓ New WebUI token generated:[/green] {new_token}")
            console.print(f"[dim]  Token updated in {config_path}[/dim]")
            console.print()
            console.print("[yellow]⚠  WebUI services need to be restarted to use the new token.[/yellow]")
            console.print("[cyan]   Run: sdgen webui restart[/cyan]")
            console.print()

        except Exception as e:
            console.print(f"[red]✗ Error writing config: {e}[/red]")
            raise typer.Exit(code=1)

        return

    # MODE 2 & 3: Read or write a specific key
    if key is None:
        console.print("[red]✗ No key provided.[/red]")
        console.print("[yellow]→ Usage: sdgen config <key> [value][/yellow]")
        console.print(f"[yellow]→ Valid keys: {', '.join(VALID_KEYS)}[/yellow]")
        raise typer.Exit(code=1)

    # Validate key
    if key not in VALID_KEYS:
        console.print(f"[red]✗ Config key '{key}' does not exist.[/red]")
        console.print(f"[yellow]→ Valid keys: {', '.join(VALID_KEYS)}[/yellow]")
        raise typer.Exit(code=1)

    # MODE 2: Read mode (no value provided)
    if value is None:
        current_value = config_data.get(key)
        if current_value is not None:
            console.print(str(current_value))
        else:
            console.print("[dim]not set[/dim]")
        return

    # MODE 3: Write mode (value provided)
    config_data[key] = value

    # Save updated config
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Add trailing newline

        console.print(f"[green]✓ {key} set to {value}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Error writing config: {e}[/red]")
        raise typer.Exit(code=1)


# WebUI subcommand group
webui_app = typer.Typer(
    name="webui",
    help="Manage WebUI services (backend + frontend)"
)


@webui_app.command(name="start")
def webui_start(
    dev_mode: bool = typer.Option(False, "--dev-mode", help="Start in dev mode (separate frontend server)"),
    backend_port: int = typer.Option(8000, "--backend-port", "-bp", help="Backend server port"),
    frontend_port: int = typer.Option(5173, "--frontend-port", "-fp", help="Frontend dev server port"),
    no_reload: bool = typer.Option(False, "--no-reload", help="Disable backend auto-reload"),
):
    """
    Start WebUI services.

    Production mode (default): Backend serves built frontend
    Dev mode (--dev-mode): Backend + separate Vite dev server

    Examples:
        sdgen webui start                    # Production mode
        sdgen webui start --dev-mode         # Dev mode
        sdgen webui start --backend-port 8080
    """
    mode_str = "DEV" if dev_mode else "PRODUCTION"
    console.print(f"[cyan]Starting WebUI services ({mode_str} mode)...[/cyan]\n")

    try:
        # Find WebUI package
        webui_path = daemon.find_webui_package()
        if not webui_path:
            console.print("[red]✗ WebUI package not found[/red]")
            raise typer.Exit(code=1)

        # Get sessions directory from config
        try:
            config = load_global_config()
            sessions_dir = Path(config.output_dir)
        except Exception:
            # Fallback to default
            sessions_dir = Path.cwd() / "apioutput"

        # Start watchdog services
        console.print("[cyan]→ Starting session watchdog...[/cyan]")
        daemon.start_watchdog(sessions_dir)
        time.sleep(1)

        console.print("[cyan]→ Starting thumbnail watchdog...[/cyan]")
        daemon.start_thumbnail_watchdog(sessions_dir)
        time.sleep(1)

        # Start backend
        console.print("[cyan]→ Starting backend...[/cyan]")
        daemon.start_backend(backend_port, webui_path, no_reload, dev_mode=dev_mode)
        time.sleep(2)

        frontend_pid = None
        if dev_mode:
            # Dev mode: Start separate frontend
            console.print("[cyan]→ Starting frontend dev server...[/cyan]")
            frontend_pid = daemon.start_frontend(frontend_port, webui_path, dev_mode=True)

        # Display URLs based on mode
        console.print("\n[bold green]✓ WebUI services started[/bold green]")
        console.print(f"[dim]Backend API: http://localhost:{backend_port}/docs[/dim]")

        if dev_mode and frontend_pid:
            # Dev mode: frontend on separate port
            console.print(f"[dim]Frontend (DEV): http://localhost:{frontend_port}[/dim]")
        else:
            # Production mode: frontend served by backend
            console.print(f"[dim]Frontend (PROD): http://localhost:{backend_port}[/dim]")

        # Display auth token if configured
        try:
            config = load_global_config()
            if config.webui_token:
                console.print(f"\n[yellow]🔑 Auth Token: {config.webui_token}[/yellow]")
                console.print("[dim]   Use this token to authenticate with the WebUI[/dim]")
        except Exception:
            pass  # Silently ignore if config not found

        console.print()

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(code=1)


@webui_app.command(name="stop")
def webui_stop():
    """
    Stop WebUI services (backend + frontend + watchdog).

    Examples:
        sdgen webui stop
    """
    console.print("[cyan]Stopping WebUI services...[/cyan]\n")

    watchdog_stopped = daemon.stop_service("watchdog")
    thumbnail_watchdog_stopped = daemon.stop_service("thumbnail_watchdog")
    backend_stopped = daemon.stop_service("backend")
    frontend_stopped = daemon.stop_service("frontend")

    if watchdog_stopped and thumbnail_watchdog_stopped and backend_stopped and frontend_stopped:
        console.print("[bold green]✓ WebUI services stopped[/bold green]")
    else:
        console.print("[yellow]⚠ Some services failed to stop[/yellow]")
        raise typer.Exit(code=1)


@webui_app.command(name="restart")
def webui_restart(
    dev_mode: bool = typer.Option(False, "--dev-mode", help="Start in dev mode (separate frontend server)"),
    backend_port: int = typer.Option(8000, "--backend-port", "-bp", help="Backend server port"),
    frontend_port: int = typer.Option(5173, "--frontend-port", "-fp", help="Frontend dev server port"),
    no_reload: bool = typer.Option(False, "--no-reload", help="Disable backend auto-reload"),
):
    """
    Restart WebUI services (backend + frontend + watchdog).

    Examples:
        sdgen webui restart
        sdgen webui restart --dev-mode
    """
    mode_str = "DEV" if dev_mode else "PRODUCTION"
    console.print(f"[cyan]Restarting WebUI services ({mode_str} mode)...[/cyan]\n")

    # Stop first
    daemon.stop_service("watchdog")
    daemon.stop_service("thumbnail_watchdog")
    daemon.stop_service("backend")
    daemon.stop_service("frontend")
    time.sleep(1)

    # Start again
    try:
        webui_path = daemon.find_webui_package()
        if not webui_path:
            console.print("[red]✗ WebUI package not found[/red]")
            raise typer.Exit(code=1)

        # Get sessions directory from config
        try:
            config = load_global_config()
            sessions_dir = Path(config.output_dir)
        except Exception:
            sessions_dir = Path.cwd() / "apioutput"

        console.print("[cyan]→ Starting session watchdog...[/cyan]")
        daemon.start_watchdog(sessions_dir)
        time.sleep(1)

        console.print("[cyan]→ Starting thumbnail watchdog...[/cyan]")
        daemon.start_thumbnail_watchdog(sessions_dir)
        time.sleep(1)

        console.print("[cyan]→ Starting backend...[/cyan]")
        daemon.start_backend(backend_port, webui_path, no_reload, dev_mode=dev_mode)
        time.sleep(2)

        if dev_mode:
            console.print("[cyan]→ Starting frontend dev server...[/cyan]")
            daemon.start_frontend(frontend_port, webui_path, dev_mode=True)

        console.print("\n[bold green]✓ WebUI services restarted[/bold green]\n")

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(code=1)


@webui_app.command(name="status")
def webui_status():
    """
    Show WebUI services status (watchdogs + backend + frontend).

    Examples:
        sdgen webui status
    """
    watchdog_running, watchdog_pid = daemon.get_service_status("watchdog")
    thumbnail_watchdog_running, thumbnail_watchdog_pid = daemon.get_service_status("thumbnail_watchdog")
    backend_running, backend_pid = daemon.get_service_status("backend")
    frontend_running, frontend_pid = daemon.get_service_status("frontend")

    table = Table(title="WebUI Status", border_style="cyan")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("PID", style="blue")

    table.add_row(
        "Session Watchdog",
        "[green]Running[/green]" if watchdog_running else "[red]Stopped[/red]",
        str(watchdog_pid) if watchdog_pid else "—"
    )
    table.add_row(
        "Thumbnail Watchdog",
        "[green]Running[/green]" if thumbnail_watchdog_running else "[red]Stopped[/red]",
        str(thumbnail_watchdog_pid) if thumbnail_watchdog_pid else "—"
    )
    table.add_row(
        "Backend",
        "[green]Running[/green]" if backend_running else "[red]Stopped[/red]",
        str(backend_pid) if backend_pid else "—"
    )
    table.add_row(
        "Frontend",
        "[green]Running[/green]" if frontend_running else "[red]Stopped[/red]",
        str(frontend_pid) if frontend_pid else "—"
    )

    console.print(table)
    console.print()
