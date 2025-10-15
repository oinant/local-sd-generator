"""
Integration tests for V2Executor - Phase 7.

These tests verify that V2Executor correctly integrates with the SD API client
and handles image generation, metadata saving, and error conditions.
"""

import base64
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from tempfile import TemporaryDirectory

from sd_generator_cli.templating.executor import V2Executor
from sd_generator_cli.api.sdapi_client import SDAPIClient, PromptConfig, GenerationConfig


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = Mock(spec=SDAPIClient)
    client.test_connection.return_value = True
    client.generate_image.return_value = {
        'images': [base64.b64encode(b'fake_image_data').decode('utf-8')],
        'info': json.dumps({
            'seed': 42,
            'steps': 30,
            'cfg_scale': 7.0
        }),
        'parameters': {
            'prompt': 'test prompt',
            'negative_prompt': 'test negative',
            'seed': 42
        }
    }
    return client


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_prompts():
    """Sample prompts from V2Pipeline."""
    return [
        {
            'prompt': 'masterpiece, 1girl, smiling, detailed',
            'negative_prompt': 'low quality, blurry',
            'seed': 42,
            'variations': {'Expression': 'smiling', 'Angle': 'front'},
            'parameters': {
                'steps': 30,
                'cfg_scale': 7.0,
                'width': 512,
                'height': 768
            }
        },
        {
            'prompt': 'masterpiece, 1girl, serious, detailed',
            'negative_prompt': 'low quality, blurry',
            'seed': 43,
            'variations': {'Expression': 'serious', 'Angle': 'front'},
            'parameters': {
                'steps': 30,
                'cfg_scale': 7.0,
                'width': 512,
                'height': 768
            }
        }
    ]


# ============================================================================
# Initialization Tests
# ============================================================================

def test_executor_init_default(temp_output_dir):
    """Test executor initialization with defaults."""
    executor = V2Executor(output_dir=temp_output_dir)

    assert executor.output_dir == Path(temp_output_dir)
    assert executor.session_dir.exists()
    assert executor.api_client is not None


def test_executor_init_with_client(mock_api_client, temp_output_dir):
    """Test executor initialization with custom client."""
    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir,
        session_name="test_session"
    )

    assert executor.api_client == mock_api_client
    assert executor.session_name == "test_session"
    assert (Path(temp_output_dir) / "test_session").exists()


# ============================================================================
# Single Execution Tests
# ============================================================================

def test_execute_single_success(mock_api_client, temp_output_dir, sample_prompts):
    """Test successful single prompt execution."""
    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir
    )

    result = executor.execute_single(sample_prompts[0], image_number=1)

    # Verify success
    assert result['success'] is True
    assert result['error'] is None

    # Verify API was called
    mock_api_client.generate_image.assert_called_once()
    call_args = mock_api_client.generate_image.call_args[0][0]
    assert isinstance(call_args, PromptConfig)
    assert call_args.prompt == sample_prompts[0]['prompt']
    assert call_args.seed == 42

    # Verify files exist
    assert result['image_path'].exists()
    assert result['metadata_path'].exists()

    # Verify image file
    assert result['image_path'].name == 'image_0001.png'
    assert result['image_path'].read_bytes() == b'fake_image_data'

    # Verify metadata
    metadata = json.loads(result['metadata_path'].read_text())
    assert metadata['prompt'] == sample_prompts[0]['prompt']
    assert metadata['seed'] == 42
    assert metadata['variations'] == sample_prompts[0]['variations']
    assert 'timestamp' in metadata


def test_execute_single_api_error(mock_api_client, temp_output_dir, sample_prompts):
    """Test handling of API errors."""
    mock_api_client.generate_image.side_effect = Exception("API connection failed")

    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir
    )

    result = executor.execute_single(sample_prompts[0], image_number=1)

    # Verify error handling
    assert result['success'] is False
    assert result['error'] == "API connection failed"
    assert result['image_path'] is None
    assert result['metadata_path'] is None


