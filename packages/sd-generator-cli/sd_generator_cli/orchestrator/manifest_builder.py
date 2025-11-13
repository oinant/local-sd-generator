"""ManifestBuilder - builds manifest snapshot from generation context."""

import re
from datetime import datetime
from typing import Any, Optional

from ..api.sdapi_client import SDAPIClient
from ..templating.models.config_models import PromptConfig
from .session_config import SessionConfig
from .session_event_collector import SessionEventCollector
from .event_types import EventType


class ManifestBuilder:
    """Builds manifest snapshots from generation state.

    This class extracts all manifest-building logic from _generate():
    - Runtime info fetching from SD API
    - Variations extraction from context and prompts
    - Generation parameters building
    - API parameters serialization
    - Complete snapshot assembly

    The builder emits events via SessionEventCollector for progress tracking.

    Example:
        >>> builder = ManifestBuilder(api_client, events)
        >>> snapshot = builder.build_snapshot(
        ...     session_config=session_config,
        ...     prompt_config=prompt_config,
        ...     context=context,
        ...     resolved_config=resolved_config,
        ...     prompts=prompts,
        ...     stats=stats
        ... )
    """

    def __init__(
        self,
        api_client: SDAPIClient,
        events: SessionEventCollector
    ):
        """Initialize manifest builder.

        Args:
            api_client: SD API client for runtime info fetching
            events: Event collector for output management
        """
        self.api_client = api_client
        self.events = events

    def build_snapshot(
        self,
        session_config: SessionConfig,
        prompt_config: PromptConfig,
        context: Any,  # ResolvedContext from V2Pipeline
        resolved_config: Any,  # ResolvedConfig from V2Pipeline
        prompts: list[dict],
        stats: dict
    ) -> dict:
        """Build complete manifest snapshot.

        This is the main entry point that orchestrates all snapshot building.

        Args:
            session_config: Session configuration
            prompt_config: Resolved prompt configuration
            context: Resolved context (from V2Pipeline.resolve())
            resolved_config: Resolved config (from V2Pipeline.resolve())
            prompts: Generated prompts list
            stats: Prompt generation statistics

        Returns:
            Complete manifest snapshot dict
        """
        # Step 1: Fetch runtime info from API
        runtime_info = self.fetch_runtime_info()

        # Step 2: Extract variations from context and prompts
        variations_map = self.extract_variations(
            context=context,
            resolved_config=resolved_config,
            prompts=prompts
        )

        # Step 3: Build generation parameters
        generation_params = self.build_generation_params(
            prompt_config=prompt_config,
            resolved_config=resolved_config,
            prompts=prompts,
            stats=stats
        )

        # Step 4: Build API parameters from first prompt
        api_params = self.build_api_params(prompts)

        # Step 5: Assemble complete snapshot
        snapshot = {
            "version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "runtime_info": runtime_info,
            "resolved_template": {
                "prompt": resolved_config.template,
                "negative": resolved_config.negative_prompt or ''
            },
            "generation_params": generation_params,
            "api_params": api_params,
            "variations": variations_map,
            "fixed_placeholders": session_config.fixed_placeholders,
            # Themable Templates metadata
            "theme_name": session_config.theme_name,
            "style": session_config.style
        }

        return snapshot

    def fetch_runtime_info(self) -> dict:
        """Fetch runtime info from SD API.

        Extracts:
        - SD model checkpoint name

        Returns:
            Runtime info dict with checkpoint or fallback
        """
        try:
            checkpoint = self.api_client.get_model_checkpoint()
            return {"sd_model_checkpoint": checkpoint}
        except Exception as e:
            self.events.emit(
                EventType.WARNING,
                {"message": f"Could not fetch runtime info: {e}"}
            )
            return {"sd_model_checkpoint": "unknown"}

    def extract_variations(
        self,
        context: Any,
        resolved_config: Any,
        prompts: list[dict]
    ) -> dict:
        """Extract variations: complete pool + actually used values.

        This extracts:
        1. All placeholders that appear in template or ControlNet images
        2. Complete pool of available values (from context.imports)
        3. Actually used values (from generated prompts)

        Args:
            context: Resolved context (has imports dict)
            resolved_config: Resolved config (has template + parameters)
            prompts: Generated prompts with variations

        Returns:
            Variations map dict:
            {
                "PlaceholderName": {
                    "available": ["value1", "value2", ...],
                    "used": ["value1"],  # Actually used in generated prompts
                    "count": 2
                }
            }
        """
        variations_map = {}

        # Step 1: Extract placeholders from template
        placeholder_pattern = re.compile(r'\{(\w+)(?:\[[^\]]+\])?\}')
        template_str = resolved_config.template if resolved_config.template else ""
        placeholders_in_template = set(placeholder_pattern.findall(template_str))

        # Step 2: Extract placeholders from ControlNet images
        placeholders_in_parameters = set()
        if resolved_config.parameters and 'controlnet' in resolved_config.parameters:
            controlnet_config = resolved_config.parameters['controlnet']
            if hasattr(controlnet_config, 'units'):
                for unit in controlnet_config.units:
                    if unit.image and isinstance(unit.image, dict):
                        # The dict keys are the import names
                        placeholders_in_parameters.update(unit.image.keys())

        all_placeholders = placeholders_in_template | placeholders_in_parameters

        # Step 3: Extract complete pool from context.imports
        # (only for placeholders actually used in template/parameters)
        for placeholder_name, import_data in context.imports.items():
            # Skip if placeholder doesn't appear in template or parameters
            if placeholder_name not in all_placeholders:
                continue

            if isinstance(import_data, dict):
                # import_data is a dict like {"key1": "value1", "key2": "value2", ...}
                all_values = list(import_data.values())
                variations_map[placeholder_name] = {
                    "available": all_values,
                    "used": [],  # Will be filled in next step
                    "count": len(all_values)
                }

        # Step 4: Extract actually used values from generated prompts
        for prompt_dict in prompts:
            variations = prompt_dict.get('variations', {})
            for key, value in variations.items():
                if key in variations_map and isinstance(variations_map[key], dict):
                    used_list = variations_map[key].get("used")
                    if isinstance(used_list, list) and value not in used_list:
                        used_list.append(value)
                else:
                    # Fallback: if placeholder not in imports (shouldn't happen)
                    variations_map[key] = {
                        "available": [value],
                        "used": [value],
                        "count": 1
                    }

        return variations_map

    def build_generation_params(
        self,
        prompt_config: PromptConfig,
        resolved_config: Any,
        prompts: list[dict],
        stats: dict
    ) -> dict:
        """Build generation parameters object.

        Args:
            prompt_config: Resolved prompt configuration
            resolved_config: Resolved config (has generation config)
            prompts: Generated prompts list
            stats: Prompt generation statistics

        Returns:
            Generation params dict with mode, seed_mode, base_seed, etc.
        """
        # Extract from prompt_config (has GenerationConfig)
        gen_mode = prompt_config.generation.mode
        seed_mode = prompt_config.generation.seed_mode
        base_seed = prompt_config.generation.seed if prompt_config.generation.seed != -1 else None

        # Calculate total combinations
        total_combs = stats.get('total_combinations', 1) if stats.get('total_placeholders', 0) > 0 else 1

        generation_params = {
            "mode": gen_mode,
            "seed_mode": seed_mode,
            "base_seed": base_seed,
            "num_images": len(prompts),
            "total_combinations": total_combs
        }

        # Add seed_list if present (seed-sweep mode)
        if resolved_config.generation and hasattr(resolved_config.generation, 'seed_list') and resolved_config.generation.seed_list:
            generation_params["seed_list"] = resolved_config.generation.seed_list

        return generation_params

    def build_api_params(self, prompts: list[dict]) -> dict:
        """Build API parameters from first prompt.

        Serializes extension configs (ADetailer, ControlNet) to dicts.

        Args:
            prompts: Generated prompts list

        Returns:
            API params dict (serializable)
        """
        api_params = {}

        if prompts and 'parameters' in prompts[0]:
            params = prompts[0]['parameters'].copy()

            # Convert extension configs to serializable dicts
            if 'adetailer' in params and hasattr(params['adetailer'], 'to_dict'):
                params['adetailer'] = params['adetailer'].to_dict()
            if 'controlnet' in params and hasattr(params['controlnet'], 'to_dict'):
                params['controlnet'] = params['controlnet'].to_dict()

            api_params = params

        return api_params
