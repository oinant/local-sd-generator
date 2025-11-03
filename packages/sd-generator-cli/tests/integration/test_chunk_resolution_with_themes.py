"""
Integration test for chunk resolution with themes and inheritance.

This test replicates the bug where chunks defined in parent templates
were not being loaded into the ResolvedContext when using themes.

Bug scenario:
1. Base template defines chunks: { QUALITY: path/to/chunk.yaml }
2. Prompt inherits from base template
3. Prompt uses chunk reference {@QUALITY} in its template
4. User runs with --theme cyberpunk
5. BUG: ValueError "Chunk 'QUALITY' not found in chunks"

Root cause:
- orchestrator.py was setting chunks={} instead of loading them
- inheritance_resolver.py only merged chunks for ChunkConfig, not TemplateConfig/PromptConfig
- parser.py wasn't parsing the 'chunks:' field from YAML
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from sd_generator_cli.templating.orchestrator import V2Pipeline


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


def test_chunk_resolution_with_themes_and_inheritance(temp_dir):
    """
    Test that chunks defined in parent templates are available in child prompts
    when using themes.

    This replicates the exact bug from v4-boys.prompt.yaml:
    - Parent template (_tpl_base_themable.template.yaml) defines chunks
    - Child prompt (v4-boys.prompt.yaml) uses {@QUALITY} chunk reference
    - Should work with --theme cyberpunk
    """

    # 1. Create chunk file
    chunk_file = temp_dir / "quality.chunk.yaml"
    chunk_file.write_text("""
version: '2.0'
type: chunk
name: Quality Tags

template: |
  masterpiece, best quality, ultra-detailed
""")

    # 2. Create base template with chunks definition
    base_template = temp_dir / "base.template.yaml"
    base_template.write_text("""
type: template
version: '2.0'
name: 'Base Template'

# CHUNKS DEFINITION (this was the bug - chunks weren't being loaded)
chunks:
  QUALITY: ./quality.chunk.yaml

# Theme configuration
themes:
  enable_autodiscovery: true

imports:
  HairColor: ./haircolors.yaml

template: |
  {prompt}

negative_prompt: |
  low quality
""")

    # 3. Create variations file for imports
    variations_file = temp_dir / "haircolors.yaml"
    variations_file.write_text("""
type: variations
version: '2.0'
name: Hair Colors
variations:
  blonde: blonde hair
  brown: brown hair
""")

    # 4. Create theme file
    theme_dir = temp_dir / "cyberpunk"
    theme_dir.mkdir()
    theme_file = theme_dir / "theme.yaml"
    theme_file.write_text("""
type: theme
version: '2.0'
name: cyberpunk

imports:
  HairColor: ../haircolors.yaml
""")

    # 5. Create prompt that inherits from base and uses chunk
    prompt_file = temp_dir / "test.prompt.yaml"
    prompt_file.write_text("""
type: prompt
version: '2.0'
name: 'Test Prompt'

implements: ./base.template.yaml

prompt: |
  {@QUALITY},
  beautiful girl,
  {HairColor}

generation:
  mode: random
  seed: 42
  seed_mode: progressive
  max_images: 1
""")

    # 6. Run the pipeline with theme (this should NOT raise ValueError)
    pipeline = V2Pipeline(configs_dir=str(temp_dir))

    # Load config
    config = pipeline.load(str(prompt_file))

    # Resolve with theme (THIS IS WHERE THE BUG WAS)
    # Before fix: ValueError: Chunk 'QUALITY' not found in chunks
    # After fix: Should work fine
    resolved_config, context = pipeline.resolve(config, theme_name="cyberpunk")

    # Assertions
    # 1. Context should have chunks loaded
    assert 'QUALITY' in context.chunks, "QUALITY chunk should be in context.chunks"

    # 2. The chunk should be a dict with 'template' key
    assert isinstance(context.chunks['QUALITY'], dict), "Chunk should be dict"
    assert 'template' in context.chunks['QUALITY'], "Chunk dict should have 'template' key"

    # 3. The chunk's template should be loaded
    assert 'masterpiece' in context.chunks['QUALITY']['template'], "Chunk template should be loaded"

    # 4. The resolved template should have chunk injected
    assert 'masterpiece' in resolved_config.template, "Chunk should be injected into template"

    # 5. Generate should work without errors
    prompts = pipeline.generate(resolved_config, context)
    assert len(prompts) == 1, "Should generate 1 prompt"
    assert 'masterpiece' in prompts[0]['prompt'], "Final prompt should contain chunk content"


def test_chunks_inheritance_chain(temp_dir):
    """
    Test that chunks are properly merged through inheritance chain.

    Scenario:
    - GrandParent template defines CHUNK_A
    - Parent template inherits GrandParent and adds CHUNK_B
    - Child prompt inherits Parent and uses both chunks
    """

    # 1. Create chunk files
    chunk_a = temp_dir / "chunk_a.chunk.yaml"
    chunk_a.write_text("""
