"""
Text chunk loading and resolution.

Chunks are reusable text templates with parameters that can be filled by:
- Chunk-specific field values
- Multi-field variations
- Inline overrides

This is pure text composition - no complex logic, just placeholder substitution.
"""

from pathlib import Path
from typing import Dict
import yaml
import re

from .types import ChunkTemplate, Chunk, FieldDefinition


def load_chunk_template(filepath: Path, base_path: Path = None) -> ChunkTemplate:
    """
    Load a chunk template from a .chunk.template.yaml file.

    The template defines:
    - output: text with {field_path} placeholders (e.g., {appearance.skin})
    - fields: available fields with metadata (for validation)

    Args:
        filepath: Path to template file
        base_path: Base directory for resolving relative paths

    Returns:
        ChunkTemplate object
    """
    if base_path:
        filepath = base_path / filepath

    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    expected_type = data.get('type')
    if expected_type not in ['chunk_template', 'character_template']:
        raise ValueError(
            f"Expected type 'chunk_template' or 'character_template', got '{expected_type}'"
        )

    # Parse fields structure (nested categories)
    fields_data = data.get('fields', {})
    fields = {}

    for category, category_fields in fields_data.items():
        if isinstance(category_fields, dict):
            fields[category] = {}
            for field_name, field_spec in category_fields.items():
                if isinstance(field_spec, dict):
                    fields[category][field_name] = FieldDefinition(
                        type=field_spec.get('type', 'text'),
                        description=field_spec.get('description', ''),
                        required=field_spec.get('required', False),
                        default=field_spec.get('default'),
                        example=field_spec.get('example')
                    )

    return ChunkTemplate(
        name=data.get('name', ''),
        type='chunk_template',  # Normalize
        version=data.get('version', '1.0'),
        description=data.get('description', ''),
        output=data.get('output', ''),
        fields=fields,
        metadata=data.get('metadata', {})
    )


def load_chunk(filepath: Path, base_path: Path = None) -> Chunk:
    """
    Load a chunk from a .chunk.yaml file.

    Args:
        filepath: Path to chunk file
        base_path: Base directory for resolving relative paths

    Returns:
        Chunk object
    """
    if base_path:
        filepath = base_path / filepath

    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    expected_type = data.get('type')
    if expected_type not in ['chunk', 'character']:
        raise ValueError(f"Expected type 'chunk' or 'character', got '{expected_type}'")

    # Parse fields structure (nested categories)
    fields_data = data.get('fields', {})
    fields = {}

    for category, category_fields in fields_data.items():
        if isinstance(category_fields, dict):
            fields[category] = {}
            for field_name, value in category_fields.items():
                fields[category][field_name] = str(value) if value is not None else ""

    return Chunk(
        name=data.get('name', ''),
        type='chunk',  # Normalize
        version=data.get('version', '1.0'),
        implements=data.get('implements'),
        fields=fields,
        metadata=data.get('metadata', {})
    )


def resolve_chunk_fields(
    chunk: Chunk,
    template: ChunkTemplate,
    additional_fields: Dict[str, Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Resolve chunk fields into a flat {field_path: value} dict ready for rendering.

    Priority (highest to lowest):
    1. additional_fields (from multi-field expansion or inline overrides)
    2. chunk.fields (chunk-specific values)
    3. template field defaults

    Args:
        chunk: Chunk instance
        template: Chunk template
        additional_fields: Additional fields to merge (nested dict)

    Returns:
        Flat dict like {"appearance.skin": "dark skin", "identity.name": "Emma"}
    """
    result = {}

    # 1. Start with template defaults
    for category, category_fields in template.fields.items():
        for field_name, field_def in category_fields.items():
            if field_def.default:
                result[f"{category}.{field_name}"] = field_def.default

    # 2. Apply chunk fields
    for category, category_fields in chunk.fields.items():
        for field_name, value in category_fields.items():
            if value:  # Only non-empty
                result[f"{category}.{field_name}"] = value

    # 3. Apply additional fields (highest priority)
    if additional_fields:
        for category, category_fields in additional_fields.items():
            for field_name, value in category_fields.items():
                if value:
                    result[f"{category}.{field_name}"] = value

    return result


def render_chunk(
    template: ChunkTemplate,
    resolved_fields: Dict[str, str]
) -> str:
    """
    Render chunk by replacing {field_path} placeholders in template.output.

    Args:
        template: Chunk template with output string
        resolved_fields: Flat dict of field values

    Returns:
        Rendered text with placeholders replaced and cleaned up

    Example:
        template.output = "{identity.name}, {appearance.age}\\n{appearance.skin}"
        resolved_fields = {"identity.name": "Emma", "appearance.age": "23", "appearance.skin": "dark skin"}
        Result: "Emma, 23 years old\\ndark skin"
    """
    output = template.output

    # Replace {category.field} placeholders
    def replace_placeholder(match):
        placeholder = match.group(1)  # e.g., "appearance.skin"
        return resolved_fields.get(placeholder, "")

    result = re.sub(r'\{([a-zA-Z_]+\.[a-zA-Z_]+)\}', replace_placeholder, output)

    # Clean up: remove empty lines, extra commas/spaces
    lines = [line.strip() for line in result.split('\n')]
    lines = [line for line in lines if line]  # Remove empty lines

    result = '\n'.join(lines)
    result = re.sub(r',\s*,+', ',', result)  # ", , " -> ","
    result = re.sub(r'\s+', ' ', result)  # Normalize spaces within lines
    result = re.sub(r',\s*$', '', result, flags=re.MULTILINE)  # Trailing commas

    return result.strip()
