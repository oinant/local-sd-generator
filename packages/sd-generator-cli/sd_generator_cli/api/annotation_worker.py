"""
Background annotation worker using thread-safe queue.

Provides real-time image annotation as they are generated,
without blocking the main generation loop.
"""

import threading
import queue
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple
from .annotator import ImageAnnotator


class AnnotationWorker:
    """
    Background worker thread for annotating images in real-time.

    Uses a thread-safe queue to receive annotation jobs as images are generated,
    and processes them in the background without blocking the main thread.
    """

    def __init__(
        self,
        keys: Optional[List[str]] = None,
        position: str = "bottom-left",
        font_size: int = 16,
        background_alpha: int = 180,
        text_color: str = "white",
        padding: int = 10,
        margin: int = 20
    ):
        """
        Initialize annotation worker.

        Args:
            keys: List of variation keys to display (None = all)
            position: Text position on image
            font_size: Font size in pixels
            background_alpha: Background transparency (0-255)
            text_color: Text color name
            padding: Padding around text
            margin: Margin from image edges
        """
        self.keys = keys
        self.position = position
        self.font_size = font_size
        self.background_alpha = background_alpha
        self.text_color = text_color
        self.padding = padding
        self.margin = margin

        # Thread-safe queue for annotation jobs
        self._queue: "queue.Queue[Optional[Tuple[Path, Dict[str, str]]]]" = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._annotator: Optional[ImageAnnotator] = None

    def start(self) -> None:
        """Start the background worker thread."""
        if self._worker_thread is not None:
            raise RuntimeError("Worker already started")

        # Initialize annotator (lazy init to avoid Pillow import if disabled)
        try:
            # Parse text color
            color_map = {
                'white': (255, 255, 255),
                'black': (0, 0, 0),
                'red': (255, 0, 0),
                'green': (0, 255, 0),
                'blue': (0, 0, 255),
                'yellow': (255, 255, 0),
            }
            text_color_rgb = color_map.get(self.text_color.lower(), (255, 255, 255))

            self._annotator = ImageAnnotator(
                position=self.position,
                font_size=self.font_size,
                text_color=text_color_rgb,
                background_color=(0, 0, 0, self.background_alpha),
                padding=self.padding,
                margin=self.margin
            )

            # Start worker thread
            self._worker_thread = threading.Thread(
                target=self._worker_loop,
                daemon=True,  # Dies when main thread exits
                name="AnnotationWorker"
            )
            self._worker_thread.start()

        except ImportError:
            # Pillow not installed, worker won't start
            raise

    def submit(self, image_path: Path, variations: Dict[str, str]) -> None:
        """
        Submit an image for annotation.

        Args:
            image_path: Path to image file
            variations: Dictionary of variation key-value pairs
        """
        if self._worker_thread is None:
            raise RuntimeError("Worker not started. Call start() first.")

        self._queue.put((image_path, variations))

    def stop(self, timeout: float = 30.0) -> None:
        """
        Stop the worker thread and wait for pending jobs.

        Args:
            timeout: Maximum time to wait for queue to drain (seconds)
        """
        if self._worker_thread is None:
            return  # Already stopped or never started

        # Signal stop
        self._stop_event.set()

        # Send poison pill to unblock worker
        self._queue.put(None)

        # Wait for thread to finish
        self._worker_thread.join(timeout=timeout)
        self._worker_thread = None

    def _worker_loop(self) -> None:
        """
        Main worker loop (runs in background thread).

        Processes annotation jobs from the queue until stopped.
        """
        while not self._stop_event.is_set():
            try:
                # Get next job (blocking, timeout to check stop_event)
                job = self._queue.get(timeout=1.0)

                # Check for poison pill (stop signal)
                if job is None:
                    break

                # Unpack job
                image_path, variations = job

                # Annotate the image
                try:
                    self._annotator.annotate_image(  # type: ignore
                        image_path=image_path,
                        variations=variations,
                        keys=self.keys,
                        output_path=None  # Overwrite original
                    )
                except Exception as e:
                    # Log error but continue processing queue
                    print(f"Warning: Failed to annotate {image_path}: {e}")

                # Mark job as done
                self._queue.task_done()

            except queue.Empty:
                # Timeout, check stop_event and continue
                continue

    def wait_until_done(self, timeout: Optional[float] = None) -> None:
        """
        Wait until all pending annotation jobs are complete.

        Args:
            timeout: Maximum time to wait (seconds), None = wait forever
        """
        self._queue.join()  # Blocks until all tasks are done

    @property
    def pending_count(self) -> int:
        """Get number of pending annotation jobs."""
        return self._queue.qsize()


def create_annotation_worker_from_config(
    annotations_config: Any  # AnnotationsConfig
) -> Optional[AnnotationWorker]:
    """
    Create and start AnnotationWorker from template config.

    Args:
        annotations_config: AnnotationsConfig from template

    Returns:
        Started AnnotationWorker or None if disabled/Pillow missing
    """
    if not annotations_config or not annotations_config.enabled:
        return None

    try:
        worker = AnnotationWorker(
            keys=annotations_config.keys if annotations_config.keys else None,
            position=annotations_config.position,
            font_size=annotations_config.font_size,
            background_alpha=annotations_config.background_alpha,
            text_color=annotations_config.text_color,
            padding=annotations_config.padding,
            margin=annotations_config.margin
        )
        worker.start()
        return worker

    except ImportError:
        # Pillow not installed
        print("⚠ Pillow not installed, skipping annotations")
        print("  Install with: pip install Pillow")
        return None