version: '2.0'
type: chunk
name: Chunk A
template: |
  quality tags A, high detail A
""")

    chunk_b = temp_dir / "chunk_b.chunk.yaml"
    chunk_b.write_text("""
version: '2.0'
type: chunk
name: Chunk B
template: |
  quality tags B, high detail B
""")

    # 2. Create grandparent template
    grandparent = temp_dir / "grandparent.template.yaml"
    grandparent.write_text("""
type: template
version: '2.0'
name: 'GrandParent'

chunks:
  CHUNK_A: ./chunk_a.chunk.yaml

template: |
  {prompt}
""")

    # 3. Create parent template (inherits grandparent, adds CHUNK_B)
    parent = temp_dir / "parent.template.yaml"
    parent.write_text("""
type: template
version: '2.0'
name: 'Parent'

implements: ./grandparent.template.yaml

chunks:
  CHUNK_B: ./chunk_b.chunk.yaml

template: |
  {@CHUNK_A}, {prompt}
""")

    # 4. Create child prompt (uses both chunks)
    child = temp_dir / "child.prompt.yaml"
    child.write_text("""
type: prompt
version: '2.0'
name: 'Child'

implements: ./parent.template.yaml

prompt: |
  {@CHUNK_B}, test content

generation:
  mode: random
  seed: 42
  seed_mode: fixed
  max_images: 1
""")

    # 5. Run pipeline
    pipeline = V2Pipeline()
    config = pipeline.load(str(child))
    resolved_config, context = pipeline.resolve(config)

    # Assertions
    # Both chunks should be in context (merged through inheritance)
    assert 'CHUNK_A' in context.chunks, "CHUNK_A should be inherited from grandparent"
    assert 'CHUNK_B' in context.chunks, "CHUNK_B should be inherited from parent"

    # Final template should have both chunks injected
    assert 'quality tags A' in resolved_config.template, "CHUNK_A should be injected"
    assert 'quality tags B' in resolved_config.template, "CHUNK_B should be injected"

    # Generate should work
    prompts = pipeline.generate(resolved_config, context)
    assert len(prompts) == 1
    assert 'quality tags A' in prompts[0]['prompt']
    assert 'quality tags B' in prompts[0]['prompt']


def test_chunk_override_in_child(temp_dir):
    """
    Test that child can override parent's chunk definition.

    Scenario:
    - Parent defines QUALITY chunk with one template
    - Child redefines QUALITY chunk with different template
    - Child's version should win
    """

    # 1. Create two different chunk files
    chunk_parent = temp_dir / "quality_parent.chunk.yaml"
    chunk_parent.write_text("""
version: '2.0'
type: chunk
name: Quality Parent
template: |
  parent quality, high detail
""")

    chunk_child = temp_dir / "quality_child.chunk.yaml"
    chunk_child.write_text("""
version: '2.0'
type: chunk
name: Quality Child
template: |
  child quality, ultra detail
""")

    # 2. Parent template
    parent = temp_dir / "parent.template.yaml"
    parent.write_text("""
type: template
version: '2.0'
name: 'Parent'

chunks:
  QUALITY: ./quality_parent.chunk.yaml

template: |
  {prompt}
""")

    # 3. Child prompt (overrides QUALITY)
    child = temp_dir / "child.prompt.yaml"
    child.write_text("""
type: prompt
version: '2.0'
name: 'Child'

implements: ./parent.template.yaml

chunks:
  QUALITY: ./quality_child.chunk.yaml

prompt: |
  {@QUALITY}, test

generation:
  mode: random
  seed: 42
  seed_mode: fixed
  max_images: 1
""")

    # 4. Run pipeline
    pipeline = V2Pipeline()
    config = pipeline.load(str(child))
    resolved_config, context = pipeline.resolve(config)

    # Assertions
    # Child's chunk should override parent's
    assert 'child quality' in context.chunks['QUALITY']['template'], "Child chunk should override parent"
    assert 'child quality' in resolved_config.template, "Child chunk should be injected"
    assert 'parent quality' not in resolved_config.template, "Parent chunk should not be in final template"
