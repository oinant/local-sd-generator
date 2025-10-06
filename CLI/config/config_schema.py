"""
Configuration Schema for JSON Config System (SF-1)

Defines dataclasses for configuration structure with validation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union


@dataclass
class ModelConfig:
    """Model/checkpoint configuration"""
    checkpoint: Optional[str] = None


@dataclass
class PromptConfig:
    """Prompt configuration"""
    template: str = ""
    negative: str = ""


@dataclass
class GenerationConfig:
    """Generation strategy configuration"""
    mode: str = "combinatorial"  # "combinatorial", "random", "ask"
    seed_mode: str = "progressive"  # "fixed", "progressive", "random", "ask"
    seed: int = 42
    max_images: int = -1  # -1 means ask user


@dataclass
class ParametersConfig:
    """Stable Diffusion parameters"""
    width: int = 512
    height: int = 768
    steps: int = 30
    cfg_scale: float = 7.0
    sampler: str = "DPM++ 2M Karras"
    batch_size: int = 1
    batch_count: int = 1

    # Hires Fix parameters
    enable_hr: bool = False
    hr_scale: float = 2.0
    hr_upscaler: str = "R-ESRGAN 4x+"
    denoising_strength: float = 0.5
    hr_second_pass_steps: Optional[int] = None


@dataclass
class OutputConfig:
    """Output naming configuration"""
    session_name: Optional[str] = None
    filename_keys: List[str] = field(default_factory=list)


@dataclass
class GenerationSessionConfig:
    """Complete generation session configuration"""
    version: str = "1.0"
    name: str = ""
    description: str = ""
    model: ModelConfig = field(default_factory=ModelConfig)
    prompt: PromptConfig = field(default_factory=PromptConfig)
    variations: Dict[str, Union[str, List[str]]] = field(default_factory=dict)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    parameters: ParametersConfig = field(default_factory=ParametersConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GenerationSessionConfig':
        """
        Create configuration from dictionary.

        Args:
            data: Dictionary loaded from JSON

        Returns:
            GenerationSessionConfig instance
        """
        # Extract nested configs
        model_data = data.get("model", {})
        prompt_data = data.get("prompt", {})
        variations_data = data.get("variations", {})
        generation_data = data.get("generation", {})
        parameters_data = data.get("parameters", {})
        output_data = data.get("output", {})

        return cls(
            version=data.get("version", "1.0"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            model=ModelConfig(
                checkpoint=model_data.get("checkpoint")
            ),
            prompt=PromptConfig(
                template=prompt_data.get("template", ""),
                negative=prompt_data.get("negative", "")
            ),
            variations=variations_data,
            generation=GenerationConfig(
                mode=generation_data.get("mode", "combinatorial"),
                seed_mode=generation_data.get("seed_mode", "progressive"),
                seed=generation_data.get("seed", 42),
                max_images=generation_data.get("max_images", -1)
            ),
            parameters=ParametersConfig(
                width=parameters_data.get("width", 512),
                height=parameters_data.get("height", 768),
                steps=parameters_data.get("steps", 30),
                cfg_scale=parameters_data.get("cfg_scale", 7.0),
                sampler=parameters_data.get("sampler", "DPM++ 2M Karras"),
                batch_size=parameters_data.get("batch_size", 1),
                batch_count=parameters_data.get("batch_count", 1),
                enable_hr=parameters_data.get("enable_hr", False),
                hr_scale=parameters_data.get("hr_scale", 2.0),
                hr_upscaler=parameters_data.get("hr_upscaler", "R-ESRGAN 4x+"),
                denoising_strength=parameters_data.get("denoising_strength", 0.5),
                hr_second_pass_steps=parameters_data.get("hr_second_pass_steps")
            ),
            output=OutputConfig(
                session_name=output_data.get("session_name"),
                filename_keys=output_data.get("filename_keys", [])
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "model": {
                "checkpoint": self.model.checkpoint
            },
            "prompt": {
                "template": self.prompt.template,
                "negative": self.prompt.negative
            },
            "variations": self.variations,
            "generation": {
                "mode": self.generation.mode,
                "seed_mode": self.generation.seed_mode,
                "seed": self.generation.seed,
                "max_images": self.generation.max_images
            },
            "parameters": {
                "width": self.parameters.width,
                "height": self.parameters.height,
                "steps": self.parameters.steps,
                "cfg_scale": self.parameters.cfg_scale,
                "sampler": self.parameters.sampler,
                "batch_size": self.parameters.batch_size,
                "batch_count": self.parameters.batch_count,
                "enable_hr": self.parameters.enable_hr,
                "hr_scale": self.parameters.hr_scale,
                "hr_upscaler": self.parameters.hr_upscaler,
                "denoising_strength": self.parameters.denoising_strength,
                "hr_second_pass_steps": self.parameters.hr_second_pass_steps
            },
            "output": {
                "session_name": self.output.session_name,
                "filename_keys": self.output.filename_keys
            }
        }


@dataclass
class ValidationError:
    """Validation error with field path and message"""
    field: str
    message: str
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        """Format error message"""
        msg = f"{self.field}: {self.message}"
        if self.suggestion:
            msg += f"\n  → {self.suggestion}"
        return msg


class ValidationResult:
    """Result of configuration validation"""

    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def add_error(self, field: str, message: str, suggestion: Optional[str] = None):
        """Add validation error"""
        self.errors.append(ValidationError(field, message, suggestion))

    def add_warning(self, field: str, message: str, suggestion: Optional[str] = None):
        """Add validation warning"""
        self.warnings.append(ValidationError(field, message, suggestion))

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)"""
        return len(self.errors) == 0

    def get_error_messages(self) -> List[str]:
        """Get formatted error messages"""
        return [str(err) for err in self.errors]

    def get_warning_messages(self) -> List[str]:
        """Get formatted warning messages"""
        return [str(warn) for warn in self.warnings]

    def __str__(self) -> str:
        """Format all errors and warnings"""
        lines = []

        if self.errors:
            lines.append("Validation Errors:")
            for err in self.errors:
                lines.append(f"  ✗ {err}")

        if self.warnings:
            if lines:
                lines.append("")
            lines.append("Warnings:")
            for warn in self.warnings:
                lines.append(f"  ⚠ {warn}")

        return "\n".join(lines)
