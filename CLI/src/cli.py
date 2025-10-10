#!/usr/bin/env python3
"""
SD Image Generator - YAML Template CLI (Phase 2 - Typer Edition)

Modern command-line interface powered by Typer for Phase 2 YAML template-driven
image generation. Supports interactive template selection and direct execution
with improved UX.

Usage:
    python3 template_cli_typer.py generate                     # Interactive mode
    python3 template_cli_typer.py generate -t path.yaml       # Direct template
    python3 template_cli_typer.py list                        # List templates
    python3 template_cli_typer.py init                        # Initialize config
    python3 template_cli_typer.py validate path.yaml          # Validate template
    python3 template_cli_typer.py api samplers                # List samplers
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from config.global_config import load_global_config, ensure_global_config


def normalize_prompt(prompt: str) -> str:
    """
    Normalize prompt by replacing newlines with commas and cleaning up.

    Args:
        prompt: Raw prompt string with possible newlines

    Returns:
        Normalized prompt with clean comma separation
    """
    # Replace newlines with ", "
    normalized = prompt.replace('\n', ', ').replace('\r', '')

    # Clean up multiple commas and spaces
    normalized = re.sub(r',(\s*,)+', ',', normalized)  # Multiple commas with optional spaces
    normalized = re.sub(r'\s+', ' ', normalized)        # Multiple spaces → single space
    normalized = re.sub(r',\s+', ', ', normalized)      # Normalize space after comma
    normalized = re.sub(r'\s+,', ',', normalized)       # Remove space before comma
    normalized = normalized.strip()                      # Trim edges

    return normalized

# Initialize Typer app and Rich console
app = typer.Typer(
    name="sdgen",
    help="SD Image Generator - YAML Template Mode (Phase 2)",
    add_completion=False,
    no_args_is_help=True
)
console = Console()

# Create API subcommand group
api_app = typer.Typer(
    name="api",
    help="API introspection commands (list models, samplers, etc.)"
)
app.add_typer(api_app, name="api")


def check_tty() -> bool:
    """Check if running in a TTY (interactive terminal)."""
    return sys.stdin.isatty()


def find_yaml_templates(configs_dir: Path) -> list[Path]:
    """
    Find all .prompt.yaml template files in configs directory.

    Args:
        configs_dir: Directory to search

    Returns:
        List of paths to .prompt.yaml files
    """
    templates = []
    for yaml_file in configs_dir.rglob("*.prompt.yaml"):
        templates.append(yaml_file)
    templates.sort(key=lambda p: p.name)
    return templates


def _generate(
    template_path: Path,
    global_config: Any,
    count: Optional[int],
    api_url: str,
    dry_run: bool,
    console: Console
):
    """
    Generate images using Template System V2.0.

    Supports:
    - Template inheritance with implements:
    - Modular imports with imports:
    - Reusable chunks
    - Advanced selectors and weights

    Args:
        template_path: Path to template file
        global_config: Global configuration object
        count: Maximum number of images to generate
        api_url: SD API URL
        dry_run: Dry-run mode flag
        console: Rich console for output
    """
    from templating.orchestrator import V2Pipeline
    from api import SDAPIClient, BatchGenerator, SessionManager, ImageWriter, ProgressReporter
    from api import PromptConfig

    try:
        # Initialize V2 Pipeline
        console.print(f"[cyan]Initializing V2 Pipeline...[/cyan]")
        pipeline = V2Pipeline(configs_dir=str(global_config.configs_dir))

        # Load and process template
        console.print(f"[cyan]Loading template:[/cyan] {template_path}")
        prompts = pipeline.run(str(template_path))

        # Apply count limit if specified
        if count is not None and len(prompts) > count:
            console.print(f"[yellow]Limiting to {count} prompts (from {len(prompts)})[/yellow]")
            prompts = prompts[:count]

        console.print(f"[green]✓ Generated {len(prompts)} prompt variations[/green]\n")

        # Session setup
        session_name = template_path.stem.lower().replace(" ", "_").replace("-", "_")
        output_base_dir = Path(global_config.output_dir)

        # Initialize API components
        api_client = SDAPIClient(api_url=api_url)
        session_manager = SessionManager(
            base_output_dir=str(output_base_dir),
            session_name=session_name,
            dry_run=dry_run
        )
        image_writer = ImageWriter(session_manager.output_dir)
        progress_reporter = ProgressReporter(
            total_images=len(prompts),
            output_dir=session_manager.output_dir,
            verbose=True
        )

        # Create batch generator
        generator = BatchGenerator(
            api_client=api_client,
            session_manager=session_manager,
            image_writer=image_writer,
            progress_reporter=progress_reporter,
            dry_run=dry_run
        )

        session_dir = Path(session_manager.output_dir)

        console.print(Panel(
            f"[bold]Output:[/bold] {session_dir}",
            title="Starting Image Generation (V2.0)",
            border_style="green"
        ))

        # Create output directory
        session_manager.create_session_dir()

        # Save JSON manifest
        manifest_path = session_dir / f"{session_name}_manifest.json"
        manifest = {
            "session_name": session_name,
            "template_source": str(template_path),
            "generated_at": datetime.now().isoformat(),
            "total_variations": len(prompts),
            "templating_system": "v2.0",
            "variations": []
        }

        for idx, prompt_dict in enumerate(prompts):
            manifest["variations"].append({
                "index": idx,
                "prompt": prompt_dict['prompt'],
                "negative_prompt": prompt_dict.get('negative_prompt', ''),
                "seed": prompt_dict.get('seed', -1),
                "variations": prompt_dict.get('variations', {}),
                "parameters": prompt_dict.get('parameters', {})
            })

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        console.print(f"[green]✓ Manifest saved:[/green] {manifest_path}\n")

        # Test connection if not in dry-run mode
        if not dry_run:
            console.print(f"[cyan]Connecting to SD API:[/cyan] {api_url}")
            if not api_client.test_connection():
                console.print("[red]✗ Failed to connect to SD API[/red]")
                console.print("   [yellow]Make sure Stable Diffusion WebUI is running[/yellow]")
                raise typer.Exit(code=1)
            console.print("[green]✓ Connected to SD API[/green]\n")

        # Apply generation parameters from first prompt's parameters
        if prompts and 'parameters' in prompts[0]:
            from api import GenerationConfig
            params = prompts[0]['parameters']
            gen_config = GenerationConfig(
                width=params.get('width', 512),
                height=params.get('height', 512),
                steps=params.get('steps', 20),
                cfg_scale=params.get('cfg_scale', 7.0),
                sampler_name=params.get('sampler', 'Euler a'),
                scheduler=params.get('scheduler', 'automatic'),
                batch_size=params.get('batch_size', 1),
                n_iter=params.get('n_iter', 1),
                enable_hr=params.get('enable_hr', False),
                hr_scale=params.get('hr_scale', 2.0),
                hr_upscaler=params.get('hr_upscaler', 'Latent'),
                denoising_strength=params.get('denoising_strength', 0.7),
                hr_second_pass_steps=params.get('hr_second_pass_steps', 0)
            )
            api_client.generation_config = gen_config

        # Convert V2 prompts to PromptConfig list
        prompt_configs = []
        for idx, prompt_dict in enumerate(prompts):
            prompt_cfg = PromptConfig(
                prompt=prompt_dict['prompt'],
                negative_prompt=prompt_dict.get('negative_prompt', ''),
                seed=prompt_dict.get('seed', -1),
                filename=f"{session_name}_{idx:04d}.png"
            )
            prompt_configs.append(prompt_cfg)

        # Generate images
        success_count, total_count = generator.generate_batch(
            prompt_configs=prompt_configs,
            delay_between_images=2.0
        )

        fail_count = total_count - success_count

        # Display final summary
        summary = f"""[bold]Total images:[/bold] {total_count}
