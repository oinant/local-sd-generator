"""Unit tests for PromptGenerator (TDD approach)."""

from pathlib import Path
from unittest.mock import Mock, MagicMock
import pytest

from sd_generator_cli.orchestrator.prompt_generator import PromptGenerator
from sd_generator_cli.orchestrator.session_config import SessionConfig
from sd_generator_cli.orchestrator.session_event_collector import SessionEventCollector
from sd_generator_cli.templating.models.config_models import PromptConfig, GenerationConfig


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_events():
    """Mock SessionEventCollector."""
    return Mock(spec=SessionEventCollector)


@pytest.fixture
def mock_pipeline():
    """Mock V2Pipeline."""
    pipeline = MagicMock()

    # Mock generate() to return sample prompts
    pipeline.generate.return_value = [
        {
            "prompt": "a person with blonde hair and blue eyes",
            "negative_prompt": "low quality",
            "seed": 42,
            "variations": {"Hair": "blonde", "Eyes": "blue"}
        },
        {
            "prompt": "a person with brunette hair and green eyes",
            "negative_prompt": "low quality",
            "seed": 43,
            "variations": {"Hair": "brunette", "Eyes": "green"}
        },
        {
            "prompt": "a person with red hair and blue eyes",
            "negative_prompt": "low quality",
            "seed": 44,
            "variations": {"Hair": "red", "Eyes": "blue"}
        }
    ]

    # Mock get_variation_statistics()
    pipeline.get_variation_statistics.return_value = {
        "total_placeholders": 2,
        "total_combinations": 6,
        "placeholders": {
            "Hair": {
                "count": 3,
                "is_multi_source": False,
                "sources": 1
            },
            "Eyes": {
                "count": 2,
                "is_multi_source": False,
                "sources": 1
            }
        }
    }

    return pipeline


@pytest.fixture
def generator(mock_pipeline, mock_events):
    """PromptGenerator instance."""
    return PromptGenerator(mock_pipeline, mock_events)


@pytest.fixture
def minimal_session_config(tmp_path):
    """Minimal SessionConfig for testing."""
    prompt_config = PromptConfig(
        version="2.0",
        source_file=Path("test.yaml"),
        name="test",
        prompt="a person with {Hair} hair and {Eyes} eyes",
        generation=GenerationConfig(mode="combinatorial", seed_mode="fixed", seed=42, max_images=10)
    )
    return SessionConfig(
        session_name="test_session",
        output_dir=tmp_path,
        template_path=Path("test.yaml"),
        prompt_config=prompt_config,
        total_images=10,
        generation_mode="combinatorial",
        seed_mode="fixed",
        base_seed=42,
        api_url="http://localhost:7860"
    )


@pytest.fixture
def mock_context():
    """Mock ResolvedContext."""
    return MagicMock()


@pytest.fixture
def mock_resolved_config():
    """Mock ResolvedConfig."""
    config = MagicMock()
    config.template = "a person with {Hair} hair and {Eyes} eyes"
    return config


# ============================================================================
# Test: generate_with_stats
# ============================================================================


