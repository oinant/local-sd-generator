"""
Data models for Template System V2.0.

This module defines the core configuration models for templates, chunks, and prompts.
Each model corresponds to a specific YAML file type in the V2.0 system.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from sd_generator_cli.templating.models.theme_models import ThemeConfigBlock


@dataclass
class TemplateConfig:
    """
    Configuration for a .template.yaml file.

    A template defines base parameters and structure for prompt generation.
    It can be inherited by other templates or prompts using implements:.

    Required fields: version, name, template
    Optional fields: implements, parameters, imports, chunks, negative_prompt, output, themes

    Themes Extension:
        themes: Dict mapping theme names to theme file paths (ex: {"cyberpunk": "./themes/cyberpunk/theme.yaml"})
        style_sensitive: If True, template supports style-based variants
        style_sensitive_placeholders: List of placeholders that vary by style

    Note: All templates/prompts are themable by default. Use --theme or --theme-file to apply themes.
    """
    version: str
    name: str
    template: str
    source_file: Path
    implements: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    imports: Dict[str, Any] = field(default_factory=dict)
    chunks: Dict[str, str] = field(default_factory=dict)  # {chunk_name: chunk_file_path}
    negative_prompt: str = ''
    output: Optional['OutputConfig'] = None
    # Themes Extension (presence of themes block indicates themable template)
    themes: Optional['ThemeConfigBlock'] = None
    style_sensitive: bool = False
    style_sensitive_placeholders: List[str] = field(default_factory=list)


@dataclass
class ChunkConfig:
    """
    Configuration for a .chunk.yaml file.

    A chunk is a reusable template block (e.g., character, scene, style).
    It can define default values and be injected into templates using @Chunk syntax.

    Required fields: version, type, template
    Optional fields: implements, imports, defaults, chunks
    """
    version: str
    type: str
    template: str
    source_file: Path
    implements: Optional[str] = None
    imports: Dict[str, Any] = field(default_factory=dict)
    defaults: Dict[str, str] = field(default_factory=dict)
    chunks: Dict[str, str] = field(default_factory=dict)


@dataclass
class AnnotationsConfig:
    """
    Configuration for automatic image annotations.

    When enabled, adds text overlays to generated images showing
    the variations used (haircut, haircolor, expression, etc.).
    """
    enabled: bool = False
    keys: List[str] = field(default_factory=list)  # Which variation keys to display (empty = all)
    position: str = "bottom-left"  # top-left, top-right, bottom-left, bottom-right
    font_size: int = 16
    background_alpha: int = 180  # 0-255 (0=transparent, 255=opaque)
    text_color: str = "white"
    padding: int = 10
    margin: int = 20


@dataclass
class OutputConfig:
    """
    Configuration for output directory and file naming.

    Controls session naming, filename patterns, and automatic annotations.
    """
    session_name: Optional[str] = None
    filename_keys: List[str] = field(default_factory=list)
    annotations: Optional[AnnotationsConfig] = None


@dataclass
class GenerationConfig:
    """
    Configuration for image generation settings.

    Defines how variations are generated (random vs combinatorial),
    seed management, and the number of images to generate.

    Seed modes (when seed_list is None):
    - fixed: Same seed for all images
    - progressive: SEED + index
    - random: -1 (random)

    Seed list mode (when seed_list is provided):
    - Overrides seed_mode
    - Each variation combination is tested on all seeds in the list
    - Example: 12 variations × 20 seeds = 240 images
    """
    mode: str  # 'random' | 'combinatorial'
    seed: int
    seed_mode: str  # 'fixed' | 'progressive' | 'random'
    max_images: int
    # Explicit seed list for seed-sweep mode (overrides seed/seed_mode)
    seed_list: Optional[List[int]] = None


@dataclass
class PromptConfig:
    """
    Configuration for a .prompt.yaml file.

    A prompt is the final configuration that combines a template with specific
    variations and generation settings to produce images.

    Required fields: version, name, generation, prompt
    Optional fields: implements, imports, chunks, parameters, negative_prompt, output, themes

    Themes Extension:
        themes: Dict mapping theme names to theme file paths (ex: {"cyberpunk": "./themes/cyberpunk/theme.yaml"})

    Note: implements is optional to support standalone prompts.
    Note: The 'prompt' field contains the content to inject into the parent template's {prompt} placeholder.
    Note: All prompts are themable by default. Use --theme or --theme-file to apply themes.
    """
    version: str
    name: str
    generation: GenerationConfig
    prompt: str
    source_file: Path
    implements: Optional[str] = None
    imports: Dict[str, Any] = field(default_factory=dict)
    chunks: Dict[str, str] = field(default_factory=dict)  # {chunk_name: chunk_file_path}
    parameters: Dict[str, Any] = field(default_factory=dict)
    negative_prompt: Optional[str] = None
    output: Optional[OutputConfig] = None
    # Themes Extension (inherited from template)
    themes: Optional['ThemeConfigBlock'] = None
    # After inheritance resolution, template will contain the fully resolved template
    template: Optional[str] = None


@dataclass
class ResolvedContext:
    """
    Context for template resolution with all variations loaded.

    This context is used during template resolution to inject chunks,
    apply selectors, and resolve placeholders.

    Attributes:
        imports: Dict mapping import names to their key-value variations
        chunks: Dict mapping chunk names to chunk dicts (with 'template', 'imports', 'defaults' keys)
        parameters: Merged SD WebUI parameters from inheritance chain
        variation_state: Current values for placeholders during generation
        style: Active style for this resolution (e.g., "cartoon", "realistic", "watercolor")
        theme_name: Name of the theme used for this resolution (e.g., "cyberpunk", "tropical", None if no theme)
        import_resolution: Metadata about how each import was resolved (theme source, override status, etc.)
        import_sources: Dict mapping placeholder names to the file that provided the variations
                       (e.g., {"HairCut": "themes/cyberpunk/cyberpunk_haircut.yaml"})
        import_metadata: Dict mapping placeholder names to metadata (e.g., {"HairCut": {"source_count": 3}})
        removed_placeholders: Set of placeholder names explicitly removed via [Remove] directive
                             (e.g., {"Accessories", "Underwear"} - these should resolve to empty string)
    """
    imports: Dict[str, Dict[str, str]]  # {import_name: {key: value}}
    chunks: Dict[str, Dict[str, Any]]   # {chunk_name: {'template': str, 'imports': dict, 'defaults': dict}}
    parameters: Dict[str, Any]
    variation_state: Dict[str, str] = field(default_factory=dict)
    # Themes Extension
    style: str = "default"
    theme_name: Optional[str] = None  # Theme name used for this resolution
    import_resolution: Dict[str, 'ImportResolution'] = field(default_factory=dict)
    import_sources: Dict[str, str] = field(default_factory=dict)  # placeholder -> file path
    import_metadata: Dict[str, Dict[str, Dict[str, Any]]] = field(default_factory=dict)  # placeholder -> metadata
    removed_placeholders: set = field(default_factory=set)  # Set[str] of intentionally removed placeholders


# ===== ADetailer Extension Support =====


@dataclass
class ADetailerDetector:
    """
    Configuration for a single ADetailer detector pass.

    Each detector runs independently and can target different regions
    (e.g., face, hands, body) with different models and prompts.

    ADetailer (After Detailer) is a SD WebUI extension that detects
    specific regions using YOLO models and applies a secondary inpainting
    pass with customizable prompts and parameters.
    """
    # Detection
    ad_model: str = "face_yolov8n.pt"
    ad_model_classes: str = ""
    ad_tab_enable: bool = True
    ad_confidence: float = 0.3
    ad_mask_k_largest: int = 0  # 0 = all detected, 1+ = only top K largest (aliased to ad_mask_k in API)

    # Prompts (optional - uses main prompt if empty)
    ad_prompt: str = ""
    ad_negative_prompt: str = ""

    # Mask filtering and processing
    ad_mask_filter_method: str = "Area"  # "Area" or "Confidence"
    ad_mask_min_ratio: float = 0.0
    ad_mask_max_ratio: float = 1.0
    ad_dilate_erode: int = 4
    ad_x_offset: int = 0
    ad_y_offset: int = 0
    ad_mask_merge_invert: str = "None"
    ad_mask_blur: int = 4

    # Inpainting
    ad_denoising_strength: float = 0.4
    ad_inpaint_only_masked: bool = True
    ad_inpaint_only_masked_padding: int = 32
    ad_use_inpaint_width_height: bool = False
    ad_inpaint_width: int = 512
    ad_inpaint_height: int = 512

    # Generation overrides (optional)
    ad_use_steps: bool = False
    ad_steps: int = 28
    ad_use_cfg_scale: bool = False
    ad_cfg_scale: float = 7.0
    ad_use_checkpoint: bool = False
    ad_checkpoint: Optional[str] = None
    ad_use_vae: bool = False
    ad_vae: Optional[str] = None
    ad_use_sampler: bool = False
    ad_sampler: str = "DPM++ 2M Karras"
    ad_scheduler: str = "Use same scheduler"
    ad_use_noise_multiplier: bool = False
    ad_noise_multiplier: float = 1.0
    ad_use_clip_skip: bool = False
    ad_clip_skip: int = 1
    ad_restore_face: bool = False
    ad_controlnet_model: str = "None"
    ad_controlnet_module: str = "None"
    ad_controlnet_weight: float = 1.0
    ad_controlnet_guidance_start: float = 0.0
    ad_controlnet_guidance_end: float = 1.0

    def to_dict(self) -> dict:
        """
        Convert to plain dict for JSON serialization (e.g., manifest files).

        Returns:
            dict: Dictionary representation of detector configuration
        """
        return {
            "ad_model": self.ad_model,
            "ad_model_classes": self.ad_model_classes,
            "ad_tab_enable": self.ad_tab_enable,
            "ad_prompt": self.ad_prompt,
            "ad_negative_prompt": self.ad_negative_prompt,
            "ad_confidence": self.ad_confidence,
            "ad_mask_filter_method": self.ad_mask_filter_method,
            "ad_mask_k_largest": self.ad_mask_k_largest,
            "ad_mask_min_ratio": self.ad_mask_min_ratio,
            "ad_mask_max_ratio": self.ad_mask_max_ratio,
            "ad_dilate_erode": self.ad_dilate_erode,
            "ad_x_offset": self.ad_x_offset,
            "ad_y_offset": self.ad_y_offset,
            "ad_mask_merge_invert": self.ad_mask_merge_invert,
            "ad_mask_blur": self.ad_mask_blur,
            "ad_denoising_strength": self.ad_denoising_strength,
            "ad_inpaint_only_masked": self.ad_inpaint_only_masked,
            "ad_inpaint_only_masked_padding": self.ad_inpaint_only_masked_padding,
            "ad_use_inpaint_width_height": self.ad_use_inpaint_width_height,
            "ad_inpaint_width": self.ad_inpaint_width,
            "ad_inpaint_height": self.ad_inpaint_height,
            "ad_use_steps": self.ad_use_steps,
            "ad_steps": self.ad_steps,
            "ad_use_cfg_scale": self.ad_use_cfg_scale,
            "ad_cfg_scale": self.ad_cfg_scale,
            "ad_use_checkpoint": self.ad_use_checkpoint,
            "ad_checkpoint": self.ad_checkpoint,
            "ad_use_vae": self.ad_use_vae,
            "ad_vae": self.ad_vae,
            "ad_use_sampler": self.ad_use_sampler,
            "ad_sampler": self.ad_sampler,
            "ad_scheduler": self.ad_scheduler,
            "ad_use_noise_multiplier": self.ad_use_noise_multiplier,
            "ad_noise_multiplier": self.ad_noise_multiplier,
            "ad_use_clip_skip": self.ad_use_clip_skip,
            "ad_clip_skip": self.ad_clip_skip,
            "ad_restore_face": self.ad_restore_face,
            "ad_controlnet_model": self.ad_controlnet_model,
            "ad_controlnet_module": self.ad_controlnet_module,
            "ad_controlnet_weight": self.ad_controlnet_weight,
            "ad_controlnet_guidance_start": self.ad_controlnet_guidance_start,
            "ad_controlnet_guidance_end": self.ad_controlnet_guidance_end,
        }

    def to_api_dict(self) -> dict:
        """
        Convert to Adetailer API format.

        Returns:
            dict: API payload for this detector in alwayson_scripts format
        """
        return {
            "ad_model": self.ad_model,
            "ad_model_classes": self.ad_model_classes,
            "ad_tab_enable": self.ad_tab_enable,
            "ad_prompt": self.ad_prompt,
            "ad_negative_prompt": self.ad_negative_prompt,
            "ad_confidence": self.ad_confidence,
            "ad_mask_filter_method": self.ad_mask_filter_method,
            "ad_mask_k": self.ad_mask_k_largest,  # Map ad_mask_k_largest to API's ad_mask_k
            "ad_mask_min_ratio": self.ad_mask_min_ratio,
            "ad_mask_max_ratio": self.ad_mask_max_ratio,
            "ad_dilate_erode": self.ad_dilate_erode,
            "ad_x_offset": self.ad_x_offset,
            "ad_y_offset": self.ad_y_offset,
            "ad_mask_merge_invert": self.ad_mask_merge_invert,
            "ad_mask_blur": self.ad_mask_blur,
            "ad_denoising_strength": self.ad_denoising_strength,
            "ad_inpaint_only_masked": self.ad_inpaint_only_masked,
            "ad_inpaint_only_masked_padding": self.ad_inpaint_only_masked_padding,
            "ad_use_inpaint_width_height": self.ad_use_inpaint_width_height,
            "ad_inpaint_width": self.ad_inpaint_width,
            "ad_inpaint_height": self.ad_inpaint_height,
            "ad_use_steps": self.ad_use_steps,
            "ad_steps": self.ad_steps,
            "ad_use_cfg_scale": self.ad_use_cfg_scale,
            "ad_cfg_scale": self.ad_cfg_scale,
            "ad_use_checkpoint": self.ad_use_checkpoint,
            "ad_checkpoint": self.ad_checkpoint,
            "ad_use_vae": self.ad_use_vae,
            "ad_vae": self.ad_vae,
            "ad_use_sampler": self.ad_use_sampler,
            "ad_sampler": self.ad_sampler,
            "ad_scheduler": self.ad_scheduler,
            "ad_use_noise_multiplier": self.ad_use_noise_multiplier,
            "ad_noise_multiplier": self.ad_noise_multiplier,
            "ad_use_clip_skip": self.ad_use_clip_skip,
            "ad_clip_skip": self.ad_clip_skip,
            "ad_restore_face": self.ad_restore_face,
            "ad_controlnet_model": self.ad_controlnet_model,
            "ad_controlnet_module": self.ad_controlnet_module,
            "ad_controlnet_weight": self.ad_controlnet_weight,
            "ad_controlnet_guidance_start": self.ad_controlnet_guidance_start,
            "ad_controlnet_guidance_end": self.ad_controlnet_guidance_end,
        }


@dataclass
class ADetailerConfig:
    """
    Top-level ADetailer configuration.

    Supports multiple detectors for multi-region refinement
    (e.g., face + hands in single generation).
    """
    enabled: bool = False
    detectors: List[ADetailerDetector] = field(default_factory=list)

    def to_dict(self) -> dict:
        """
        Convert to plain dict for JSON serialization (e.g., manifest files).

        Returns:
            dict: Dictionary representation of ADetailer configuration
        """
        return {
            "enabled": self.enabled,
            "detectors": [detector.to_dict() for detector in self.detectors]
        }

    def resolve_placeholders(self, variations: Dict[str, str]) -> 'ADetailerConfig':
        """
        Resolve placeholders in detector prompts with variation values.

        Creates a new ADetailerConfig with placeholders in ad_prompt and
        ad_negative_prompt replaced by actual variation values. This allows
        ADetailer prompts to use the same placeholders as the main prompt
        without affecting combinatorial generation.

        Args:
            variations: Dict mapping placeholder names to values
                       (e.g., {"Expression": "smiling", "EyeColor": "blue"})

        Returns:
            New ADetailerConfig with resolved prompts

        Example:
            >>> config = ADetailerConfig(enabled=True, detectors=[
            ...     ADetailerDetector(ad_prompt="face, {Expression}, {EyeColor} eyes")
            ... ])
            >>> variations = {"Expression": "smiling", "EyeColor": "blue"}
            >>> resolved = config.resolve_placeholders(variations)
            >>> resolved.detectors[0].ad_prompt
            'face, smiling, blue eyes'
        """
        from sd_generator_cli.templating.utils.placeholder_resolver import resolve_text_placeholders

        # Create new detectors with resolved prompts
        resolved_detectors = []
        for detector in self.detectors:
            # Create copy of detector (dataclass copy)
            from dataclasses import replace
            resolved_detector = replace(
                detector,
                ad_prompt=resolve_text_placeholders(detector.ad_prompt, variations),
                ad_negative_prompt=resolve_text_placeholders(detector.ad_negative_prompt, variations)
            )
            resolved_detectors.append(resolved_detector)

        # Return new config with resolved detectors
        return ADetailerConfig(
            enabled=self.enabled,
            detectors=resolved_detectors
        )

    def to_api_dict(self) -> Optional[dict]:
        """
        Convert to alwayson_scripts format for SD WebUI API.

        The ADetailer API format requires:
        - args[0]: bool - Enable ADetailer
        - args[1]: bool - Skip img2img
        - args[2+]: dict - Detector configurations

        Returns:
            dict with ADetailer payload, or None if disabled or no detectors
        """
        if not self.enabled or not self.detectors:
            return None

        return {
            "ADetailer": {
                "args": [
                    True,   # Enable ADetailer
                    False,  # Skip img2img
                    *[detector.to_api_dict() for detector in self.detectors]
                ]
            }
        }


@dataclass
class ADetailerFileConfig:
    """
    Configuration parsed from a .adetailer.yaml file.

    This represents a reusable Adetailer preset that can be
    imported into prompts via parameters: section.

    Example file structure:
        version: '2.0'
        name: 'High Quality Face Refinement'
        description: 'Optimal settings for close-up portraits'
        detector:
          ad_model: "face_yolov8n.pt"
          ad_confidence: 0.3
          ad_prompt: "detailed eyes, perfect skin"
    """
    version: str
    name: str
    detector: ADetailerDetector
    source_file: Path
    description: str = ''
