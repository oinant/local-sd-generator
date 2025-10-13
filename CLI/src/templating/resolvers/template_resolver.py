"""
Template resolver for Template System V2.0 - Phase 5.

This module handles template resolution with support for:
- Chunk injection (@ChunkName, @chunks.positive)
- Chunk injection with parameters (@{Chunk with Param:{Import[selector]}})
- Selector parsing ([limit], [#indexes], [keys], [$weight])
- Placeholder resolution with selectors ({Placeholder[selectors]})
- Context-based resolution (chunks, defaults, imports)
"""

import re
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Selector:
    """Represents a parsed selector."""
    limit: Optional[int] = None  # [N] - N random variations
    indexes: Optional[List[int]] = None  # [#1,3,5] - Specific indexes
    keys: Optional[List[str]] = None  # [BobCut,LongHair] - Specific keys
    weight: int = 1  # [$W] - Combinatorial weight (default 1)


class TemplateResolver:
    """
    Resolves templates with chunk injection and placeholders.

    Supports:
    - Simple chunk refs: @Character
    - Nested chunk refs: @chunks.positive
    - Chunk with params: @{Character with Angles:{Angle[15]}, Poses:{Pose[$5]}}
    - Placeholder selectors: {Angle[15;$8]} {Haircut[BobCut,LongHair]} {Pose[#1,3,5]}
    """

    # Regex patterns
    # Match @{ChunkName with ...} - we'll parse params manually to handle nested braces
    # This regex just finds the start of chunk-with-params syntax
    CHUNK_WITH_PARAMS_START = re.compile(
        r'@\{(\w+)\s+with\s+'
    )

    # Match @chunks.positive or @ChunkName
    CHUNK_REF_PATTERN = re.compile(
        r'@([\w.]+)'
    )

    # Match {PlaceholderName[selectors]} or {PlaceholderName}
    PLACEHOLDER_PATTERN = re.compile(
        r'\{(\w+)(?:\[([^\]]+)\])?\}'
    )

    def __init__(self, loader=None, parser=None, import_resolver=None):
        """
        Initialize the template resolver.

        Args:
            loader: YamlLoader instance (for loading chunk files)
            parser: ConfigParser instance (for parsing chunks)
            import_resolver: ImportResolver instance (for resolving chunk imports)
        """
        self.loader = loader
        self.parser = parser
        self.import_resolver = import_resolver

    def resolve_template(
        self,
        template: str,
        context: Dict[str, Any],
        skip_chunk_injection: bool = False
    ) -> str:
        """
        Resolve a template with chunk injection and placeholders.

        Args:
            template: Template string to resolve
            context: Resolution context containing:
                - imports: Dict of resolved imports {import_name: {key: value}}
                - chunks: Dict of chunk values {name: value}
                - defaults: Dict of default values {name: value}
                - variation_state: Optional current variation state (for $0 weight)
            skip_chunk_injection: If True, skip chunk injection (already done in Phase 1)

        Returns:
            Resolved template string

        Note:
            Resolution order:
            1. Chunk injection (@ChunkName, @{Chunk with...}) [if not skipped]
            2. Placeholder resolution ({Placeholder[selectors]})
        """
        resolved = template

        # Phase 1: Inject chunks (only if not already done)
        if not skip_chunk_injection:
            resolved = self._inject_chunks_with_params(resolved, context)
            resolved = self._inject_chunk_refs(resolved, context)

        # Phase 2: Resolve placeholders
        resolved = self._resolve_placeholders(resolved, context)

        return resolved

    def _inject_chunks_with_params(
        self,
        template: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Inject chunks with parameter passing.

        Syntax: @{ChunkName with Param1:{Value1[sel]}, Param2:{Value2}}

        Phase 1 behavior:
        - Load chunk template
        - Parse param overrides (e.g., HairCut:{HairCut[#10,12]})
        - Replace placeholders in chunk template with overridden versions
        - Merge chunk imports into parent context
        - Return modified chunk template (placeholders preserved)

        Args:
            template: Template string
            context: Resolution context

        Returns:
            Template with chunks injected (placeholders preserved)
        """
        # Manual parsing to handle nested braces
        result = []
        i = 0

        while i < len(template):
            # Look for @{ChunkName with
            match = self.CHUNK_WITH_PARAMS_START.match(template, i)

            if not match:
                # No match at current position - copy character and continue
                result.append(template[i])
                i += 1
                continue

            # Found @{ChunkName with at position i
            chunk_name = match.group(1)
            params_start = match.end()  # Position after "with "

            # Find matching closing } by counting braces
            depth = 1  # We're inside the outer @{...}
            params_end = params_start

            while params_end < len(template) and depth > 0:
                if template[params_end] == '{':
                    depth += 1
                elif template[params_end] == '}':
                    depth -= 1
                params_end += 1

            if depth != 0:
                # Unmatched braces - skip this match
                result.append(template[i])
                i += 1
                continue

            # Extract params string (everything between "with " and final })
            params_str = template[params_start:params_end-1]  # -1 to exclude final }

            # Load chunk config
            chunk_config = self._load_chunk_config(chunk_name, context)
            chunk_template = chunk_config['template']

            # Merge chunk imports into parent context
            if 'imports' in chunk_config and chunk_config['imports']:
                self._merge_chunk_imports_into_context(chunk_config, context)

            # Parse parameter overrides
            param_overrides = self._parse_chunk_param_overrides(params_str)

            # Apply overrides to chunk template
            modified_template = chunk_template
            for param_name, param_value_str in param_overrides.items():
                modified_template = modified_template.replace(
                    f'{{{param_name}}}',
                    param_value_str
                )

            # Append modified chunk template to result
            result.append(modified_template)

            # Move past this chunk reference
            i = params_end

        return ''.join(result)

    def _inject_chunk_refs(
        self,
        template: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Inject simple chunk references.

        Supports:
        - @ChunkName (simple reference)
        - @chunks.positive (nested import reference)

        Phase 1 behavior (structural resolution):
        - Inject chunk template with placeholders UNRESOLVED
        - Merge chunk imports into parent context
        - Do NOT resolve placeholders yet (that's Phase 2)

        Args:
            template: Template string
            context: Resolution context

        Returns:
            Template with chunk refs injected (placeholders preserved)
        """
        def replace_ref(match):
            ref = match.group(1)  # e.g., "Character" or "chunks.positive"

            if '.' in ref:
                # Nested reference: @chunks.positive
                return self._resolve_nested_chunk_ref(ref, context)
            else:
                # Simple reference: @ChunkName
                # Load chunk config
                chunk_config = self._load_chunk_config(ref, context)
                chunk_template = chunk_config['template']

                # Merge chunk imports into parent context (so placeholders are available)
                if 'imports' in chunk_config and chunk_config['imports']:
                    self._merge_chunk_imports_into_context(chunk_config, context)

                # Return chunk template with placeholders UNRESOLVED
                # Phase 2 (generator) will resolve them
                return chunk_template

        return self.CHUNK_REF_PATTERN.sub(replace_ref, template)

    def _resolve_placeholders(
        self,
        template: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Resolve placeholders with optional selectors.

        Syntax: {PlaceholderName[selectors]} or {PlaceholderName}

        Phase 2 behavior (called by generator for each variation):
        - Use context['chunks'] (variation_state) if available
        - Fall back to applying selectors and choosing first value

        Args:
            template: Template string
            context: Resolution context

        Returns:
            Template with placeholders resolved
        """
        def replace_placeholder(match):
            name = match.group(1)
            selector_str = match.group(2)  # May be None

            # Check if we have a value already resolved in chunks (from generator)
            # This happens when generator has already picked specific values
            # (e.g., for weight 0 random selection, or combinatorial loops)
            chunks = context.get('chunks', {})
            if name in chunks:
                # Value already resolved by generator - use it directly
                return str(chunks[name])

            # When a selector is present, use imports to apply selection
            # This allows chunk param overrides like {HairCut[#10,12]} to work
            if selector_str:
                # Get from imports only (skip chunks since we already checked above)
                imports = context.get('imports', {})
                if name in imports:
                    import_data = imports[name]
                    if isinstance(import_data, dict) and 'template' not in import_data:
                        # It's a variations dict - apply selector
                        selector = self._parse_selectors(selector_str)
                        selected_values = self._apply_selector(import_data, selector, context)
                        return selected_values[0] if selected_values else ""

            # No selector OR not found in imports - use normal priority
            value = self._get_placeholder_value(name, context)

            # If value is dict (import reference), need to resolve to a specific value
            if isinstance(value, dict):
                if selector_str:
                    selector = self._parse_selectors(selector_str)
                    selected_values = self._apply_selector(value, selector, context)
                    return selected_values[0] if selected_values else ""
                else:
                    # No selector - return first value
                    return list(value.values())[0] if value else ""

            # Value is a string (from chunks/defaults or direct value) - return as-is
            return str(value) if value is not None else ""

        return self.PLACEHOLDER_PATTERN.sub(replace_placeholder, template)

    def _parse_chunk_param_overrides(
        self,
        params_str: str
    ) -> Dict[str, str]:
        """
        Parse chunk parameter overrides from "Param1:{Value1[sel]}, Param2:{Value2}" format.

        Returns RAW value strings (with selectors preserved), not resolved.

        Args:
            params_str: Parameters string

        Returns:
            Dict mapping parameter names to raw value strings (e.g., {HairCut: '{HairCut[#10,12]}'})
        """
        params = {}

        # Split by commas (outside of braces)
        parts = self._split_params(params_str)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Parse "ParamName:{Value[selectors]}"
            if ':' not in part:
                continue

            param_name, value_str = part.split(':', 1)
            param_name = param_name.strip()
            value_str = value_str.strip()

            # Store RAW value string (do NOT resolve)
            params[param_name] = value_str

        return params

    def _parse_chunk_params(
        self,
        params_str: str,
        context: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Parse chunk parameters from "Param1:{Value1[sel]}, Param2:{Value2}" format.

        DEPRECATED: Use _parse_chunk_param_overrides() for Phase 1.

        Args:
            params_str: Parameters string
            context: Resolution context

        Returns:
            Dict mapping parameter names to resolved values
        """
        params = {}

        # Split by commas (outside of braces)
        parts = self._split_params(params_str)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Parse "ParamName:{Value[selectors]}"
            if ':' not in part:
                continue

            param_name, value_str = part.split(':', 1)
            param_name = param_name.strip()
            value_str = value_str.strip()

            # Resolve the value (may contain placeholder with selector)
            resolved_value = self._resolve_placeholders(value_str, context)
            params[param_name] = resolved_value

        return params

    def _split_params(self, params_str: str) -> List[str]:
        """
        Split parameters by comma, respecting nested braces and brackets.

        Args:
            params_str: Parameters string

        Returns:
            List of parameter strings
        """
        parts = []
        current = []
        depth = 0

        for char in params_str:
            if char in '{[':
                depth += 1
                current.append(char)
            elif char in '}]':
                depth -= 1
                current.append(char)
            elif char == ',' and depth == 0:
                parts.append(''.join(current))
                current = []
            else:
                current.append(char)

        if current:
            parts.append(''.join(current))

        return parts

    def _load_chunk_config(
        self,
        chunk_name: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Load chunk config with full metadata (template + imports).

        Args:
            chunk_name: Name of chunk to load
            context: Resolution context

        Returns:
            Dict containing chunk data (template, imports, etc.)

        Raises:
            ValueError: If chunk not found in imports
        """
        imports = context.get('imports', {})

        if chunk_name not in imports:
            raise ValueError(f"Chunk '{chunk_name}' not found in imports")

        chunk_data = imports[chunk_name]

        # chunk_data should be a dict with 'template' and 'imports' fields
        # (loaded by import_resolver when it's a .chunk.yaml file)
        if isinstance(chunk_data, dict):
            return chunk_data

        # If it's a string, wrap it as a simple template
        if isinstance(chunk_data, str):
            return {'template': chunk_data, 'imports': {}}

        raise ValueError(f"Invalid chunk data for '{chunk_name}'")

    def _merge_chunk_imports_into_context(
        self,
        chunk_config: Dict[str, Any],
        parent_context: Dict[str, Any]
    ) -> None:
        """
        Merge chunk imports into parent context (in-place).

        This allows chunk placeholders to be resolved in Phase 2.

        Args:
            chunk_config: Chunk config dict (with 'imports' field)
            parent_context: Parent resolution context (modified in-place)
        """
        # Resolve chunk imports if present
        if 'imports' in chunk_config and chunk_config['imports']:
            # Use import_resolver to resolve chunk imports
            if self.import_resolver:
                # Create a temporary config-like object with imports
                class TempConfig:
                    def __init__(self, imports_dict):
                        self.imports = imports_dict

                temp_config = TempConfig(chunk_config['imports'])

                # Resolve using chunk's base path (if available)
                base_path = chunk_config.get('base_path')
                if base_path:
                    resolved_imports = self.import_resolver.resolve_imports(
                        temp_config,
                        base_path
                    )
                    # Merge into parent context (child overrides parent)
                    parent_context['imports'].update(resolved_imports)

    def _build_chunk_context(
        self,
        chunk_config: Dict[str, Any],
        parent_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build resolution context for a chunk with its own imports.

        DEPRECATED: Use _merge_chunk_imports_into_context() instead for Phase 1.

        Args:
            chunk_config: Chunk config dict (with 'imports' field)
            parent_context: Parent resolution context

        Returns:
            New context with chunk's imports resolved
        """
        # Start with empty context
        chunk_context = {
            'imports': {},
            'chunks': parent_context.get('chunks', {}),
            'defaults': chunk_config.get('defaults', {}),
            'variation_state': parent_context.get('variation_state', {})
        }

        # Resolve chunk imports if present
        if 'imports' in chunk_config and chunk_config['imports']:
            # Use import_resolver to resolve chunk imports
            if self.import_resolver:
                # Create a temporary config-like object with imports
                # import_resolver.resolve_imports expects a config with .imports attr
                class TempConfig:
                    def __init__(self, imports_dict):
                        self.imports = imports_dict

                temp_config = TempConfig(chunk_config['imports'])

                # Resolve using chunk's base path (if available)
                base_path = chunk_config.get('base_path', parent_context.get('base_path'))
                if base_path:
                    resolved_imports = self.import_resolver.resolve_imports(
                        temp_config,
                        base_path
                    )
                    chunk_context['imports'] = resolved_imports

        return chunk_context

    def _get_chunk_template(
        self,
        chunk_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Get chunk template from imports.

        DEPRECATED: Use _load_chunk_config() instead for full chunk support.

        Args:
            chunk_name: Name of chunk to load
            context: Resolution context

        Returns:
            Chunk template string

        Raises:
            ValueError: If chunk not found in imports
        """
        chunk_config = self._load_chunk_config(chunk_name, context)
        return chunk_config['template']

    def _resolve_nested_chunk_ref(
        self,
        ref: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Resolve nested chunk reference like "chunks.positive".

        Args:
            ref: Nested reference (e.g., "chunks.positive")
            context: Resolution context

        Returns:
            Resolved chunk template
        """
        parts = ref.split('.')
        imports = context.get('imports', {})

        # Navigate nested structure
        current = imports
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise ValueError(f"Nested reference '{ref}' not found in imports")

        # Current should now be the chunk data
        if isinstance(current, dict) and 'template' in current:
            chunk_template = current['template']
            # Recursively resolve
            return self.resolve_template(chunk_template, context)
        elif isinstance(current, str):
            return current
        else:
            raise ValueError(f"Invalid nested chunk data for '{ref}'")

    def _get_placeholder_value(
        self,
        name: str,
        context: Dict[str, Any]
    ) -> Any:
        """
        Get placeholder value from context.

        Priority order:
        1. chunks: (specific values)
        2. defaults: (default values)
        3. imports: (variation dict)

        Args:
            name: Placeholder name
            context: Resolution context

        Returns:
            Value (str or dict)
        """
        # Priority 1: chunks
        chunks = context.get('chunks', {})
        if name in chunks:
            return chunks[name]

        # Priority 2: defaults
        defaults = context.get('defaults', {})
        if name in defaults:
            return defaults[name]

        # Priority 3: imports (returns dict of variations)
        imports = context.get('imports', {})
        if name in imports:
            return imports[name]

        # Not found - return None (will be replaced with empty string)
        return None

    def _parse_selectors(self, selector_str: str) -> Selector:
        """
        Parse selector string into Selector object.

        Supports:
        - [15] - Limit to 15 random variations
        - [#1,3,5] - Select index 1, 3, 5
        - [BobCut,LongHair] - Select by keys
        - [$8] - Weight 8 for combinatorial
        - [15;$8] - Combination (semicolon separator)

        Args:
            selector_str: Selector string (without brackets)

        Returns:
            Selector object
        """
        selector = Selector()

        # Split by semicolon for multiple selectors
        parts = [p.strip() for p in selector_str.split(';')]

        for part in parts:
            if not part:
                continue

            # Weight selector: $8
            if part.startswith('$'):
                try:
                    selector.weight = int(part[1:])
                except ValueError:
                    pass  # Ignore invalid weight
                continue

            # Index selector: #1,3,5
            if part.startswith('#'):
                index_str = part[1:]
                try:
                    indexes = [int(i.strip()) for i in index_str.split(',')]
                    selector.indexes = indexes
                except ValueError:
                    pass  # Ignore invalid indexes
                continue

            # Limit selector: 15 (pure number)
            if part.isdigit():
                selector.limit = int(part)
                continue

            # Key selector: BobCut,LongHair (contains letters/commas)
            if ',' in part or part[0].isupper():
                keys = [k.strip() for k in part.split(',')]
                selector.keys = keys
                continue

        return selector

    def _apply_selector(
        self,
        variations: Dict[str, str],
        selector: Selector,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Apply selector to variations dict.

        Args:
            variations: Dict of variations {key: value}
            selector: Parsed selector
            context: Resolution context (for random seed if needed)

        Returns:
            List of selected variation values
        """
        # Start with all variations
        keys = list(variations.keys())
        values = list(variations.values())

        # Apply index selector first (most specific)
        if selector.indexes is not None:
            selected_values = []
            for idx in selector.indexes:
                if 0 <= idx < len(values):
                    selected_values.append(values[idx])
            return selected_values if selected_values else values

        # Apply key selector
        if selector.keys is not None:
            selected_values = []
            for key in selector.keys:
                if key in variations:
                    selected_values.append(variations[key])
            return selected_values if selected_values else values

        # Apply limit selector
        if selector.limit is not None:
            if selector.limit >= len(values):
                return values
            # Random selection
            return random.sample(values, selector.limit)

        # No selector - return all
        return values

    def extract_weights(self, template: str) -> Dict[str, int]:
        """
        Extract all weights from placeholders in template.

        Used by combinatorial generator to determine loop order.

        Args:
            template: Template string

        Returns:
            Dict mapping placeholder names to weights
        """
        weights = {}

        for match in self.PLACEHOLDER_PATTERN.finditer(template):
            name = match.group(1)
            selector_str = match.group(2)

            if selector_str:
                selector = self._parse_selectors(selector_str)
                weights[name] = selector.weight
            else:
                weights[name] = 1  # Default weight

        return weights

    def _inject_all_chunks_phase1(
        self,
        template: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Phase 1: Inject all chunks structurally (preserving placeholders).

        This method:
        1. Injects chunks with parameters (@{Chunk with Param:...})
        2. Injects simple chunk refs (@ChunkName)
        3. Merges chunk imports into context
        4. Does NOT resolve any placeholders

        Called by orchestrator.resolve() during Phase 1.

        Args:
            template: Template string with chunk refs
            context: Resolution context

        Returns:
            Template with chunks injected but placeholders preserved
        """
        # Inject chunks with params first
        resolved = self._inject_chunks_with_params(template, context)

        # Then inject simple chunk refs
        resolved = self._inject_chunk_refs(resolved, context)

        return resolved
