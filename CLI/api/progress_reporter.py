"""
Console progress reporting for batch generation

Handles all console output and progress tracking.
"""

import time
from pathlib import Path
from typing import Optional, Callable


class ProgressReporter:
    """
    Reports generation progress to console

    Responsibility: Console output and progress tracking
    - Print generation start/success messages
    - Display progress counters (X/Y)
    - Calculate and display time estimates
    - Print final summary

    Does NOT handle:
    - API communication
    - File I/O
    - Actual generation logic
    """

    def __init__(self,
                 total_images: int,
                 output_dir: Optional[Path] = None,
                 verbose: bool = True):
        """
        Initialize progress reporter

        Args:
            total_images: Total number of images to generate
            output_dir: Output directory (for display)
            verbose: If False, suppresses all output
        """
        self.total = total_images
        self.output_dir = output_dir
        self.verbose = verbose
        self.start_time: Optional[float] = None
        self.completed_count = 0
        self.success_count = 0

    def report_batch_start(self):
        """Print batch generation start message"""
        if not self.verbose:
            return

        print(f"🚀 Début de génération de {self.total} images")
        if self.output_dir:
            print(f"📁 Dossier de sortie: {self.output_dir}")
        print("-" * 50)

        self.start_time = time.time()

    def report_image_start(self, index: int, filename: str):
        """
        Print image generation start message

        Args:
            index: Current image index (1-based)
            filename: Image filename
        """
        if not self.verbose:
            return

        print(f"🎨 [{index}/{self.total}] Génération: {filename}")

    def report_image_success(self, filename: str):
        """
        Print image success message

        Args:
            filename: Saved image filename
        """
        if not self.verbose:
            return

        self.success_count += 1
        print(f"✅ Image sauvée: {filename}")

    def report_image_failure(self, filename: str, error: str):
        """
        Print image failure message

        Args:
            filename: Failed image filename
            error: Error message
        """
        if not self.verbose:
            return

        print(f"❌ Erreur génération {filename}: {error}")

    def report_progress_update(self, index: int, update_interval: int = 10):
        """
        Print time remaining estimate

        Args:
            index: Current image index (1-based)
            update_interval: Print estimate every N images (default: 10)
        """
        if not self.verbose or self.start_time is None:
            return

        if index % update_interval == 0:
            elapsed = time.time() - self.start_time
            avg_time = elapsed / index
            remaining = (self.total - index) * avg_time
            print(f"⏱️  Temps restant estimé: {remaining / 60:.1f} minutes\n")

    def report_batch_complete(self):
        """Print final batch summary"""
        if not self.verbose or self.start_time is None:
            return

        total_time = time.time() - self.start_time
        print("-" * 50)
        print(f"✅ Génération terminée!")
        print(f"📊 Succès: {self.success_count}/{self.total} images")
        print(f"⏱️  Temps total: {total_time / 60:.1f} minutes")
        if self.output_dir:
            print(f"📁 Images dans: {self.output_dir}")

    def get_summary(self) -> dict:
        """
        Get progress summary as dictionary

        Returns:
            dict: Summary with success/total counts and elapsed time
        """
        elapsed = 0.0
        if self.start_time is not None:
            elapsed = time.time() - self.start_time

        return {
            "total": self.total,
            "success": self.success_count,
            "failed": self.total - self.success_count,
            "elapsed_seconds": elapsed,
            "elapsed_minutes": elapsed / 60
        }

    def set_callback(self,
                    on_start: Optional[Callable[[int, str], None]] = None,
                    on_success: Optional[Callable[[str], None]] = None,
                    on_failure: Optional[Callable[[str, str], None]] = None):
        """
        Set custom callbacks for events (for testing or custom UI)

        Args:
            on_start: Called on image start (index, filename)
            on_success: Called on image success (filename)
            on_failure: Called on image failure (filename, error)
        """
        self._on_start_callback = on_start
        self._on_success_callback = on_success
        self._on_failure_callback = on_failure

    def increment_completed(self):
        """Increment completed counter"""
        self.completed_count += 1

    def increment_success(self):
        """Increment success counter"""
        self.success_count += 1


class SilentProgressReporter(ProgressReporter):
    """
    Progress reporter that outputs nothing

    Useful for tests or when you want to suppress all output.
    """

    def __init__(self, total_images: int):
        """
        Initialize silent reporter

        Args:
            total_images: Total number of images
        """
        super().__init__(total_images, verbose=False)