class TestGenerateWithStats:
    """Test prompt generation with statistics."""

    def test_generates_prompts_and_returns_stats(
        self,
        generator,
        minimal_session_config,
        mock_context,
        mock_resolved_config,
        mock_pipeline
    ):
        """Generates prompts and returns with statistics."""
        prompts, stats = generator.generate_with_stats(
            session_config=minimal_session_config,
            context=mock_context,
            resolved_config=mock_resolved_config
        )

        # Should call pipeline.generate()
        mock_pipeline.generate.assert_called_once_with(mock_resolved_config, mock_context)

        # Should return prompts
        assert len(prompts) == 3
        assert prompts[0]["prompt"] == "a person with blonde hair and blue eyes"

        # Should return stats
        assert stats["total_placeholders"] == 2
        assert stats["total_combinations"] == 6

    def test_applies_count_limit_when_specified(
        self,
        generator,
        mock_context,
        mock_resolved_config,
        mock_pipeline
    ):
        """Applies count limit to generated prompts."""
        # Create session config with total_images=2 (limit)
        session_config = SessionConfig(
            session_name="test",
            output_dir=Path("/tmp"),
            template_path=Path("test.yaml"),
            prompt_config=PromptConfig(
                version="2.0",
                source_file=Path("test.yaml"),
                name="test",
                prompt="test",
                generation=GenerationConfig(mode="combinatorial", seed_mode="fixed", seed=42, max_images=2)
            ),
            total_images=2,  # Limit to 2
            generation_mode="combinatorial",
            seed_mode="fixed",
            api_url="http://localhost:7860"
        )

        prompts, stats = generator.generate_with_stats(
            session_config=session_config,
            context=mock_context,
            resolved_config=mock_resolved_config
        )

        # Should limit to 2 prompts (from 3 generated)
        assert len(prompts) == 2

    def test_emits_prompt_generation_events(
        self,
        generator,
        minimal_session_config,
        mock_context,
        mock_resolved_config,
        mock_events
    ):
        """Emits PROMPT_GENERATION_START and PROMPT_STATS events."""
        generator.generate_with_stats(
            session_config=minimal_session_config,
            context=mock_context,
            resolved_config=mock_resolved_config
        )

        # Should emit multiple events
        assert mock_events.emit.call_count >= 2

        # Check event types (at least PROMPT_GENERATION_START and PROMPT_STATS)
        call_args_list = mock_events.emit.call_args_list
        event_types = [str(call) for call in call_args_list]
        assert any("PROMPT_GENERATION_START" in event for event in event_types)
        assert any("PROMPT_STATS" in event for event in event_types)

    def test_handles_no_placeholders_detected(
        self,
        generator,
        minimal_session_config,
        mock_context,
        mock_resolved_config,
        mock_pipeline,
        mock_events
    ):
        """Handles templates with no placeholders."""
        # Mock stats with no placeholders
        mock_pipeline.get_variation_statistics.return_value = {
            "total_placeholders": 0,
            "total_combinations": 1,
            "placeholders": {}
        }

        prompts, stats = generator.generate_with_stats(
            session_config=minimal_session_config,
            context=mock_context,
            resolved_config=mock_resolved_config
        )

        # Should still return prompts
        assert len(prompts) == 3
        assert stats["total_placeholders"] == 0

        # Should emit WARNING or INFO about no placeholders
        warning_calls = [call for call in mock_events.emit.call_args_list
                        if "WARNING" in str(call) or "INFO" in str(call)]
        assert len(warning_calls) > 0


# ============================================================================
# Test: format_stats_for_display (helper method)
# ============================================================================


class TestFormatStatsForDisplay:
    """Test statistics formatting for display."""

    def test_formats_stats_with_all_info(self, generator):
        """Formats stats with placeholder details."""
        stats = {
            "total_placeholders": 2,
            "total_combinations": 6,
            "placeholders": {
                "Hair": {"count": 3, "is_multi_source": False, "sources": 1},
                "Eyes": {"count": 2, "is_multi_source": False, "sources": 1}
            }
        }

        formatted = generator.format_stats_for_display(stats, num_images=3, gen_mode="combinatorial")

        # Should include placeholder counts
        assert "Hair" in formatted
        assert "3 variations" in formatted
        assert "Eyes" in formatted
        assert "2 variations" in formatted

        # Should include total combinations
        assert "6" in formatted

        # Should include generation info
        assert "combinatorial" in formatted
        assert "3 images" in formatted

    def test_formats_large_combinations_with_commas(self, generator):
        """Formats large combination numbers with commas."""
        stats = {
            "total_placeholders": 1,
            "total_combinations": 1_500_000,
            "placeholders": {"Test": {"count": 1500000, "is_multi_source": False, "sources": 1}}
        }

        formatted = generator.format_stats_for_display(stats, num_images=100, gen_mode="random")

        # Should format large numbers with commas
        assert "1,500,000" in formatted

    def test_indicates_multi_source_placeholders(self, generator):
        """Indicates when placeholders are from multiple sources."""
        stats = {
            "total_placeholders": 1,
            "total_combinations": 10,
            "placeholders": {
                "Hair": {"count": 10, "is_multi_source": True, "sources": 3}
            }
        }

        formatted = generator.format_stats_for_display(stats, num_images=10, gen_mode="combinatorial")

        # Should indicate multi-source
        assert "3 files merged" in formatted or "merged" in formatted.lower()


# ============================================================================
# Test: apply_count_limit (helper method)
# ============================================================================


class TestApplyCountLimit:
    """Test count limiting logic."""

    def test_limits_prompts_when_count_specified(self, generator):
        """Limits prompts to specified count."""
        prompts = [{"prompt": f"test {i}"} for i in range(10)]

        limited = generator.apply_count_limit(prompts, count_limit=3)

        assert len(limited) == 3
        assert limited[0]["prompt"] == "test 0"
        assert limited[2]["prompt"] == "test 2"

    def test_returns_all_prompts_when_no_limit(self, generator):
        """Returns all prompts when count_limit is None."""
        prompts = [{"prompt": f"test {i}"} for i in range(10)]

        limited = generator.apply_count_limit(prompts, count_limit=None)

        assert len(limited) == 10

    def test_returns_all_prompts_when_limit_exceeds_count(self, generator):
        """Returns all prompts when limit exceeds available count."""
        prompts = [{"prompt": f"test {i}"} for i in range(3)]

        limited = generator.apply_count_limit(prompts, count_limit=10)

        assert len(limited) == 3
