#!/usr/bin/env python3
"""
Image Annotation Tool for SD Generator Sessions

Reads a session directory with manifest.json and adds text annotations
to images showing the variations used (haircut, haircolor, expression, etc.).

Usage:
    python3 annotate_images.py <session_dir> [options]

Examples:
    # Annotate with all variations
    python3 annotate_images.py apioutput/2025-01-20_143025

    # Annotate with specific keys only
    python3 annotate_images.py apioutput/2025-01-20_143025 --keys HairCut,HairColor

    # Custom position and style
    python3 annotate_images.py apioutput/2025-01-20_143025 \\
        --position bottom-right \\
        --font-size 20 \\
        --background-alpha 200
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow is not installed.")
    print("Install with: pip install Pillow")
    exit(1)


class ImageAnnotator:
    """Annotates images with variation metadata."""

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
            position: Where to place the text (top-left, top-right, bottom-left, bottom-right)
            font_size: Font size in pixels
            text_color: RGB tuple for text color
            background_color: RGBA tuple for background (last value is alpha)
            padding: Padding around text inside the box
            margin: Margin from image edges
        """
        self.position = position
        self.font_size = font_size
        self.text_color = text_color
        self.background_color = background_color
        self.padding = padding
        self.margin = margin

        # Try to load a nice font, fallback to default
        try:
            # Try common font locations
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "/System/Library/Fonts/Helvetica.ttc",  # macOS
                "C:\\Windows\\Fonts\\arial.ttf",  # Windows
            ]
            self.font = None
            for font_path in font_paths:
                if Path(font_path).exists():
                    self.font = ImageFont.truetype(font_path, font_size)
                    break

            if self.font is None:
                self.font = ImageFont.load_default()
        except Exception:
            self.font = ImageFont.load_default()

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
            output_path: Where to save annotated image (None = overwrite original)

        Returns:
            Path to annotated image
        """
        # Load image
        img = Image.open(image_path)

        # Convert to RGBA if needed (for transparency)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Filter variations by keys
        if keys:
            display_variations = {k: v for k, v in variations.items() if k in keys}
        else:
            display_variations = variations

        if not display_variations:
            print(f"  Warning: No variations to display for {image_path.name}")
            return image_path

        # Build text lines
        lines = []
        for key, value in display_variations.items():
            lines.append(f"{key}: {value}")

        # Create overlay for text
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Calculate text box size
        text = "\n".join(lines)

        # Get text bounding box using textbbox
        bbox = draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        box_width = text_width + 2 * self.padding
        box_height = text_height + 2 * self.padding

        # Calculate position
        if self.position == "top-left":
            x = self.margin
            y = self.margin
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

        # Composite overlay onto image
        img = Image.alpha_composite(img, overlay)

        # Convert back to RGB for saving as JPEG/PNG
        if output_path and output_path.suffix.lower() in ['.jpg', '.jpeg']:
            img = img.convert('RGB')

        # Save
        save_path = output_path or image_path
        img.save(save_path)

        return save_path


def annotate_session(
    session_dir: Path,
    keys: Optional[List[str]] = None,
    output_suffix: str = "_annotated",
    **annotator_kwargs
) -> int:
    """
    Annotate all images in a session directory.

    Args:
        session_dir: Path to session directory containing manifest.json
        keys: List of variation keys to display (None = all)
        output_suffix: Suffix to add to annotated files (empty = overwrite)
        **annotator_kwargs: Arguments passed to ImageAnnotator

    Returns:
        Number of images annotated
    """
    # Check session directory exists
    if not session_dir.exists():
        print(f"ERROR: Session directory not found: {session_dir}")
        return 0

    # Load manifest
    manifest_path = session_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: manifest.json not found in {session_dir}")
        return 0

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    images = manifest.get('images', [])
    if not images:
        print(f"ERROR: No images found in manifest")
        return 0

    print(f"Found {len(images)} images in manifest")

    # Create annotator
    annotator = ImageAnnotator(**annotator_kwargs)

    # Annotate each image
    annotated_count = 0
    for img_data in images:
        filename = img_data['filename']
        variations = img_data['applied_variations']

        image_path = session_dir / filename

        if not image_path.exists():
            print(f"  Warning: Image not found: {filename}")
            continue

        # Determine output path
        if output_suffix:
            stem = image_path.stem
            suffix = image_path.suffix
            output_path = session_dir / f"{stem}{output_suffix}{suffix}"
        else:
            output_path = image_path

        # Annotate
        print(f"  Annotating: {filename}")
        annotator.annotate_image(image_path, variations, keys, output_path)
        annotated_count += 1

    return annotated_count


def main():
    parser = argparse.ArgumentParser(
        description="Annotate SD Generator session images with variation metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Annotate with all variations
  python3 annotate_images.py apioutput/2025-01-20_143025

  # Annotate with specific keys only
  python3 annotate_images.py apioutput/2025-01-20_143025 --keys HairCut,HairColor

  # Custom position and style
  python3 annotate_images.py apioutput/2025-01-20_143025 \\
      --position bottom-right \\
      --font-size 20 \\
      --background-alpha 200

  # Overwrite original images (no suffix)
  python3 annotate_images.py apioutput/2025-01-20_143025 --overwrite
        """
    )

    parser.add_argument(
        'session_dir',
        type=Path,
        help='Path to session directory containing manifest.json'
    )
    parser.add_argument(
        '--keys',
        type=str,
        help='Comma-separated list of variation keys to display (e.g., HairCut,HairColor)'
    )
    parser.add_argument(
        '--position',
        type=str,
        default='bottom-left',
        choices=['top-left', 'top-right', 'bottom-left', 'bottom-right'],
        help='Position of the annotation box (default: bottom-left)'
    )
    parser.add_argument(
        '--font-size',
        type=int,
        default=16,
        help='Font size in pixels (default: 16)'
    )
    parser.add_argument(
        '--background-alpha',
        type=int,
        default=180,
        help='Background transparency 0-255 (default: 180)'
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite original images instead of creating _annotated copies'
    )

    args = parser.parse_args()

    # Parse keys
    keys = None
    if args.keys:
        keys = [k.strip() for k in args.keys.split(',')]
        print(f"Displaying keys: {', '.join(keys)}")

    # Determine output suffix
    output_suffix = "" if args.overwrite else "_annotated"

    # Annotate session
    print(f"\nAnnotating session: {args.session_dir}")
    print(f"Position: {args.position}")
    print(f"Font size: {args.font_size}px")
    print(f"Background alpha: {args.background_alpha}/255")
    print()

    count = annotate_session(
        session_dir=args.session_dir,
        keys=keys,
        output_suffix=output_suffix,
        position=args.position,
        font_size=args.font_size,
        background_color=(0, 0, 0, args.background_alpha)
    )

    print(f"\n✓ Annotated {count} images")

    if not args.overwrite:
        print(f"Annotated images saved with suffix '_annotated'")


if __name__ == '__main__':
    main()
