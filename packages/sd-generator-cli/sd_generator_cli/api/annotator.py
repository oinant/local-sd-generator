"""
Image annotation module for adding variation metadata overlays.

Adds text annotations to generated images showing which variations were used
(haircut, haircolor, expression, etc.) for easy reference and organization.
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image as PILImageModule, ImageDraw as PILImageDrawModule, ImageFont as PILImageFontModule
    from ..templating.models.config_models import AnnotationsConfig

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore
    ImageFont = None  # type: ignore


class ImageAnnotator:
    """Annotates images with variation metadata text overlays."""

    def __init__(
        self,
        position: str = "bottom-left",
        font_size: int = 16,
        text_color: Tuple[int, int, int] = (255, 255, 255),
        background_color: Tuple[int, int, int, int] = (0, 0, 0, 180),
        padding: int = 10,
        margin: int = 20
    ):
        """
        Initialize annotator.

        Args:
            position: Where to place text (top-left, top-right, bottom-left, bottom-right)
            font_size: Font size in pixels
            text_color: RGB tuple for text
            background_color: RGBA tuple for background (alpha: 0=transparent, 255=opaque)
            padding: Padding around text inside box
            margin: Margin from image edges
        """
        if Image is None:
            raise ImportError(
                "Pillow is required for image annotations. "
                "Install with: pip install Pillow"
            )

        self.position = position
        self.font_size = font_size
        self.text_color = text_color
        self.background_color = background_color
        self.padding = padding
        self.margin = margin

        # Load font
        self.font = self._load_font()

    def _load_font(self):
        """Load a font, falling back to default if needed."""
        try:
            # Try common font locations
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "/System/Library/Fonts/Helvetica.ttc",  # macOS
                "C:\\Windows\\Fonts\\arial.ttf",  # Windows
            ]
            for font_path in font_paths:
                if Path(font_path).exists():
                    return ImageFont.truetype(font_path, self.font_size)

            # Fallback to default
            return ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()

    def annotate_image(
        self,
        image_path: Path,
        variations: Dict[str, str],
        keys: Optional[List[str]] = None,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Annotate a single image with variation metadata.

        Args:
            image_path: Path to image file
            variations: Dictionary of variation key-value pairs
            keys: List of keys to display (None = all keys)
            output_path: Where to save (None = overwrite original)

        Returns:
            Path to annotated image
        """
        # Load image
        img: Any = Image.open(image_path)  # type: ignore

        # Convert to RGBA for transparency
        if img.mode != 'RGBA':
            img = img.convert('RGBA')  # type: ignore

        # Filter variations by keys
        if keys:
            display_variations = {k: v for k, v in variations.items() if k in keys}
        else:
            display_variations = variations

        if not display_variations:
            return image_path

        # Build text lines
        lines = [f"{key}: {value}" for key, value in display_variations.items()]
        text = "\n".join(lines)

        # Create overlay
        overlay: Any = Image.new('RGBA', img.size, (0, 0, 0, 0))  # type: ignore
        draw: Any = ImageDraw.Draw(overlay)  # type: ignore

        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        box_width = text_width + 2 * self.padding
        box_height = text_height + 2 * self.padding

        # Calculate position
        if self.position == "top-left":
            x, y = self.margin, self.margin
        elif self.position == "top-right":
            x = img.width - box_width - self.margin
            y = self.margin
        elif self.position == "bottom-left":
            x = self.margin
            y = img.height - box_height - self.margin
        else:  # bottom-right
            x = img.width - box_width - self.margin
            y = img.height - box_height - self.margin

        # Draw background box
        draw.rectangle(
            [x, y, x + box_width, y + box_height],
            fill=self.background_color
        )

        # Draw text
        draw.text(
            (x + self.padding, y + self.padding),
            text,
            fill=self.text_color,
            font=self.font
        )

        # Composite overlay
        img = Image.alpha_composite(img, overlay)  # type: ignore

        # Convert back to RGB for JPEG
        if output_path and output_path.suffix.lower() in ['.jpg', '.jpeg']:
            img = img.convert('RGB')  # type: ignore

        # Save
        save_path = output_path or image_path
        img.save(save_path)

        return save_path


def annotate_session(
    session_dir: Path,
    keys: Optional[List[str]] = None,
    position: str = "bottom-left",
    font_size: int = 16,
    background_alpha: int = 180,
    text_color: str = "white",
    padding: int = 10,
    margin: int = 20,
    overwrite: bool = True
) -> int:
    """
    Annotate all images in a session directory.

    Args:
        session_dir: Path to session directory with manifest.json
        keys: List of variation keys to display (None = all)
        position: Text position
        font_size: Font size in pixels
        background_alpha: Background transparency (0-255)
        text_color: Text color name
        padding: Padding around text
        margin: Margin from edges
        overwrite: Overwrite originals (True) or create _annotated copies (False)

    Returns:
        Number of images annotated
    """
    # Check manifest exists
    manifest_path = session_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"Warning: No manifest.json found in {session_dir}")
        return 0

    # Load manifest
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    images = manifest.get('images', [])
    if not images:
        return 0

    # Parse text color
    color_map = {
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
    }
    text_color_rgb = color_map.get(text_color.lower(), (255, 255, 255))

    # Create annotator
    annotator = ImageAnnotator(
        position=position,
        font_size=font_size,
        text_color=text_color_rgb,
        background_color=(0, 0, 0, background_alpha),
        padding=padding,
        margin=margin
    )

    # Annotate each image
    annotated_count = 0
    for img_data in images:
        filename = img_data['filename']
        variations = img_data['applied_variations']

        image_path = session_dir / filename
        if not image_path.exists():
            continue

        # Determine output path
        if overwrite:
            output_path = image_path
        else:
            stem = image_path.stem
            suffix = image_path.suffix
            output_path = session_dir / f"{stem}_annotated{suffix}"

        # Annotate
        annotator.annotate_image(image_path, variations, keys, output_path)
        annotated_count += 1

    return annotated_count


def annotate_session_from_config(
    session_dir: Path,
    annotations_config: Any  # AnnotationsConfig from config_models
) -> int:
    """
    Annotate session using AnnotationsConfig from template.

    Args:
        session_dir: Path to session directory
        annotations_config: AnnotationsConfig instance from template

    Returns:
        Number of images annotated
    """
    if not annotations_config.enabled:
        return 0

    return annotate_session(
        session_dir=session_dir,
        keys=annotations_config.keys if annotations_config.keys else None,
        position=annotations_config.position,
        font_size=annotations_config.font_size,
        background_alpha=annotations_config.background_alpha,
        text_color=annotations_config.text_color,
        padding=annotations_config.padding,
        margin=annotations_config.margin,
        overwrite=True  # Always overwrite when integrated
    )