def test_execute_single_with_parameters(mock_api_client, temp_output_dir, sample_prompts):
    """Test parameter application during execution."""
    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir
    )

    result = executor.execute_single(sample_prompts[0], image_number=1)

    # Verify parameters were applied
    mock_api_client.set_generation_config.assert_called_once()
    config = mock_api_client.set_generation_config.call_args[0][0]
    assert config.steps == 30
    assert config.cfg_scale == 7.0
    assert config.width == 512
    assert config.height == 768


# ============================================================================
# Batch Execution Tests
# ============================================================================

def test_execute_prompts_batch(mock_api_client, temp_output_dir, sample_prompts):
    """Test batch execution of multiple prompts."""
    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir
    )

    results = executor.execute_prompts(sample_prompts)

    # Verify all prompts were executed
    assert len(results) == 2
    assert all(r['success'] for r in results)

    # Verify API was called for each prompt
    assert mock_api_client.generate_image.call_count == 2

    # Verify files were created
    assert results[0]['image_path'].name == 'image_0001.png'
    assert results[1]['image_path'].name == 'image_0002.png'


def test_execute_prompts_with_progress(mock_api_client, temp_output_dir, sample_prompts):
    """Test progress callback during batch execution."""
    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir
    )

    progress_calls = []

    def progress_callback(current, total):
        progress_calls.append((current, total))

    results = executor.execute_prompts(
        sample_prompts,
        progress_callback=progress_callback
    )

    # Verify progress was reported
    assert len(progress_calls) > 0
    assert progress_calls[-1] == (2, 2)  # Final call


def test_execute_prompts_partial_failure(mock_api_client, temp_output_dir, sample_prompts):
    """Test batch execution with partial failures."""
    # First call succeeds, second fails
    mock_api_client.generate_image.side_effect = [
        {
            'images': [base64.b64encode(b'fake_image_data').decode('utf-8')],
            'info': json.dumps({'seed': 42})
        },
        Exception("API error on second image")
    ]

    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir
    )

    results = executor.execute_prompts(sample_prompts)

    # Verify mixed results
    assert len(results) == 2
    assert results[0]['success'] is True
    assert results[1]['success'] is False
    assert results[1]['error'] == "API error on second image"


# ============================================================================
# Metadata Tests
# ============================================================================

def test_metadata_contains_all_fields(mock_api_client, temp_output_dir, sample_prompts):
    """Test that metadata contains all expected fields."""
    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir
    )

    result = executor.execute_single(sample_prompts[0], image_number=1)

    metadata = json.loads(result['metadata_path'].read_text())

    # Verify all expected fields
    assert 'prompt' in metadata
    assert 'negative_prompt' in metadata
    assert 'seed' in metadata
    assert 'variations' in metadata
    assert 'parameters' in metadata
    assert 'image_path' in metadata
    assert 'timestamp' in metadata
    assert 'api_info' in metadata


def test_metadata_variations_preserved(mock_api_client, temp_output_dir, sample_prompts):
    """Test that variation info is correctly preserved in metadata."""
    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir
    )

    result = executor.execute_single(sample_prompts[0], image_number=1)

    metadata = json.loads(result['metadata_path'].read_text())

    # Verify variations
    assert metadata['variations']['Expression'] == 'smiling'
    assert metadata['variations']['Angle'] == 'front'


# ============================================================================
# Output Management Tests
# ============================================================================

def test_session_directory_creation(mock_api_client, temp_output_dir):
    """Test that session directories are created correctly."""
    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir,
        session_name="my_session"
    )

    session_dir = Path(temp_output_dir) / "my_session"
    assert session_dir.exists()
    assert session_dir == executor.session_dir


