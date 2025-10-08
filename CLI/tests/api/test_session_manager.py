"""
Unit tests for SessionManager
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from api import SessionManager
from api import GenerationConfig


class TestSessionManager:
    """Test session directory management"""

    @pytest.fixture
    def temp_base_dir(self):
        """Create temporary base directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_init(self, temp_base_dir):
        """Test session manager initialization"""
        manager = SessionManager(
            base_output_dir=temp_base_dir,
            session_name="test_session",
            dry_run=False
        )

        assert manager.base_output_dir == temp_base_dir
        assert manager.session_name == "test_session"
        assert manager.dry_run is False
        assert isinstance(manager.session_start_time, datetime)

    def test_output_dir_lazy_creation(self, temp_base_dir):
        """Test output_dir is created lazily"""
        manager = SessionManager(base_output_dir=temp_base_dir)

        # Accessing output_dir triggers path building
        output_dir = manager.output_dir

        assert isinstance(output_dir, Path)
        assert str(output_dir).startswith(temp_base_dir)

    def test_session_path_with_name(self, temp_base_dir):
        """Test session path includes session name"""
        manager = SessionManager(
            base_output_dir=temp_base_dir,
            session_name="my_session"
        )

        output_dir = manager.output_dir

        assert "my_session" in str(output_dir)

    def test_session_path_without_name(self, temp_base_dir):
        """Test session path without name uses only timestamp"""
        manager = SessionManager(base_output_dir=temp_base_dir)

        output_dir = manager.output_dir

        # Should be: base_dir/YYYY-MM-DD_HHMMSS/
        assert output_dir.parent == Path(temp_base_dir)

    def test_dry_run_subdirectory(self, temp_base_dir):
        """Test dry-run mode creates /dryrun subdirectory"""
        manager = SessionManager(
            base_output_dir=temp_base_dir,
            dry_run=True
        )

        output_dir = manager.output_dir

        assert "dryrun" in str(output_dir)
        assert output_dir.parent.name == "dryrun"

    def test_create_session_dir(self, temp_base_dir):
        """Test physical directory creation"""
        manager = SessionManager(base_output_dir=temp_base_dir)

        session_path = manager.create_session_dir()

        assert session_path.exists()
        assert session_path.is_dir()

    def test_create_session_dir_idempotent(self, temp_base_dir):
        """Test create_session_dir can be called multiple times"""
        manager = SessionManager(base_output_dir=temp_base_dir)

        path1 = manager.create_session_dir()
        path2 = manager.create_session_dir()

        assert path1 == path2
        assert path1.exists()

    def test_save_session_config(self, temp_base_dir):
        """Test session config file creation"""
        manager = SessionManager(
            base_output_dir=temp_base_dir,
            session_name="test_session"
        )

        gen_config = GenerationConfig(steps=25, cfg_scale=8.0)

        manager.save_session_config(
            generation_config=gen_config,
            base_prompt="a cat",
            negative_prompt="low quality",
            additional_info={"test": "value"}
        )

        config_file = manager.output_dir / "session_config.txt"
        assert config_file.exists()

        # Read and verify content
        content = config_file.read_text(encoding='utf-8')
        assert "SESSION CONFIGURATION" in content
        assert "a cat" in content
        assert "low quality" in content
        assert "steps: 25" in content
        assert "cfg_scale: 8.0" in content
        assert "test: value" in content

    def test_save_session_config_dry_run(self, temp_base_dir):
        """Test session config includes dry-run mode"""
        manager = SessionManager(
            base_output_dir=temp_base_dir,
            dry_run=True
        )

        gen_config = GenerationConfig()

        manager.save_session_config(
            generation_config=gen_config,
            base_prompt="test",
            negative_prompt=""
        )

        config_file = manager.output_dir / "session_config.txt"
        content = config_file.read_text(encoding='utf-8')

        assert "Mode: Dry-run" in content

    def test_get_session_info(self, temp_base_dir):
        """Test session info dictionary"""
        manager = SessionManager(
            base_output_dir=temp_base_dir,
            session_name="info_test",
            dry_run=True
        )

        info = manager.get_session_info()

        assert info['session_name'] == "info_test"
        assert info['dry_run'] is True
        assert info['base_output_dir'] == temp_base_dir
        assert 'start_time' in info
        assert 'output_dir' in info

    def test_multiple_sessions_different_timestamps(self, temp_base_dir):
        """Test multiple sessions get different directories"""
        import time

        manager1 = SessionManager(base_output_dir=temp_base_dir)
        dir1 = manager1.output_dir

        # Small delay to ensure different timestamp
        time.sleep(1.1)

        manager2 = SessionManager(base_output_dir=temp_base_dir)
        dir2 = manager2.output_dir

        assert dir1 != dir2

    def test_session_config_minimal(self, temp_base_dir):
        """Test session config with minimal parameters"""
        manager = SessionManager(base_output_dir=temp_base_dir)
        gen_config = GenerationConfig()

        manager.save_session_config(
            generation_config=gen_config,
            base_prompt="",
            negative_prompt=""
        )

        config_file = manager.output_dir / "session_config.txt"
        assert config_file.exists()

        content = config_file.read_text(encoding='utf-8')
        assert "SESSION CONFIGURATION" in content
