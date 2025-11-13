"""PromptGenerator - generates prompts and provides statistics."""

from typing import Optional, Any

from ..templating.orchestrator import V2Pipeline
from .session_config import SessionConfig
from .session_event_collector import SessionEventCollector
from .event_types import EventType


class PromptGenerator:
    """Generates prompts from resolved template and provides statistics.

    This class handles:
    - Prompt generation via V2Pipeline
    - Variation statistics calculation and formatting
    - Count limiting
    - Event emission for progress tracking

    Example:
        >>> generator = PromptGenerator(pipeline, events)
        >>> prompts, stats = generator.generate_with_stats(
        ...     session_config=config,
        ...     context=context,
        ...     resolved_config=resolved_config
        ... )
    """

    def __init__(
        self,
        pipeline: V2Pipeline,
        events: SessionEventCollector
    ):
        """Initialize prompt generator.

        Args:
            pipeline: V2Pipeline instance for prompt generation
            events: Event collector for output management
        """
        self.pipeline = pipeline
        self.events = events

    def generate_with_stats(
        self,
        session_config: SessionConfig,
        context: Any,  # ResolvedContext
        resolved_config: Any  # ResolvedConfig
    ) -> tuple[list[dict], dict]:
        """Generate prompts and return with statistics.

        This is the main entry point that:
        1. Generates prompts via pipeline
        2. Calculates variation statistics
        3. Applies count limit if specified
        4. Emits progress events

        Args:
            session_config: Session configuration
            context: Resolved context (from V2Pipeline.resolve())
            resolved_config: Resolved config (from V2Pipeline.resolve())

        Returns:
            Tuple of (prompts, stats):
            - prompts: List of prompt dicts
            - stats: Statistics dict with placeholders info
        """
        # Emit start event
        self.events.emit(EventType.PROMPT_GENERATION_START)

        # Generate prompts
        prompts = self.pipeline.generate(resolved_config, context)

        # Calculate statistics
        template_str = resolved_config.template if resolved_config.template else ""
        stats = self.pipeline.get_variation_statistics(template_str, context)

        # Emit stats event for display
        if stats['total_placeholders'] > 0:
            # Format stats for display
            formatted_stats = self.format_stats_for_display(
                stats=stats,
                num_images=len(prompts),
                gen_mode=session_config.generation_mode
            )
            self.events.emit(
                EventType.PROMPT_STATS,
                {"stats": stats, "formatted": formatted_stats}
            )
        else:
            # No placeholders detected
            self.events.emit(
                EventType.WARNING,
                {"message": "No placeholders detected in template"}
            )

        # Apply count limit if specified
        if session_config.total_images and len(prompts) > session_config.total_images:
            original_count = len(prompts)
            prompts = self.apply_count_limit(prompts, session_config.total_images)
            self.events.emit(
                EventType.INFO,
                {"message": f"Limiting to {session_config.total_images} prompts (from {original_count})"}
            )

        return prompts, stats

    def format_stats_for_display(
        self,
        stats: dict,
        num_images: int,
        gen_mode: str
    ) -> str:
        """Format statistics for display.

        Creates a formatted string with:
        - Placeholder counts
        - Multi-source indicators
        - Total combinations
        - Generation mode
        - Number of images to generate

        Args:
            stats: Statistics dict from pipeline
            num_images: Number of images to generate
            gen_mode: Generation mode ("combinatorial" or "random")

        Returns:
            Formatted statistics string
        """
        lines = []

        # Add placeholder details
        for placeholder_name, placeholder_info in stats['placeholders'].items():
            count_str = f"{placeholder_info['count']} variations"
            if placeholder_info['is_multi_source']:
                count_str += f" ({placeholder_info['sources']} files merged)"
            lines.append(f"  {placeholder_name}: {count_str}")

        # Add total combinations
        total_comb = stats['total_combinations']
        if total_comb > 1_000_000:
            total_str = f"{total_comb:,}"
        else:
            total_str = str(total_comb)

        lines.append("")
        lines.append(f"  Total combinations: {total_str}")

        # Add generation info
        lines.append(f"  Generation mode: {gen_mode}")
        lines.append(f"  Will generate: {num_images} images")

        return "\n".join(lines)

    def apply_count_limit(
        self,
        prompts: list[dict],
        count_limit: Optional[int]
    ) -> list[dict]:
        """Apply count limit to prompts list.

        Args:
            prompts: List of prompt dicts
            count_limit: Optional limit (None = no limit)

        Returns:
            Limited prompts list
        """
        if count_limit is None:
            return prompts

        if len(prompts) <= count_limit:
            return prompts

        return prompts[:count_limit]