def test_set_output_dir(mock_api_client, temp_output_dir):
    """Test changing output directory."""
    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir
    )

    # Create new temp dir
    with TemporaryDirectory() as new_tmpdir:
        executor.set_output_dir(new_tmpdir, session_name="new_session")

        assert executor.output_dir == Path(new_tmpdir)
        assert executor.session_name == "new_session"
        assert (Path(new_tmpdir) / "new_session").exists()


def test_get_session_summary(mock_api_client, temp_output_dir, sample_prompts):
    """Test session summary generation."""
    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir
    )

    results = executor.execute_prompts(sample_prompts)
    summary = executor.get_session_summary(results)

    # Verify summary
    assert summary['total'] == 2
    assert summary['successful'] == 2
    assert summary['failed'] == 0
    assert len(summary['image_paths']) == 2
    assert 'session_dir' in summary


def test_get_session_summary_with_failures(mock_api_client, temp_output_dir, sample_prompts):
    """Test session summary with failures."""
    # First succeeds, second fails
    mock_api_client.generate_image.side_effect = [
        {
            'images': [base64.b64encode(b'fake_image_data').decode('utf-8')],
            'info': json.dumps({'seed': 42})
        },
        Exception("API error")
    ]

    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir
    )

    results = executor.execute_prompts(sample_prompts)
    summary = executor.get_session_summary(results)

    # Verify summary
    assert summary['total'] == 2
    assert summary['successful'] == 1
    assert summary['failed'] == 1
    assert len(summary['errors']) == 1
    assert summary['errors'][0]['index'] == 1
    assert summary['errors'][0]['error'] == "API error"


# ============================================================================
# Connection Tests
# ============================================================================

def test_test_connection_success(mock_api_client, temp_output_dir):
    """Test successful connection test."""
    mock_api_client.test_connection.return_value = True

    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir
    )

    assert executor.test_connection() is True


def test_test_connection_failure(mock_api_client, temp_output_dir):
    """Test failed connection test."""
    mock_api_client.test_connection.return_value = False

    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir
    )

    assert executor.test_connection() is False


# ============================================================================
# Parameter Mapping Tests
# ============================================================================

def test_parameter_mapping_complete(mock_api_client, temp_output_dir):
    """Test that all parameters are correctly mapped."""
    prompt_dict = {
        'prompt': 'test',
        'negative_prompt': 'bad',
        'seed': 123,
        'variations': {},
        'parameters': {
            'steps': 50,
            'cfg_scale': 8.5,
            'width': 768,
            'height': 1024,
            'sampler': 'Euler a',
            'scheduler': 'Karras',
            'enable_hr': True,
            'hr_scale': 2.0,
            'hr_upscaler': 'R-ESRGAN 4x+',
            'denoising_strength': 0.7,
            'hr_second_pass_steps': 20
        }
    }

    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir
    )

    executor.execute_single(prompt_dict, image_number=1)

    # Verify config was set
    config = mock_api_client.set_generation_config.call_args[0][0]
    assert config.steps == 50
    assert config.cfg_scale == 8.5
    assert config.width == 768
    assert config.height == 1024
    assert config.sampler_name == 'Euler a'
    assert config.scheduler == 'Karras'
    assert config.enable_hr is True
    assert config.hr_scale == 2.0
    assert config.hr_upscaler == 'R-ESRGAN 4x+'
    assert config.denoising_strength == 0.7
    assert config.hr_second_pass_steps == 20


def test_parameter_mapping_partial(mock_api_client, temp_output_dir):
    """Test parameter mapping with only some parameters."""
    prompt_dict = {
        'prompt': 'test',
        'negative_prompt': 'bad',
        'seed': 123,
        'variations': {},
        'parameters': {
            'steps': 25,
            'cfg_scale': 9.0
        }
    }

    executor = V2Executor(
        api_client=mock_api_client,
        output_dir=temp_output_dir
    )

    executor.execute_single(prompt_dict, image_number=1)

    # Verify only specified params were set
    config = mock_api_client.set_generation_config.call_args[0][0]
    assert config.steps == 25
    assert config.cfg_scale == 9.0
