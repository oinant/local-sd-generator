"""
Session directory management for image generation

Handles creation of timestamped session directories and session configuration files.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from dataclasses import asdict

from .sdapi_client import GenerationConfig


class SessionManager:
    """
    Manages session directories and configuration files

    Responsibility: Session lifecycle and directory structure
    - Create timestamped session directories
    - Handle dry-run mode directory separation
    - Save session configuration files

    Does NOT handle:
    - Image file I/O
    - API communication
    - Progress reporting
    """

    def __init__(self,
                 base_output_dir: str = "apioutput",
                 session_name: Optional[str] = None,
                 dry_run: bool = False):
        """
        Initialize session manager

        Args:
            base_output_dir: Base directory for all sessions
            session_name: Optional name suffix for session directory
            dry_run: If True, creates sessions in /dryrun subdirectory
        """
        self.base_output_dir = base_output_dir
        self.session_name = session_name
        self.dry_run = dry_run
        self.session_start_time = datetime.now()
        self._output_dir: Optional[Path] = None

    @property
    def output_dir(self) -> Path:
        """
        Get current session directory path

        Creates the directory structure if it doesn't exist yet.

        Returns:
            Path: Absolute path to session directory
        """
        if self._output_dir is None:
            self._output_dir = self._build_session_path()
        return self._output_dir

    def _build_session_path(self) -> Path:
        """
        Build session directory path

        Format: {base_dir}/[dryrun/]{timestamp}[_{session_name}]/

        Returns:
            Path: Session directory path (not yet created)
        """
        timestamp = self.session_start_time.strftime("%Y-%m-%d_%H%M%S")

        if self.session_name:
            session_dir_name = f"{timestamp}_{self.session_name}"
        else:
            session_dir_name = timestamp

        # In dry-run mode, use /dryrun subdirectory
        if self.dry_run:
            base_dir = Path(self.base_output_dir) / "dryrun"
        else:
            base_dir = Path(self.base_output_dir)

        return base_dir / session_dir_name

    def create_session_dir(self) -> Path:
        """
        Create session directory if it doesn't exist

        Returns:
            Path: Created session directory path
        """
        session_path = self.output_dir
        session_path.mkdir(parents=True, exist_ok=True)
        return session_path

    def save_session_config(self,
                           generation_config: GenerationConfig,
                           base_prompt: str = "",
                           negative_prompt: str = "",
                           additional_info: Optional[Dict] = None):
        """
        Save session configuration to text file

        Creates a human-readable session_config.txt file with:
        - Session metadata (date, name, API URL, output dir)
        - Prompts (base prompt, negative prompt)
        - Generation parameters
        - Additional information

        Args:
            generation_config: Generation configuration used
            base_prompt: Base prompt template
            negative_prompt: Negative prompt
            additional_info: Optional dict of additional metadata
        """
        # Ensure directory exists
        self.create_session_dir()

        config_path = self.output_dir / "session_config.txt"

        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("SESSION CONFIGURATION\n")
            f.write("=" * 60 + "\n\n")

            # Session information
            f.write(f"Date de génération: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Nom de session: {self.session_name or 'Non spécifié'}\n")
            f.write(f"Mode: {'Dry-run' if self.dry_run else 'Production'}\n")
            f.write(f"Dossier de sortie: {self.output_dir}\n\n")

            # Prompts
            f.write("-" * 40 + "\n")
            f.write("PROMPTS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Prompt de base:\n{base_prompt}\n\n")
            f.write(f"Prompt négatif:\n{negative_prompt}\n\n")

            # Generation parameters
            f.write("-" * 40 + "\n")
            f.write("PARAMÈTRES DE GÉNÉRATION\n")
            f.write("-" * 40 + "\n")
            config_dict = asdict(generation_config)
            for key, value in config_dict.items():
                f.write(f"{key}: {value}\n")

            # Additional information
            if additional_info:
                f.write("\n" + "-" * 40 + "\n")
                f.write("INFORMATIONS ADDITIONNELLES\n")
                f.write("-" * 40 + "\n")
                for key, value in additional_info.items():
                    f.write(f"{key}: {value}\n")

    def get_session_info(self) -> Dict:
        """
        Get session information as dictionary

        Returns:
            dict: Session metadata
        """
        return {
            "session_name": self.session_name,
            "start_time": self.session_start_time.isoformat(),
            "output_dir": str(self.output_dir),
            "dry_run": self.dry_run,
            "base_output_dir": self.base_output_dir
        }
