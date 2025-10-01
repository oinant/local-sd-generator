"""
Module for generating and managing JSON metadata for generation sessions.

This module provides utilities for creating structured metadata files
that document all aspects of an image generation session.

Part of SF-5: JSON Metadata Export
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


def generate_metadata_dict(
    prompt_template: str,
    negative_prompt: str,
    variations_loaded: Dict[str, Dict[str, str]],
    generation_info: Dict[str, Any],
    parameters: Dict[str, Any],
    output_info: Dict[str, Any],
    model_info: Optional[Dict[str, str]] = None,
    config_source: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a complete metadata dictionary for a generation session.

    Args:
        prompt_template: The prompt template with placeholders
        negative_prompt: The negative prompt used
        variations_loaded: Dict of {placeholder: {key: value}} variations
        generation_info: Dict with session info (date, timestamp, total_images, etc.)
        parameters: Dict with generation parameters (width, height, steps, etc.)
        output_info: Dict with output configuration (folder, filename_keys, etc.)
        model_info: Optional dict with model/checkpoint info
        config_source: Optional path to source config file (for JSON configs)

    Returns:
        Complete metadata dictionary ready for JSON export

    Example:
        >>> metadata = generate_metadata_dict(
        ...     prompt_template="masterpiece, {Expression}, {Angle}",
        ...     negative_prompt="low quality",
        ...     variations_loaded={
        ...         "Expression": {"smiling": "smiling", "sad": "sad"},
        ...         "Angle": {"front": "front view"}
        ...     },
        ...     generation_info={
        ...         "date": "2025-10-01T14:30:52",
        ...         "timestamp": "20251001_143052",
        ...         "total_images": 6,
        ...         "generation_time_seconds": 45.2
        ...     },
        ...     parameters={
        ...         "width": 512,
        ...         "height": 768,
        ...         "steps": 30,
        ...         "cfg_scale": 7.0,
        ...         "sampler": "DPM++ 2M Karras"
        ...     },
        ...     output_info={
        ...         "folder": "/path/to/output",
        ...         "filename_keys": ["Expression", "Angle"]
        ...     }
        ... )
    """
    metadata = {
        "version": "1.0",
        "generation_info": generation_info,
        "prompt": {
            "template": prompt_template,
            "negative": negative_prompt
        },
        "variations": _build_variations_metadata(variations_loaded, prompt_template),
        "generation": _extract_generation_mode_info(generation_info),
        "parameters": parameters,
        "output": output_info
    }

    # Add model info if provided
    if model_info:
        metadata["model"] = model_info

    # Add config source if provided
    if config_source:
        metadata["config_source"] = config_source

    # Add example resolved prompt
    if variations_loaded:
        example_prompt = _create_example_prompt(prompt_template, variations_loaded)
        metadata["prompt"]["example_resolved"] = example_prompt

    return metadata


def _build_variations_metadata(
    variations_dict: Dict[str, Dict[str, str]],
    prompt_template: str,
    max_values_in_metadata: int = 10
) -> Dict[str, Dict[str, Any]]:
    """
    Build variations metadata with counts and truncated value lists.

    Args:
        variations_dict: Dict of {placeholder: {key: value}}
        prompt_template: Original prompt template (for context)
        max_values_in_metadata: Maximum number of values to include (default: 10)

    Returns:
        Dict with variation metadata including counts and value lists
    """
    variations_metadata = {}

    for placeholder, variations in variations_dict.items():
        values_list = list(variations.values())
        count = len(values_list)

        # Truncate to max_values_in_metadata
        if count > max_values_in_metadata:
            displayed_values = values_list[:max_values_in_metadata]
            displayed_values.append(f"... and {count - max_values_in_metadata} more")
        else:
            displayed_values = values_list

        variations_metadata[placeholder] = {
            "count": count,
            "values": displayed_values
        }

    return variations_metadata


