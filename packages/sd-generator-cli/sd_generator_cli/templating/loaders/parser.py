"""
Configuration parser for Template System V2.0.

This module converts raw YAML data dictionaries into typed config model objects.
It handles parsing of templates, chunks, prompts, and variation files.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from ..models.config_models import (
    TemplateConfig,
    ChunkConfig,
    PromptConfig,
    GenerationConfig,
    ADetailerFileConfig,
    ADetailerDetector,
    ADetailerConfig,
    OutputConfig,
    AnnotationsConfig
)
from ..models.theme_models import ThemeConfigBlock
import yaml


class ConfigParser:
    """
    Parser for converting YAML dictionaries into config model objects.

    This class handles the parsing of all V2.0 configuration file types:
    - .template.yaml → TemplateConfig
    - .chunk.yaml → ChunkConfig
    - .prompt.yaml → PromptConfig
    - .adetailer.yaml → ADetailerFileConfig
    - .yaml (variations) → Dict[str, str]
    """

    def parse_template(self, data: Dict[str, Any], source_file: Path) -> TemplateConfig:
        """
        Parse a .template.yaml file.

        Args:
            data: Raw YAML dictionary
            source_file: Absolute path to the source YAML file

        Returns:
            TemplateConfig object

        Raises:
            KeyError: If required fields are missing
            ValueError: If template field is not a string
        """
        # Validate template field type
        template = data['template']
        if not isinstance(template, str):
            raise ValueError(
                f"Invalid 'template' field in {source_file.name}: "
                f"Expected string, got {type(template).__name__}.\n"
                f"Hint: If you're using placeholders like {{prompt}}, you need to quote them:\n"
                f"  ✗ Wrong:   template: {{prompt}}\n"
                f"  ✓ Correct: template: \"{{prompt}}\"\n"
                f"  ✓ Or use:  template: |\n"
                f"               {{prompt}}"
            )

        # Validate {prompt} placeholder is present (Template Method Pattern)
        if '{prompt}' not in template:
            raise ValueError(
                f"Invalid template in {source_file.name}: "
                f"Template files must contain {{prompt}} placeholder. "
                f"This is the injection point for child content (Template Method Pattern).\n"
                f"Example:\n"
                f"  template: |\n"
                f"    masterpiece, {{prompt}}, detailed"
            )

        # Parse parameters with special handling for adetailer
        parameters = data.get('parameters') or {}
        parsed_parameters = self._parse_parameters(parameters, source_file.parent)

        # Parse output configuration
        output_config = self._parse_output_config(data.get('output'))

        # Parse themes configuration (presence indicates themable template)
        themes_config = self._parse_themes_config(data.get('themes'))

        return TemplateConfig(
            version=data.get('version', '1.0.0'),  # Default to 1.0.0 for backward compat
            name=data['name'],
            template=template,
            source_file=source_file,
            implements=data.get('implements'),
            parameters=parsed_parameters,  # Use parsed parameters
            imports=data.get('imports') or {},
            negative_prompt=data.get('negative_prompt') or '',
            output=output_config,
            # Themable Templates Extension
            themes=themes_config,
            style_sensitive=data.get('style_sensitive', False),
            style_sensitive_placeholders=data.get('style_sensitive_placeholders', [])
        )

    def parse_chunk(self, data: Dict[str, Any], source_file: Path) -> ChunkConfig:
        """
        Parse a .chunk.yaml file.

        Args:
            data: Raw YAML dictionary
            source_file: Absolute path to the source YAML file

        Returns:
            ChunkConfig object

        Raises:
            KeyError: If required fields are missing
            ValueError: If template field is not a string
        """
        # Validate template field type
        template = data['template']
        if not isinstance(template, str):
            raise ValueError(
                f"Invalid 'template' field in {source_file.name}: "
                f"Expected string, got {type(template).__name__}.\n"
                f"Hint: If you're using placeholders like {{Expression}}, you need to quote them:\n"
                f"  ✗ Wrong:   template: {{Expression}}\n"
                f"  ✓ Correct: template: \"{{Expression}}\"\n"
                f"  ✓ Or use:  template: |\n"
                f"               {{Expression}}"
            )

        # Validate reserved placeholders are NOT used in chunks
        reserved_placeholders = ['{prompt}', '{negprompt}', '{loras}']
        found_reserved = [p for p in reserved_placeholders if p in template]
        if found_reserved:
            raise ValueError(
                f"Invalid template in {source_file.name}: "
                f"Chunks cannot use reserved placeholders: {', '.join(found_reserved)}. "
                f"Reserved placeholders are only allowed in template files.\n"
                f"Chunks are reusable blocks composed into templates, not templates themselves."
            )

        return ChunkConfig(
            version=data.get('version', '1.0.0'),
            type=data['type'],
            template=template,
            source_file=source_file,
            implements=data.get('implements'),
            imports=data.get('imports') or {},
            defaults=data.get('defaults') or {},
            chunks=data.get('chunks') or {}
        )

    def parse_prompt(self, data: Dict[str, Any], source_file: Path) -> PromptConfig:
        """
        Parse a .prompt.yaml file.

        Supports both:
        - Standalone prompts (no implements field)
        - Inherited prompts (with implements field)

        Args:
            data: Raw YAML dictionary
            source_file: Absolute path to the source YAML file

        Returns:
            PromptConfig object

        Raises:
            KeyError: If required fields are missing
            ValueError: If prompt field is not a string or template field is used
        """
        # Validation: prompt.yaml files use 'prompt:' not 'template:'
        if 'template' in data:
            raise ValueError(
                f"Invalid field in {source_file.name}: "
                f"Prompt files must use 'prompt:' field, not 'template:'. "
                f"Please rename 'template:' to 'prompt:' in your file."
            )

        # Validation: V2.0 uses 'imports:' not 'variations:'
        if 'variations' in data:
            raise ValueError(
                f"Invalid field in {source_file.name}: "
                f"V2.0 Template System uses 'imports:' field, not 'variations:'. "
                f"Please rename 'variations:' to 'imports:' in your YAML file.\n"
                f"Example:\n"
                f"  ✗ Wrong:\n"
                f"    variations:\n"
                f"      HairCut: path/to/haircuts.yaml\n"
                f"  ✓ Correct:\n"
                f"    imports:\n"
                f"      HairCut: path/to/haircuts.yaml"
            )

        # Validate prompt field type
        prompt = data['prompt']
        if not isinstance(prompt, str):
            raise ValueError(
                f"Invalid 'prompt' field in {source_file.name}: "
                f"Expected string, got {type(prompt).__name__}.\n"
                f"Hint: If you're using placeholders like {{Angle}}, you need to quote them:\n"
                f"  ✗ Wrong:   prompt: {{Angle}}\n"
                f"  ✓ Correct: prompt: \"{{Angle}}\"\n"
                f"  ✓ Or use:  prompt: |\n"
                f"               {{Angle}}"
            )

        # Parse generation config
        gen_data = data['generation']
        generation = GenerationConfig(
            mode=gen_data['mode'],
            seed=gen_data['seed'],
            seed_mode=gen_data['seed_mode'],
            max_images=gen_data['max_images']
        )

        # Parse parameters with special handling for adetailer
        parameters = data.get('parameters') or {}
        parsed_parameters = self._parse_parameters(parameters, source_file.parent)

        # Parse output configuration
        output_config = self._parse_output_config(data.get('output'))

        # Parse themes configuration (inherited from template if not specified)
        themes_config = self._parse_themes_config(data.get('themes'))

        return PromptConfig(
            version=data.get('version', '1.0.0'),
            name=data['name'],
            generation=generation,
            prompt=prompt,
            source_file=source_file,
            implements=data.get('implements'),  # Optional: supports standalone prompts
            imports=data.get('imports') or {},
            parameters=parsed_parameters,  # Use parsed parameters
            negative_prompt=data.get('negative_prompt'),
            output=output_config,
            themes=themes_config
        )

    def parse_variations(self, data: Dict[str, Any]) -> Dict[str, Union[str, Dict[str, str]]]:
        """
        Parse a variations file (.yaml).

        V2.0 format supports three structures:
        1. Structured (with metadata):
           {
               "type": "variations",
               "name": "HairColors",
               "version": "1.0",
               "variations": {
                   "BobCut": "bob cut, chin-length hair",
                   "LongHair": "long flowing hair"
               }
           }
        2. Flat (direct dictionary):
           {
               "BobCut": "bob cut, chin-length hair",
               "LongHair": "long flowing hair"
           }
        3. Multi-part variations (dict values):
           {
               "short_bob": {
                   "main": "short bob cut, brown hair",
                   "lora": "<lora:hair_short_bob:0.7>"
               },
               "long_waves": {
                   "main": "long wavy hair, blonde",
                   "lora": "<lora:hair_long_waves:0.8>"
               }
           }

        Args:
            data: Raw YAML dictionary

        Returns:
            Dictionary mapping keys to prompt strings OR dicts of named parts
            - Simple variations: {key: "value"}
            - Multi-part variations: {key: {"part1": "value1", "part2": "value2"}}

        Raises:
            ValueError: If data is not a dictionary or variations key is missing
        """
        if not isinstance(data, dict):
            raise ValueError("Variations file must be a YAML dictionary")

        # Check if structured format (has 'variations' key)
        if 'variations' in data:
            variations = data['variations']
            if not isinstance(variations, dict):
                raise ValueError(
                    f"'variations' field must be a dictionary, got {type(variations).__name__}"
                )
            return self._parse_variation_values(variations)

        # Flat format: entire dict is variations
        return self._parse_variation_values(data)

    def _parse_variation_values(self, variations: Dict[str, Any]) -> Dict[str, Union[str, Dict[str, str]]]:
        """
        Parse variation values, preserving dict structure for multi-part variations.

        Args:
            variations: Dict of variation key-value pairs

        Returns:
            Dict with values as strings (simple) or dicts (multi-part)

        Raises:
            ValueError: If variation value is invalid type or dict has non-string values
        """
        parsed = {}

        for key, value in variations.items():
            if isinstance(value, dict):
                # Multi-part variation - validate all parts are strings
                for part_name, part_value in value.items():
                    if not isinstance(part_value, str):
                        raise ValueError(
                            f"Multi-part variation '{key}' has non-string value for part '{part_name}': "
                            f"got {type(part_value).__name__}. All parts must be strings."
                        )
                # Store as dict of parts
                parsed[str(key)] = {str(part): str(val) for part, val in value.items()}

            elif isinstance(value, str):
                # Simple variation - store as string
                parsed[str(key)] = str(value)

            else:
                # Invalid type
                raise ValueError(
                    f"Variation '{key}' has invalid value type: {type(value).__name__}. "
                    f"Values must be strings (simple variation) or dicts (multi-part variation)."
                )

        return parsed

    def parse_adetailer_file(self, data: Dict[str, Any], source_file: Path) -> ADetailerFileConfig:
        """
        Parse a .adetailer.yaml file.

        Expected structure:
            version: '2.0'
            name: 'High Quality Face Refinement'
            description: 'Optimal settings for close-up portraits'
            detector:
              ad_model: "face_yolov8n.pt"
              ad_confidence: 0.3
              ad_prompt: "detailed eyes, perfect skin"
              ad_negative_prompt: ""
              ad_denoising_strength: 0.4
              ad_inpaint_only_masked: true
              ad_inpaint_only_masked_padding: 32
              ad_use_steps: false
              ad_steps: 28
              ad_mask_k_largest: 0
              ad_dilate_erode: 4
              ad_mask_blur: 4
              ad_x_offset: 0
              ad_y_offset: 0

        Args:
            data: Raw YAML dictionary
            source_file: Absolute path to the .adetailer.yaml file

        Returns:
            ADetailerFileConfig object

        Raises:
            ValueError: If version invalid or required fields missing
        """
        # Validate version
        if 'version' not in data:
            raise ValueError(f"Missing 'version' field in {source_file.name}")
        if data['version'] != '2.0':
            raise ValueError(
                f"Invalid version '{data['version']}' in {source_file.name} "
                f"(expected '2.0')"
            )

        # Validate required 'detector' section
        if 'detector' not in data:
            raise ValueError(f"Missing 'detector' section in {source_file.name}")

        # Parse detector config
        detector_data = data['detector']
        if not isinstance(detector_data, dict):
            raise ValueError(
                f"'detector' field must be a dictionary in {source_file.name}, "
                f"got {type(detector_data).__name__}"
            )

        detector = ADetailerDetector(
            ad_model=detector_data.get('ad_model', 'face_yolov8n.pt'),
            ad_confidence=detector_data.get('ad_confidence', 0.3),
            ad_mask_k_largest=detector_data.get('ad_mask_k_largest', 0),
            ad_prompt=detector_data.get('ad_prompt', ''),
            ad_negative_prompt=detector_data.get('ad_negative_prompt', ''),
            ad_denoising_strength=detector_data.get('ad_denoising_strength', 0.4),
            ad_inpaint_only_masked=detector_data.get('ad_inpaint_only_masked', True),
            ad_inpaint_only_masked_padding=detector_data.get('ad_inpaint_only_masked_padding', 32),
            ad_use_steps=detector_data.get('ad_use_steps', False),
            ad_steps=detector_data.get('ad_steps', 28),
            ad_dilate_erode=detector_data.get('ad_dilate_erode', 4),
            ad_mask_blur=detector_data.get('ad_mask_blur', 4),
            ad_x_offset=detector_data.get('ad_x_offset', 0),
            ad_y_offset=detector_data.get('ad_y_offset', 0),
        )

        return ADetailerFileConfig(
            version=data['version'],
            name=data.get('name', source_file.stem),
            detector=detector,
            source_file=source_file,
            description=data.get('description', '')
        )

    def _parse_parameters(self, parameters: Dict[str, Any], base_path: Path) -> Dict[str, Any]:
        """
        Parse parameters section with special handling for adetailer.

        Standard parameters are passed through as-is.
        The 'adetailer' parameter is specially parsed into ADetailerConfig.

        Args:
            parameters: Raw parameters dict from YAML
            base_path: Base path for resolving file paths

        Returns:
            Parsed parameters dict with adetailer as ADetailerConfig object

        Raises:
            ValueError: If adetailer parameter format invalid
            FileNotFoundError: If adetailer file not found
        """
        parsed = parameters.copy()

        # Special handling for adetailer parameter
        if 'adetailer' in parsed:
            adetailer_value = parsed['adetailer']
            parsed['adetailer'] = self.parse_adetailer_parameter(adetailer_value, base_path)

        # Special handling for controlnet parameter
        if 'controlnet' in parsed:
            controlnet_value = parsed['controlnet']
            parsed['controlnet'] = self.parse_controlnet_parameter(controlnet_value, base_path)

        return parsed

    def parse_adetailer_parameter(
        self,
        adetailer_value: Any,
        base_path: Path
    ) -> ADetailerConfig:
        """
        Parse parameters.adetailer from prompt YAML.

        Supports four formats:
        1. String (single file path):
           adetailer: "../variations/adetailer/face_hq.adetailer.yaml"

        2. List (multiple detector files - simple paths):
           adetailer:
             - "../variations/adetailer/face_hq.adetailer.yaml"
             - "../variations/adetailer/hand_fix.adetailer.yaml"

        3. Dict with import + override:
           adetailer:
             import: "../variations/adetailer/face_hq.adetailer.yaml"
             override:
               ad_prompt: "custom prompt"
               ad_denoising_strength: 0.5

        4. List with dicts (mixed paths and overrides):
           adetailer:
             - import: "../variations/adetailer/face_hq.adetailer.yaml"
               override:
                 ad_prompt: "detailed face, {Expression}"
             - import: "../variations/adetailer/hand_fix.adetailer.yaml"
               override:
                 ad_prompt: "perfect hands"
             - "../variations/adetailer/body.adetailer.yaml"  # Mix simple path OK

        Override prompts support placeholders (e.g., {Expression}, {EyeColor})
        which will be resolved to the same values used in the main prompt,
        with NO combinatoric impact (same values, not new combinations).

        Args:
            adetailer_value: Value from parameters.adetailer (string/list/dict)
            base_path: Base path for resolving relative file paths

        Returns:
            ADetailerConfig with enabled=True and detectors loaded

        Raises:
            FileNotFoundError: If .adetailer.yaml file not found
            ValueError: If format is invalid
        """
        detectors: List[ADetailerDetector] = []

        if isinstance(adetailer_value, str):
            # Single file import
            detector = self._load_adetailer_file(adetailer_value, base_path)
            detectors.append(detector)

        elif isinstance(adetailer_value, list):
            # Multi-detector import (array of paths or dicts)
            for item in adetailer_value:
                if isinstance(item, str):
                    # Simple path
                    detector = self._load_adetailer_file(item, base_path)
                    detectors.append(detector)
                elif isinstance(item, dict):
                    # Dict with import + override
                    if 'import' not in item:
                        raise ValueError(
                            "parameters.adetailer list item dict must have 'import' key. "
                            "Example:\n"
                            "  adetailer:\n"
                            "    - import: path/to/config.adetailer.yaml\n"
                            "      override:\n"
                            "        ad_prompt: 'custom prompt'"
                        )

                    import_path = item['import']
                    detector = self._load_adetailer_file(import_path, base_path)

                    # Apply overrides if present
                    if 'override' in item:
                        overrides = item['override']
                        if not isinstance(overrides, dict):
                            raise ValueError(
                                f"parameters.adetailer item override must be a dict, "
                                f"got {type(overrides).__name__}"
                            )

                        for key, value in overrides.items():
                            if hasattr(detector, key):
                                setattr(detector, key, value)
                            else:
                                raise ValueError(
                                    f"Invalid override key '{key}' in parameters.adetailer. "
                                    f"Not a valid ADetailerDetector field."
                                )

                    detectors.append(detector)
                else:
                    raise ValueError(
                        f"parameters.adetailer array items must be strings or dicts, "
                        f"got {type(item).__name__}"
                    )

        elif isinstance(adetailer_value, dict):
            # Import with override
            if 'import' not in adetailer_value:
                raise ValueError(
                    "parameters.adetailer dict must have 'import' key. "
                    "Example:\n"
                    "  adetailer:\n"
                    "    import: path/to/config.adetailer.yaml\n"
                    "    override:\n"
                    "      ad_prompt: 'custom prompt'"
                )

            import_path = adetailer_value['import']
            detector = self._load_adetailer_file(import_path, base_path)

            # Apply overrides if present
            if 'override' in adetailer_value:
                overrides = adetailer_value['override']
                if not isinstance(overrides, dict):
                    raise ValueError(
                        f"parameters.adetailer.override must be a dict, "
                        f"got {type(overrides).__name__}"
                    )

                for key, value in overrides.items():
                    if hasattr(detector, key):
                        setattr(detector, key, value)
                    else:
                        raise ValueError(
                            f"Invalid override key '{key}' in parameters.adetailer. "
                            f"Not a valid ADetailerDetector field."
                        )

            detectors.append(detector)

        else:
            raise ValueError(
                f"parameters.adetailer must be a string, list, or dict, "
                f"got {type(adetailer_value).__name__}"
            )

        return ADetailerConfig(enabled=True, detectors=detectors)

    def _load_adetailer_file(self, path: str, base_path: Path) -> ADetailerDetector:
        """
        Load a .adetailer.yaml file and return its detector.

        Helper function for parse_adetailer_parameter().

        Args:
            path: Relative path to .adetailer.yaml file
            base_path: Base path for resolving relative paths

        Returns:
            ADetailerDetector from the file

        Raises:
            FileNotFoundError: If file not found
            ValueError: If file format invalid
        """
        # Resolve path relative to base_path
        resolved_path = (base_path / path).resolve()

        if not resolved_path.exists():
            raise FileNotFoundError(
                f"Adetailer file not found: {resolved_path}\n"
                f"  Looked in: {base_path}\n"
                f"  For: {path}"
            )

        # Load and parse YAML
        with open(resolved_path, 'r') as f:
            data = yaml.safe_load(f)

        # Parse as ADetailerFileConfig
        config = self.parse_adetailer_file(data, resolved_path)

        return config.detector

    def parse_controlnet_parameter(
        self,
        controlnet_value: Any,
        base_path: Path
    ) -> "ControlNetConfig":
        """
        Parse parameters.controlnet from prompt YAML.

        Supports three formats:
        1. String (single file path):
           controlnet: "../variations/controlnet/canny.controlnet.yaml"

        2. List (multiple unit files + optional overrides):
           controlnet:
             - "../variations/controlnet/canny.controlnet.yaml"
             - "../variations/controlnet/depth.controlnet.yaml"
             - weight: 0.8  # Override first unit

        3. Dict (inline configuration):
           controlnet:
             model: "control_v11p_sd15_canny"
             module: "canny"
             weight: 1.0

        Args:
            controlnet_value: Value from parameters.controlnet (string/list/dict)
            base_path: Base path for resolving relative file paths

        Returns:
            ControlNetConfig with units loaded

        Raises:
            FileNotFoundError: If .controlnet.yaml file not found
            ValueError: If format is invalid
        """
        from ..models.controlnet import ControlNetUnit, ControlNetConfig

        units: List[ControlNetUnit] = []

        if isinstance(controlnet_value, str):
            # Single file import
            config = self._load_controlnet_file(controlnet_value, base_path)
            units.extend(config.units)

        elif isinstance(controlnet_value, list):
            # Multi-unit import (files + optional dict overrides)
            overrides: Optional[Dict] = None

            for item in controlnet_value:
                if isinstance(item, str):
                    # Load file
                    config = self._load_controlnet_file(item, base_path)
                    units.extend(config.units)
                elif isinstance(item, dict):
                    # Store overrides for first unit
                    if overrides is None:
                        overrides = item

            # Apply overrides to first unit if present
            if overrides and units:
                for key, value in overrides.items():
                    if hasattr(units[0], key):
                        setattr(units[0], key, value)
                    else:
                        raise ValueError(
                            f"Invalid override key '{key}' in parameters.controlnet. "
                            f"Not a valid ControlNetUnit field."
                        )

        elif isinstance(controlnet_value, dict):
            # Inline unit configuration
            try:
                unit = ControlNetUnit(**controlnet_value)
                units.append(unit)
            except TypeError as e:
                raise ValueError(
                    f"Invalid inline controlnet configuration: {e}"
                )

        else:
            raise ValueError(
                f"parameters.controlnet must be a string, list, or dict, "
                f"got {type(controlnet_value).__name__}"
            )

        return ControlNetConfig(units=units)

    def _load_controlnet_file(self, path: str, base_path: Path) -> "ControlNetConfig":
        """
        Load a .controlnet.yaml file and return its config.

        Helper function for parse_controlnet_parameter().

        Args:
            path: Relative path to .controlnet.yaml file
            base_path: Base path for resolving relative paths

        Returns:
            ControlNetConfig from the file

        Raises:
            FileNotFoundError: If file not found
            ValueError: If file is invalid
        """
        from ..loaders.controlnet_parser import parse_controlnet_file

        # Resolve path
        resolved_path = (base_path / path).resolve()

        if not resolved_path.exists():
            raise FileNotFoundError(
                f"ControlNet file not found:\n"
                f"  Looked in: {base_path}\n"
                f"  For: {path}"
            )

        # Parse and return config
        return parse_controlnet_file(resolved_path)

    def _parse_output_config(self, output_data: Optional[Dict[str, Any]]) -> Optional[OutputConfig]:
        """
        Parse output configuration with annotations.

        Args:
            output_data: Raw output dict from YAML (can be None)

        Returns:
            OutputConfig object or None if no output_data
        """
        if not output_data:
            return None

        # Parse session_name
        session_name = output_data.get('session_name')

        # Parse filename_keys
        filename_keys = output_data.get('filename_keys', [])

        # Parse annotations if present
        annotations_data = output_data.get('annotations')
        annotations_config = None
        if annotations_data:
            annotations_config = AnnotationsConfig(
                enabled=annotations_data.get('enabled', False),
                keys=annotations_data.get('keys', []),
                position=annotations_data.get('position', 'bottom-left'),
                font_size=annotations_data.get('font_size', 16),
                background_alpha=annotations_data.get('background_alpha', 180),
                text_color=annotations_data.get('text_color', 'white'),
                padding=annotations_data.get('padding', 10),
                margin=annotations_data.get('margin', 20)
            )

        return OutputConfig(
            session_name=session_name,
            filename_keys=filename_keys,
            annotations=annotations_config
        )

    def _parse_themes_config(self, themes_data: Optional[Dict[str, Any]]) -> Optional[ThemeConfigBlock]:
        """
        Parse themes configuration block.

        The presence of a themes block indicates a themable template.
        Supports three modes:
        1. Explicit only: themes.explicit dict
        2. Autodiscovery only: themes.enable_autodiscovery: true
        3. Hybrid: both explicit and autodiscovery

        Args:
            themes_data: Raw themes dict from YAML (can be None)

        Returns:
            ThemeConfigBlock object or None if no themes_data

        Examples:
            # Explicit only
            themes:
              explicit:
                pirates: ./pirates/theme.yaml

            # Autodiscovery only
            themes:
              enable_autodiscovery: true

            # Hybrid
            themes:
              enable_autodiscovery: true
              search_paths: [./themes/, ../shared/]
              explicit:
                custom: ../custom/theme.yaml
        """
        if not themes_data:
            return None

        return ThemeConfigBlock(
            enable_autodiscovery=themes_data.get('enable_autodiscovery', False),
            search_paths=themes_data.get('search_paths', []),
            explicit=themes_data.get('explicit', {})
        )