[bold green]Success:[/bold green] {success_count}
[bold red]Failed:[/bold red] {fail_count}"""

        if dry_run:
            summary += f"\n\n[yellow]Dry-run mode: API requests saved to:[/yellow]\n  {session_dir}"
        else:
            summary += f"\n\n[green]Images saved to:[/green]\n  {session_dir}"

        console.print(Panel(summary, title="✓ Generation Complete (V2.0)", border_style="green"))

    except Exception as e:
        console.print(f"\n[red]✗ V2 Pipeline error:[/red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(code=1)


def select_template_interactive(configs_dir: Path) -> Path:
    """
    Interactive template selection with Rich formatting.

    Args:
        configs_dir: Directory containing templates

    Returns:
        Path to selected template

    Raises:
        typer.Exit: If no templates found or invalid selection
    """
    templates = find_yaml_templates(configs_dir)

    if not templates:
        console.print(f"[red]✗ No .prompt.yaml templates found in {configs_dir}[/red]")
        raise typer.Exit(code=1)

    # Create Rich table
    table = Table(title=f"Select YAML Template ({len(templates)} available)")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Name", style="green")
    table.add_column("Path", style="blue")

    for idx, template_path in enumerate(templates, 1):
        try:
            from templating.orchestrator import V2Pipeline
            pipeline = V2Pipeline()
            config = pipeline.load(str(template_path))
            name = config.name
            rel_path = str(template_path.relative_to(configs_dir))
        except Exception:
            name = template_path.stem
            rel_path = str(template_path)

        table.add_row(str(idx), name, rel_path)

    console.print(table)

    while True:
        try:
            choice = console.input(f"\n[bold]Select template (1-{len(templates)}): [/bold]").strip()

            if not choice:
                console.print("[red]No selection made[/red]")
                raise typer.Exit(code=1)

            idx = int(choice) - 1

            if 0 <= idx < len(templates):
                return templates[idx]
            else:
                console.print(f"[yellow]Invalid selection. Please enter 1-{len(templates)}[/yellow]")

        except ValueError:
            console.print("[yellow]Invalid input. Please enter a number.[/yellow]")
        except KeyboardInterrupt:
            console.print("\n[red]Selection cancelled[/red]")
            raise typer.Exit(code=130)


@app.command(name="generate")
def generate_images(
    template: Optional[Path] = typer.Option(
        None,
        "--template", "-t",
        help="Path to .prompt.yaml template file",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    count: Optional[int] = typer.Option(
        None,
        "--count", "-n",
        help="Maximum number of variations to generate",
        min=1,
    ),
    api_url: Optional[str] = typer.Option(
        None,
        "--api-url",
        help="Override Stable Diffusion API URL",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Save API requests as JSON instead of generating images",
    ),
):
    """
    Generate images from YAML template using V2.0 Template System.

    If no template is specified, enters interactive mode.

    V2.0 features:
    - Inheritance with implements:
    - Modular imports with imports:
    - Reusable chunks
    - Advanced selectors and weights

    Examples:
        python3 template_cli_typer.py generate
        python3 template_cli_typer.py generate -t portrait.yaml
        python3 template_cli_typer.py generate -t test.yaml -n 10 --dry-run
    """
    try:
        # Load global configuration
        try:
            global_config = load_global_config()
        except Exception as e:
            console.print(f"[red]✗ Error loading config:[/red] {e}")
            console.print("\n[yellow]Run[/yellow] [cyan]sdgen init[/cyan] [yellow]to create configuration.[/yellow]")
            raise typer.Exit(code=1)

        configs_dir = Path(global_config.configs_dir)
        api_url = api_url or global_config.api_url

        # Verify configs directory exists
        if not configs_dir.exists():
            console.print(f"[red]✗ Configs directory not found:[/red] {configs_dir}")
            console.print("\n[yellow]Create the directory or update your .sdgen_config.json[/yellow]")
            raise typer.Exit(code=1)

        # Determine template path
        if template is None:
            # Interactive selection
            if not check_tty():
                console.print("[red]✗ Interactive mode requires a TTY (terminal)[/red]")
                console.print("\n[yellow]Use --template to specify template directly[/yellow]")
                raise typer.Exit(code=1)

            template_path = select_template_interactive(configs_dir)
        else:
            template_path = template

            # If relative path, try resolving relative to configs_dir first
            if not template_path.is_absolute():
                configs_dir_path = configs_dir / template_path
                if configs_dir_path.exists():
                    template_path = configs_dir_path
                else:
                    template_path = Path.cwd() / template_path

            if not template_path.exists():
                console.print(f"[red]✗ Template file not found:[/red] {template_path}")
                raise typer.Exit(code=1)

        # Processing header
        console.print(Panel(
            f"[bold]Template:[/bold] {template_path.name}",
            title="Processing Template (V2.0)",
            border_style="cyan"
        ))

        _generate(
            template_path=template_path,
            global_config=global_config,
            count=count,
            api_url=api_url,
            dry_run=dry_run,
            console=console
        )

    except typer.Exit:
        raise
    except KeyboardInterrupt:
        console.print("\n[red]✗ Interrupted by user[/red]")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"\n[red]✗ Unexpected error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command(name="list")
def list_templates(
    configs_dir: Optional[Path] = typer.Option(
        None,
        "--configs-dir",
        help="Configs directory (overrides global config)",
    ),
):
    """
    List available YAML templates with rich formatting.

    Examples:
        python3 template_cli_typer.py list
        python3 template_cli_typer.py list --configs-dir /path/to/configs
    """
    try:
        if configs_dir is None:
            global_config = load_global_config()
            configs_dir = Path(global_config.configs_dir)

        templates = find_yaml_templates(configs_dir)

        if not templates:
            console.print(f"[yellow]No templates found in {configs_dir}[/yellow]")
            raise typer.Exit(code=0)

        # Rich table output
        table = Table(title=f"Available Templates ({len(templates)} found)")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Name", style="green")
        table.add_column("Path", style="blue")

        for idx, template_path in enumerate(templates, 1):
            try:
                from templating.orchestrator import V2Pipeline
                pipeline = V2Pipeline()
                config = pipeline.load(str(template_path))
                name = config.name
            except Exception:
                name = template_path.stem

            rel_path = str(template_path.relative_to(configs_dir))
            table.add_row(str(idx), name, rel_path)

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗ Error listing templates:[/red] {e}")
        raise typer.Exit(code=1)


@app.command(name="init")
def init_config(
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Overwrite existing configuration",
    ),
):
    """
    Initialize global configuration file interactively.

    Examples:
        python3 template_cli_typer.py init
        python3 template_cli_typer.py init --force
    """
    try:
        console.print("[cyan]Initializing global configuration...[/cyan]\n")
        config = ensure_global_config(interactive=True, force_create=force)
        console.print("[green]✓ Global configuration initialized[/green]")
        console.print(f"\n[cyan]Config file:[/cyan] {config.config_path}")
    except Exception as e:
        console.print(f"[red]✗ Failed to initialize config:[/red] {e}")
        raise typer.Exit(code=1)


@app.command(name="validate")
def validate_template(
    template: Path = typer.Argument(
        ...,
        help="Path to template file to validate",
        exists=True,
    ),
):
    """
    Validate a YAML template file using V2.0 Template System.

    Checks syntax, required fields, and import files.

    Examples:
        python3 template_cli_typer.py validate portrait.yaml
        python3 template_cli_typer.py validate path/to/config.prompt.yaml
    """
    try:
        console.print(f"[cyan]Validating template (V2.0):[/cyan] {template}\n")

        from templating.orchestrator import V2Pipeline

        pipeline = V2Pipeline()
        config = pipeline.load(str(template))

        console.print(f"[green]✓ Template is valid (V2.0):[/green] {config.name}\n")

        # Show V2 summary
        table = Table(title="Template Summary (V2.0)", show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Name", config.name)
        table.add_row("Type", config.type)
        table.add_row("Version", config.version)

        if config.implements:
            table.add_row("Implements", config.implements)

        if config.template:
            template_preview = config.template[:60] + "..." if len(config.template) > 60 else config.template
            table.add_row("Template", template_preview)

        if hasattr(config, 'imports') and config.imports:
            table.add_row("Imports", str(len(config.imports)))

        if hasattr(config, 'chunks') and config.chunks:
            table.add_row("Chunks", str(len(config.chunks)))

        if hasattr(config, 'parameters') and config.parameters:
            param_keys = ', '.join(list(config.parameters.keys())[:5])
            if len(config.parameters) > 5:
                param_keys += f", ... ({len(config.parameters)} total)"
            table.add_row("Parameters", param_keys)

        console.print(table)

        # Validate import files exist
        console.print(f"\n[cyan]Checking import files:[/cyan]")
        all_files_exist = True

        if hasattr(config, 'imports') and config.imports:
            base_path = template.parent
            for key, file_path in config.imports.items():
                import_path = base_path / file_path
                if import_path.exists():
                    console.print(f"  [green]✓[/green] {key}: {file_path}")
                else:
                    console.print(f"  [red]✗[/red] {key}: {file_path} [yellow](not found)[/yellow]")
                    all_files_exist = False
        else:
            console.print("  [dim]No import files defined[/dim]")

        if all_files_exist:
            console.print("\n[green]✓ All validation checks passed[/green]")
        else:
            console.print("\n[yellow]⚠ Some import files are missing[/yellow]")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"\n[red]✗ Template validation failed:[/red] {e}")
        raise typer.Exit(code=1)


# API introspection commands
@api_app.command(name="samplers")
def list_samplers(
    api_url: Optional[str] = typer.Option(
        None,
        "--api-url",
        help="Override API URL from global config",
    ),
):
    """List available samplers from SD WebUI."""
    try:
        from api import SDAPIClient

        if api_url is None:
            global_config = load_global_config()
            api_url = global_config.api_url

        api_client = SDAPIClient(api_url=api_url)

        console.print(f"[cyan]Connecting to SD API:[/cyan] {api_url}")
        if not api_client.test_connection():
            console.print("[red]✗ Failed to connect to SD API[/red]")
            raise typer.Exit(code=1)
        console.print("[green]✓ Connected[/green]\n")

        samplers = api_client.get_samplers()

        table = Table(title=f"Available Samplers ({len(samplers)} found)")
        table.add_column("Name", style="green")
        table.add_column("Aliases", style="blue")

        for sampler in samplers:
            name = sampler.get('name', 'Unknown')
            aliases = sampler.get('aliases', [])
            alias_str = ', '.join(aliases) if aliases else "—"
            table.add_row(name, alias_str)

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(code=1)


@api_app.command(name="schedulers")
def list_schedulers(
    api_url: Optional[str] = typer.Option(
        None,
        "--api-url",
        help="Override API URL from global config",
    ),
):
    """List available schedulers from SD WebUI."""
    try:
        from api import SDAPIClient

        if api_url is None:
            global_config = load_global_config()
            api_url = global_config.api_url

        api_client = SDAPIClient(api_url=api_url)

        console.print(f"[cyan]Connecting to SD API:[/cyan] {api_url}")
        if not api_client.test_connection():
            console.print("[red]✗ Failed to connect to SD API[/red]")
            raise typer.Exit(code=1)
        console.print("[green]✓ Connected[/green]\n")

        schedulers = api_client.get_schedulers()

        table = Table(title=f"Available Schedulers ({len(schedulers)} found)")
        table.add_column("Name", style="green")
        table.add_column("Label", style="blue")

        for scheduler in schedulers:
            name = scheduler.get('name', 'Unknown')
            label = scheduler.get('label', name)
            table.add_row(name, label)

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(code=1)


@api_app.command(name="models")
def list_models(
    api_url: Optional[str] = typer.Option(
        None,
        "--api-url",
        help="Override API URL from global config",
    ),
):
    """List available SD models/checkpoints."""
    try:
        from api import SDAPIClient

        if api_url is None:
            global_config = load_global_config()
            api_url = global_config.api_url

        api_client = SDAPIClient(api_url=api_url)

        console.print(f"[cyan]Connecting to SD API:[/cyan] {api_url}")
        if not api_client.test_connection():
            console.print("[red]✗ Failed to connect to SD API[/red]")
            raise typer.Exit(code=1)
        console.print("[green]✓ Connected[/green]\n")

        models = api_client.get_sd_models()

        table = Table(title=f"Available SD Models ({len(models)} found)")
        table.add_column("Model Name", style="green")
        table.add_column("Hash", style="blue")

        for model in models:
            model_name = model.get('model_name', 'Unknown')
            hash_val = model.get('hash', '—')
            table.add_row(model_name, hash_val)

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(code=1)


@api_app.command(name="upscalers")
def list_upscalers(
    api_url: Optional[str] = typer.Option(
        None,
        "--api-url",
        help="Override API URL from global config",
    ),
):
    """List available upscalers (for Hires Fix)."""
    try:
        from api import SDAPIClient

        if api_url is None:
            global_config = load_global_config()
            api_url = global_config.api_url

        api_client = SDAPIClient(api_url=api_url)

        console.print(f"[cyan]Connecting to SD API:[/cyan] {api_url}")
        if not api_client.test_connection():
            console.print("[red]✗ Failed to connect to SD API[/red]")
            raise typer.Exit(code=1)
        console.print("[green]✓ Connected[/green]\n")

        upscalers = api_client.get_upscalers()

        table = Table(title=f"Available Upscalers ({len(upscalers)} found)")
        table.add_column("Name", style="green")
        table.add_column("Scale", style="blue")

        for upscaler in upscalers:
            name = upscaler.get('name', 'Unknown')
            scale = upscaler.get('scale', 'N/A')
            table.add_row(name, f"{scale}x")

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(code=1)


@api_app.command(name="model-info")
def show_model_info(
    api_url: Optional[str] = typer.Option(
        None,
        "--api-url",
        help="Override API URL from global config",
    ),
):
    """Show currently loaded model information."""
    try:
        from api import SDAPIClient

        if api_url is None:
            global_config = load_global_config()
            api_url = global_config.api_url

        api_client = SDAPIClient(api_url=api_url)

        console.print(f"[cyan]Connecting to SD API:[/cyan] {api_url}")
        if not api_client.test_connection():
            console.print("[red]✗ Failed to connect to SD API[/red]")
            raise typer.Exit(code=1)
        console.print("[green]✓ Connected[/green]\n")

        info = api_client.get_model_info()

        table = Table(title="Current Model Information", show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Checkpoint", info.get('checkpoint', 'unknown'))
        table.add_row("VAE", info.get('vae', 'auto'))
        table.add_row("CLIP Skip", str(info.get('clip_skip', 1)))

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
