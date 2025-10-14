"""
Manifest generation and writing for V2 snapshot system

This module handles the creation and writing of manifest.json files
with complete snapshot information for reproducibility.
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Any
from pathlib import Path


@dataclass
class ManifestImage:
    """Represents a single generated image in the manifest"""
    filename: str
    seed: int
    prompt: str
    negative_prompt: str
    applied_variations: Dict[str, str]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "filename": self.filename,
            "seed": self.seed,
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "applied_variations": self.applied_variations
        }


class ManifestWriter:
    """
    Writes V2 manifests with complete snapshot information

    Responsibilities:
    - Format snapshot and image data
    - Write manifest.json to output directory
    - Ensure proper JSON encoding (UTF-8, indented)
    """

    def __init__(self, output_dir: Path):
        """
        Initialize manifest writer

        Args:
            output_dir: Directory where manifest.json will be written
        """
        self.output_dir = Path(output_dir)

    def write(self, snapshot: dict, images: List[ManifestImage]) -> Path:
        """
        Write complete manifest with snapshot and images

        Args:
            snapshot: Complete snapshot dictionary (version, timestamp, runtime_info, etc.)
            images: List of ManifestImage objects

        Returns:
            Path to written manifest.json file
        """
        manifest = {
            "snapshot": snapshot,
            "images": [img.to_dict() for img in images]
        }

        manifest_path = self.output_dir / "manifest.json"

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return manifest_path

    def write_manifest_dict(self, manifest: dict) -> Path:
        """
        Write manifest from a complete dictionary

        Args:
            manifest: Complete manifest dictionary with 'snapshot' and 'images' keys

        Returns:
            Path to written manifest.json file
        """
        manifest_path = self.output_dir / "manifest.json"

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return manifest_path
