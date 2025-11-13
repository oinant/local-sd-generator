"""ManifestManager - manages manifest lifecycle (create, update, finalize)."""

import json
from pathlib import Path
from typing import Optional

from .session_event_collector import SessionEventCollector
from .event_types import EventType


class ManifestManager:
    """Manages manifest.json lifecycle during generation.

    This class handles:
    - Manifest initialization with 'ongoing' status
    - Incremental updates (adding image entries)
    - Status finalization (ongoing → completed/aborted)

    The manager uses a simple FSM for status:
    - ongoing: Generation in progress
    - completed: Generation finished successfully
    - aborted: Generation interrupted or failed

    Example:
        >>> manager = ManifestManager(manifest_path, events)
        >>> manager.initialize(snapshot)
        >>> manager.update_incremental(0, "image_001.png", prompt_dict, api_response)
        >>> manager.finalize(status="completed")
    """

    def __init__(
        self,
        manifest_path: Path,
        events: SessionEventCollector
    ):
        """Initialize manifest manager.

        Args:
            manifest_path: Path to manifest.json file
            events: Event collector for output management
        """
        self.manifest_path = manifest_path
        self.events = events

    def initialize(self, snapshot: dict) -> None:
        """Create initial manifest with 'ongoing' status.

        This creates a new manifest.json file with:
        - snapshot: Complete generation config snapshot
        - images: Empty list (will be filled incrementally)
        - status: "ongoing" (FSM initial state)

        Args:
            snapshot: Manifest snapshot from ManifestBuilder
        """
        manifest = {
            "snapshot": snapshot,
            "images": [],
            "status": "ongoing"
        }

        # Write manifest
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        # Emit event
        self.events.emit(
            EventType.MANIFEST_CREATED,
            {"manifest_path": str(self.manifest_path)}
        )

    def update_incremental(
        self,
        idx: int,
        filename: str,
        prompt_dict: dict,
        api_response: Optional[dict]
    ) -> None:
        """Add new image entry to manifest.

        This method:
        1. Reads current manifest
        2. Extracts real seed from API response (if available)
        3. Adds new image entry
        4. Writes updated manifest

        Args:
            idx: Image index in prompts list
            filename: Generated image filename
            prompt_dict: Prompt dictionary with seed, variations, etc.
            api_response: Optional API response (contains real seed in 'info')
        """
        # Read current manifest (with error recovery)
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except Exception:
            # Manifest corrupted or missing - recreate minimal structure
            manifest = {
                "snapshot": {},  # Lost snapshot, but we can continue
                "images": [],
                "status": "ongoing"
            }

        # Extract real seed from API response
        real_seed = prompt_dict.get('seed', -1)

        if api_response and 'info' in api_response:
            try:
                # Parse 'info' JSON string to get real seed
                info = json.loads(api_response['info'])
                real_seed = info.get('seed', real_seed)
            except Exception:
                # Fallback to original seed if parsing fails
                pass

        # Build image entry
        image_entry = {
            "filename": filename,
            "seed": real_seed,
            "prompt": prompt_dict.get('prompt', ''),
            "negative_prompt": prompt_dict.get('negative_prompt', ''),
            "applied_variations": prompt_dict.get('variations', {})
        }

        # Add to manifest
        manifest["images"].append(image_entry)

        # Write updated manifest
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    def finalize(self, status: str = "completed") -> None:
        """Update manifest status (completed/aborted).

        This is the final step in manifest lifecycle.

        Args:
            status: Final status ("completed" or "aborted")
        """
        try:
            # Read current manifest
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            # Update status
            manifest["status"] = status

            # Write updated manifest
            with open(self.manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)

            # Emit event
            self.events.emit(
                EventType.MANIFEST_FINALIZED,
                {"status": status}
            )

        except Exception as e:
            # Manifest missing or corrupted
            self.events.emit(
                EventType.WARNING,
                {"message": f"Could not finalize manifest: {e}"}
            )

    def get_status(self) -> Optional[str]:
        """Get current manifest status.

        Returns:
            Current status ("ongoing", "completed", "aborted") or None if error
        """
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            return manifest.get("status")
        except Exception:
            return None
