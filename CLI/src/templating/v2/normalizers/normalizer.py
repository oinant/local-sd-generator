"""
Prompt normalizer for Template System V2.0 - Phase 6.

This module implements prompt normalization according to spec section 8.
Normalization is applied AFTER template resolution (all placeholders replaced).

Normalization rules (applied in order):
1. Trim whitespace at start/end of each line
2. Collapse multiple commas into single comma
3. Remove orphan commas at start/end of lines
4. Normalize spacing around commas (no space before, one space after)
5. Preserve maximum 1 blank line between content
"""

import re


class PromptNormalizer:
    """
    Normalizes resolved prompts according to V2.0 spec section 8.

    Applies 5 normalization rules to ensure consistent prompt formatting
    for Stable Diffusion API.
    """

    def normalize_prompt(self, prompt: str) -> str:
        """
        Normalize a resolved prompt string.

        Applies all 5 normalization rules from spec section 8.1:
        1. Trim whitespace at start/end of lines (but preserve structure)
        2. Collapse multiple commas
        3. Remove orphan commas (lines with only commas)
        4. Normalize spacing around commas (", " format)
        5. Preserve max 1 blank line

        Args:
            prompt: Resolved prompt string (after template resolution)

        Returns:
            Normalized prompt string

        Example:
            >>> normalizer = PromptNormalizer()
            >>> normalizer.normalize_prompt("  1girl,, beautiful  ")
            "1girl, beautiful"
        """
        if not prompt or not prompt.strip():
            return ""

        # Rule 2: Collapse multiple commas (do this first)
        normalized = self._collapse_commas(prompt)

        # Rule 3: Remove orphan commas (lines with only comma/whitespace)
        normalized = self._remove_orphan_commas(normalized)

        # Rule 4: Normalize spacing around commas (", " format, preserves trailing)
        normalized = self._normalize_spacing(normalized)

        # Rule 1: Trim whitespace at start/end of lines (but preserve trailing ", ")
        normalized = self._trim_whitespace(normalized)

        # Rule 5: Preserve max 1 blank line
        normalized = self._preserve_max_one_blank_line(normalized)

        # Final cleanup: trim the entire result
        return normalized.strip()

    def _trim_whitespace(self, text: str) -> str:
        """
        Trim whitespace at start and end of each line.

        Rule 1: "  1girl, beautiful  " → "1girl, beautiful"

        IMPORTANT: Preserves trailing ", " (comma + space) for SD compatibility.

        Args:
            text: Input text

        Returns:
            Text with trimmed lines (preserving trailing ", ")
        """
        lines = text.split('\n')
        trimmed_lines = []

        for line in lines:
            # Check if line ends with ", " before trimming
            has_trailing_comma = line.rstrip().endswith(',')

            # Trim the line
            trimmed = line.strip()

            # Restore trailing ", " if it was present
            if has_trailing_comma and trimmed and not trimmed.endswith(','):
                trimmed += ','

            trimmed_lines.append(trimmed)

        return '\n'.join(trimmed_lines)

    def _collapse_commas(self, text: str) -> str:
        """
        Collapse multiple commas (with optional spaces) into single comma.

        Rule 2: "1girl,, beautiful" → "1girl, beautiful"
                "1girl, , beautiful" → "1girl, beautiful"

        Args:
            text: Input text

        Returns:
            Text with collapsed commas
        """
        # Replace sequences of comma+spaces with single comma+space
        # Handles: ,, or , , or ,,, etc.
        collapsed = re.sub(r',(\s*,)+', ',', text)
        return collapsed

    def _remove_orphan_commas(self, text: str) -> str:
        """
        Remove orphan commas (lines containing only commas/whitespace).

        Rule 3: Orphan = a line with ONLY comma(s) and/or whitespace.
        Also removes leading commas from start of text and trailing from end.

        Examples:
        - ", 1girl" → "1girl" (leading orphan)
        - "1girl,\n,\ndetailed" → "1girl,\n\ndetailed" (middle orphan line)
        - "1girl,\ndetailed" → "1girl,\ndetailed" (NOT orphan, intentional SD formatting)

        Args:
            text: Input text

        Returns:
            Text with orphan commas removed
        """
        # Remove lines that contain ONLY commas and whitespace
        # This handles empty placeholders: "text,\n,\ntext" → "text,\n\ntext"
        # Match comma-only lines but preserve the surrounding newlines
        lines = text.split('\n')
        cleaned_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            # If line is only commas/whitespace, replace with empty string
            # This preserves the line (for blank line preservation)
            if stripped == '' or stripped == ',':
                cleaned_lines.append('')
            else:
                cleaned_lines.append(line)

        text = '\n'.join(cleaned_lines)

        # Remove leading comma from very start of text
        text = re.sub(r'^\s*,\s*', '', text)

        # Remove trailing comma from very end of text (after final content)
        text = re.sub(r'\s*,\s*$', '', text)

        return text

    def _normalize_spacing(self, text: str) -> str:
        """
        Normalize spacing around commas: no space before, one space after.

        Rule 4: "1girl,beautiful" → "1girl, beautiful"
                "1girl , beautiful" → "1girl, beautiful"

        Args:
            text: Input text

        Returns:
            Text with normalized comma spacing
        """
        # Remove all spaces before commas
        normalized = re.sub(r'\s+,', ',', text)

        # Ensure exactly one space after commas (unless at end of line or string)
        # Use negative lookahead to avoid adding space before newline
        normalized = re.sub(r',(?!\n)(?! )', ', ', normalized)

        # Remove extra spaces after commas (but preserve single space)
        normalized = re.sub(r',  +', ', ', normalized)

        return normalized

    def _preserve_max_one_blank_line(self, text: str) -> str:
        """
        Preserve maximum 1 blank line between content.

        Rule 5: "1girl,\n\n\ndetailed" → "1girl,\n\ndetailed"

        A blank line = two consecutive newlines (\n\n)
        Multiple blank lines = three or more newlines (\n\n\n+)

        Args:
            text: Input text

        Returns:
            Text with max 1 blank line preserved
        """
        # Replace 3+ newlines with exactly 2 newlines (= 1 blank line)
        # \n\n = 1 blank line (preserve)
        # \n\n\n+ = multiple blank lines (collapse to \n\n)
        normalized = re.sub(r'\n{3,}', '\n\n', text)
        return normalized