def _extract_generation_mode_info(generation_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract generation mode specific information.

    Args:
        generation_info: Full generation info dict

    Returns:
        Dict with generation mode, seed, counts, etc.
    """
    return {
        "mode": generation_info.get("generation_mode", "unknown"),
        "seed_mode": generation_info.get("seed_mode", "unknown"),
        "seed": generation_info.get("seed", -1),
        "total_combinations": generation_info.get("total_combinations", 0),
        "images_generated": generation_info.get("total_images", 0)
    }


def _create_example_prompt(
    prompt_template: str,
    variations_dict: Dict[str, Dict[str, str]]
) -> str:
    """
    Create an example resolved prompt using first variation of each placeholder.

    Args:
        prompt_template: Template with placeholders
        variations_dict: Dict of variations

    Returns:
        Example prompt with placeholders replaced
    """
    example = prompt_template

    for placeholder, variations in variations_dict.items():
        if variations:
            # Take the first value as example
            first_value = list(variations.values())[0]
            example = example.replace(f"{{{placeholder}}}", first_value)

    return example


def save_metadata_json(
    metadata_dict: Dict[str, Any],
    output_folder: str,
    filename: str = "metadata.json"
) -> Path:
    """
    Save metadata dictionary as pretty-printed JSON file.

    Args:
        metadata_dict: Metadata dictionary to save
        output_folder: Folder to save the file in
        filename: Name of the metadata file (default: "metadata.json")

    Returns:
        Path to the saved metadata file

    Raises:
        OSError: If folder doesn't exist or write fails
    """
    output_path = Path(output_folder)

    # Ensure folder exists
    if not output_path.exists():
        raise OSError(f"Output folder does not exist: {output_folder}")

    metadata_file = output_path / filename

    # Write with pretty-printing (2-space indent)
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata_dict, f, indent=2, ensure_ascii=False)

    return metadata_file


def load_metadata_json(
    output_folder: str,
    filename: str = "metadata.json"
) -> Dict[str, Any]:
    """
    Load metadata from JSON file.

    Args:
        output_folder: Folder containing the metadata file
        filename: Name of the metadata file (default: "metadata.json")

    Returns:
        Metadata dictionary

    Raises:
        FileNotFoundError: If metadata file doesn't exist
        JSONDecodeError: If file is not valid JSON
    """
    metadata_file = Path(output_folder) / filename

    if not metadata_file.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    return metadata


def create_legacy_config_text(metadata_dict: Dict[str, Any]) -> str:
    """
    Create legacy session_config.txt content from metadata dict.

    This is for backward compatibility.

    Args:
        metadata_dict: Metadata dictionary

    Returns:
        Text content for session_config.txt
    """
    lines = []
    lines.append("=" * 80)
    lines.append("DEPRECATION NOTICE:")
    lines.append("This text file is deprecated. Please use metadata.json instead.")
    lines.append("=" * 80)
    lines.append("")

    gen_info = metadata_dict.get("generation_info", {})
    lines.append(f"Session: {gen_info.get('session_name', 'N/A')}")
    lines.append(f"Date: {gen_info.get('date', 'N/A')}")
    lines.append(f"Total Images: {gen_info.get('total_images', 0)}")
    lines.append("")

    prompt_info = metadata_dict.get("prompt", {})
    lines.append(f"Prompt Template: {prompt_info.get('template', 'N/A')}")
    lines.append(f"Negative Prompt: {prompt_info.get('negative', 'N/A')}")
    lines.append("")

    variations = metadata_dict.get("variations", {})
    lines.append("Variations:")
    for placeholder, var_info in variations.items():
        lines.append(f"  {placeholder}: {var_info.get('count', 0)} variations")
    lines.append("")

    lines.append("For complete information, see metadata.json")

    return "\n".join(lines)


if __name__ == "__main__":
    # Quick test
    print("🧪 Testing metadata_generator module\n")

    test_metadata = generate_metadata_dict(
        prompt_template="masterpiece, {Expression}, {Angle}, beautiful",
        negative_prompt="low quality, blurry",
        variations_loaded={
            "Expression": {"smiling": "smiling", "sad": "sad", "angry": "angry"},
            "Angle": {"front": "front view", "side": "side view"}
        },
        generation_info={
            "date": "2025-10-01T14:30:52",
            "timestamp": "20251001_143052",
            "session_name": "test_session",
            "total_images": 6,
            "generation_time_seconds": 45.2,
            "generation_mode": "combinatorial",
            "seed_mode": "progressive",
            "seed": 42,
            "total_combinations": 6
        },
        parameters={
            "width": 512,
            "height": 768,
            "steps": 30,
            "cfg_scale": 7.0,
            "sampler": "DPM++ 2M Karras",
            "batch_size": 1,
            "batch_count": 1
        },
        output_info={
            "folder": "/tmp/test_output",
            "filename_keys": ["Expression", "Angle"]
        }
    )

    print("Generated metadata:")
    print(json.dumps(test_metadata, indent=2))
    print("\n✅ Test completed!")
