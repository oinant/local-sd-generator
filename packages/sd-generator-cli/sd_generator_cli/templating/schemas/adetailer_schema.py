"""
Schema for .adetailer.yaml files.

ADetailer files define face/hand detection and enhancement configurations
that can be imported into prompt files via the parameters.adetailer field.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, Literal, List, Union


class ADetailerDetectorSchema(BaseModel):
    """
    Schema for individual ADetailer detector configuration.

    Defines detection and inpainting parameters for a specific model
    (face, hand, person, etc.).
    """

    # Model and detection
    ad_model: str = Field(..., description="Detection model (e.g., face_yolov8n.pt)")
    ad_prompt: str = Field(default="", description="Additional prompt for inpainting")
    ad_negative_prompt: str = Field(default="", description="Negative prompt for inpainting")
    ad_confidence: float = Field(default=0.3, description="Detection confidence threshold", ge=0.0, le=1.0)

    # Mask settings
    ad_mask_k_largest: int = Field(default=1, description="Process K largest detections", ge=0)
    ad_mask_blur: int = Field(default=4, description="Mask blur radius", ge=0)
    ad_dilate_erode: int = Field(default=4, description="Mask dilation/erosion")
    ad_x_offset: int = Field(default=0, description="Horizontal mask offset")
    ad_y_offset: int = Field(default=0, description="Vertical mask offset")
    ad_mask_merge_invert: Optional[str] = Field(default="none", description="Mask merge/invert mode")

    # Inpainting settings
    ad_denoising_strength: float = Field(default=0.4, description="Denoising strength", ge=0.0, le=1.0)
    ad_inpaint_only_masked: bool = Field(default=True, description="Only inpaint masked area")
    ad_inpaint_only_masked_padding: int = Field(default=32, description="Masked area padding", ge=0)
    ad_use_inpaint_width_height: bool = Field(default=False, description="Use custom inpaint dimensions")
    ad_inpaint_width: int = Field(default=512, description="Inpaint width", ge=64)
    ad_inpaint_height: int = Field(default=512, description="Inpaint height", ge=64)

    # Generation overrides
    ad_use_steps: bool = Field(default=False, description="Override steps")
    ad_steps: int = Field(default=28, description="Sampling steps", ge=1)
    ad_use_cfg_scale: bool = Field(default=False, description="Override CFG scale")
    ad_cfg_scale: float = Field(default=7.0, description="CFG scale", ge=1.0)
    ad_use_checkpoint: bool = Field(default=False, description="Override checkpoint")
    ad_checkpoint: str = Field(default="", description="Checkpoint name")
    ad_use_vae: bool = Field(default=False, description="Override VAE")
    ad_vae: str = Field(default="", description="VAE name")
    ad_use_sampler: bool = Field(default=False, description="Override sampler")
    ad_sampler: str = Field(default="", description="Sampler name")
    ad_use_noise_multiplier: bool = Field(default=False, description="Override noise multiplier")
    ad_noise_multiplier: float = Field(default=1.0, description="Noise multiplier", ge=0.0)
    ad_use_clip_skip: bool = Field(default=False, description="Override CLIP skip")
    ad_clip_skip: int = Field(default=1, description="CLIP skip layers", ge=1)

    # Post-processing
    ad_restore_face: bool = Field(default=False, description="Apply face restoration")

    # ControlNet
    ad_controlnet_model: str = Field(default="none", description="ControlNet model")
    ad_controlnet_module: str = Field(default="none", description="ControlNet preprocessor")
    ad_controlnet_weight: float = Field(default=1.0, description="ControlNet weight", ge=0.0, le=2.0)
    ad_controlnet_guidance_start: float = Field(default=0.0, description="ControlNet guidance start", ge=0.0, le=1.0)
    ad_controlnet_guidance_end: float = Field(default=1.0, description="ControlNet guidance end", ge=0.0, le=1.0)

    class Config:
        extra = "allow"  # Allow extra fields for future ADetailer versions


class ADetailerFileSchema(BaseModel):
    """
    Schema for .adetailer.yaml files.

    ADetailer files must:
    - Have type: "adetailer_config"
    - Contain either detector (V2) or detectors (V1) configuration
    """

    type: Literal["adetailer_config"] = Field(
        ...,
        description="File type identifier (must be 'adetailer_config')"
    )

    version: str = Field(default="1.0", description="Schema version")
    name: Optional[str] = Field(None, description="Configuration name")

    # V2 format: single detector (dict)
    detector: Optional[Dict[str, Any]] = Field(
        None,
        description="Single detector configuration (V2 format)"
    )

    # V1 format: multiple detectors (list)
    detectors: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="List of detector configurations (V1 format)"
    )

    # Optional fields
    description: Optional[str] = Field(
        None,
        description="Human-readable description of this preset"
    )

    class Config:
        extra = "forbid"  # Reject unknown fields

    @validator('detector', 'detectors')
    def validate_has_detector_config(cls, v, values):
        """Ensure at least one detector configuration is present."""
        # Check if we have either detector or detectors
        detector = values.get('detector') if 'detector' in values else v
        detectors = values.get('detectors') if 'detectors' in values else v

        if detector is None and detectors is None:
            raise ValueError(
                "ADetailer config must have either 'detector' (V2) or 'detectors' (V1) field"
            )

        return v

    @validator('detectors')
    def validate_detectors_not_empty(cls, v):
        """Ensure detectors list is not empty if present."""
        if v is not None and len(v) == 0:
            raise ValueError("detectors field cannot be empty list")
        return v
