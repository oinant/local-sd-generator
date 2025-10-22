"""ControlNet data models for SD WebUI integration.

This module provides data structures for ControlNet configuration,
following the same pattern as ADetailer integration.
"""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class ControlNetUnit:
    """Single ControlNet unit configuration.

    Represents one ControlNet preprocessor + model combination.
    Can be used standalone or combined with other units.

    Example:
        >>> unit = ControlNetUnit(
        ...     model="control_v11p_sd15_canny",
        ...     module="canny",
        ...     weight=1.0,
        ...     threshold_a=100,
        ...     threshold_b=200
        ... )
    """

    # Required field
    model: str  # e.g., "control_v11p_sd15_canny"

    # Input image (mutually exclusive with module auto-generation)
    image: Optional[str] = None  # Path to control image or base64

    # Preprocessor
    module: str = "none"  # Preprocessor module (e.g., "canny", "depth_midas")

    # Weight and guidance
    weight: float = 1.0  # Unit influence (0.0-2.0)
    guidance_start: float = 0.0  # When to start guidance (0.0-1.0)
    guidance_end: float = 1.0  # When to stop guidance (0.0-1.0)

    # Preprocessor parameters
    processor_res: int = 512  # Preprocessor resolution
    threshold_a: float = 64.0  # Preprocessor param A (e.g., canny low threshold)
    threshold_b: float = 128.0  # Preprocessor param B (e.g., canny high threshold)

    # Control modes
    resize_mode: str = "Crop and Resize"  # "Just Resize", "Crop and Resize", "Resize and Fill"
    control_mode: str = "Balanced"  # "Balanced", "My prompt is more important", "ControlNet is more important"

    # Advanced
    pixel_perfect: bool = False
    low_vram: bool = False
    guess_mode: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to plain dict for JSON serialization (e.g., manifest files).

        Returns:
            Dictionary representation of ControlNet unit configuration.

        Example:
            >>> unit = ControlNetUnit(model="control_v11p_sd15_canny", module="canny")
            >>> config_dict = unit.to_dict()
            >>> config_dict["model"]
            'control_v11p_sd15_canny'
        """
        return {
            "model": self.model,
            "image": self.image,
            "module": self.module,
            "weight": self.weight,
            "guidance_start": self.guidance_start,
            "guidance_end": self.guidance_end,
            "processor_res": self.processor_res,
            "threshold_a": self.threshold_a,
            "threshold_b": self.threshold_b,
            "resize_mode": self.resize_mode,
            "control_mode": self.control_mode,
            "pixel_perfect": self.pixel_perfect,
            "low_vram": self.low_vram,
            "guess_mode": self.guess_mode,
        }

    def to_api_dict(self) -> dict[str, Any]:
        """Convert to SD WebUI ControlNet API format.

        Returns:
            Dictionary matching SD WebUI ControlNet extension API format.

        Example:
            >>> unit = ControlNetUnit(model="control_v11p_sd15_canny", module="canny")
            >>> api_dict = unit.to_api_dict()
            >>> api_dict["enabled"]
            True
            >>> api_dict["model"]
            'control_v11p_sd15_canny'
        """
        return {
            "enabled": True,
            "module": self.module,
            "model": self.model,
            "weight": self.weight,
            "image": self.image,
            "resize_mode": self.resize_mode,
            "low_vram": self.low_vram,
            "processor_res": self.processor_res,
            "threshold_a": self.threshold_a,
            "threshold_b": self.threshold_b,
            "guidance_start": self.guidance_start,
            "guidance_end": self.guidance_end,
            "control_mode": self.control_mode,
            "pixel_perfect": self.pixel_perfect,
            "guessmode": self.guess_mode,
        }


@dataclass
class ControlNetConfig:
    """Container for ControlNet units.

    Manages one or more ControlNet units and converts them to
    SD WebUI API payload format.

    Example:
        >>> unit1 = ControlNetUnit(model="control_v11p_sd15_canny", module="canny")
        >>> unit2 = ControlNetUnit(model="control_v11p_sd15_depth", module="depth_midas")
        >>> config = ControlNetConfig(units=[unit1, unit2])
        >>> payload = config.to_api_dict()
        >>> len(payload["controlnet"]["args"])
        2
    """

    units: list[ControlNetUnit] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to plain dict for JSON serialization (e.g., manifest files).

        Returns:
            Dictionary representation of ControlNet configuration.

        Example:
            >>> unit = ControlNetUnit(model="control_v11p_sd15_canny", module="canny")
            >>> config = ControlNetConfig(units=[unit])
            >>> config_dict = config.to_dict()
            >>> len(config_dict["units"])
            1
        """
        return {
            "units": [unit.to_dict() for unit in self.units]
        }

    def to_api_dict(self) -> Optional[dict[str, Any]]:
        """Convert to alwayson_scripts payload format.

        Returns:
            Dictionary for alwayson_scripts.controlnet field,
            or None if no units configured.

        Example:
            >>> config = ControlNetConfig(units=[])
            >>> config.to_api_dict()
            None

            >>> unit = ControlNetUnit(model="control_v11p_sd15_canny", module="canny")
            >>> config = ControlNetConfig(units=[unit])
            >>> payload = config.to_api_dict()
            >>> "controlnet" in payload
            True
        """
        if not self.units:
            return None

        return {
            "controlnet": {
                "args": [unit.to_api_dict() for unit in self.units]
            }
        }
