"""
Unit tests for ProgressReporter
"""

from pathlib import Path

from sd_generator_cli.api import ProgressReporter, SilentProgressReporter


class TestProgressReporter:
    """Test console progress reporting"""

    def test_init(self):
        """Test reporter initialization"""
        reporter = ProgressReporter(
            total_images=10,
            output_dir=Path("/tmp/test"),
            verbose=True
        )

        assert reporter.total == 10
        assert reporter.output_dir == Path("/tmp/test")
        assert reporter.verbose is True
        assert reporter.completed_count == 0
        assert reporter.success_count == 0

    def test_init_minimal(self):
        """Test reporter with minimal parameters"""
        reporter = ProgressReporter(total_images=5)

        assert reporter.total == 5
        assert reporter.output_dir is None
        assert reporter.verbose is True

    def test_report_batch_start(self, capsys):
        """Test batch start message"""
        reporter = ProgressReporter(
            total_images=10,
            output_dir=Path("/tmp/test")
        )

        reporter.report_batch_start()

        output = capsys.readouterr().out
        assert "10 images" in output
        assert "/tmp/test" in output
        assert reporter.start_time is not None

    def test_report_batch_start_silent(self, capsys):
        """Test silent mode suppresses output"""
        reporter = ProgressReporter(total_images=10, verbose=False)

        reporter.report_batch_start()

        output = capsys.readouterr().out
        assert output == ""

    def test_report_image_start(self, capsys):
        """Test image start message"""
        reporter = ProgressReporter(total_images=5)

        reporter.report_image_start(1, "image_001.png")

        output = capsys.readouterr().out
        assert "[1/5]" in output
        assert "image_001.png" in output

    def test_report_image_success(self, capsys):
        """Test image success message"""
        reporter = ProgressReporter(total_images=5)

        reporter.report_image_success("image_001.png")

        output = capsys.readouterr().out
        assert "✅" in output or "image_001.png" in output
        assert reporter.success_count == 1

    def test_report_image_failure(self, capsys):
        """Test image failure message"""
        reporter = ProgressReporter(total_images=5)

        reporter.report_image_failure("image_001.png", "API error")

        output = capsys.readouterr().out
        assert "❌" in output or "Erreur" in output
        assert "image_001.png" in output
        assert "API error" in output

    def test_report_progress_update(self, capsys):
        """Test periodic progress update"""
        reporter = ProgressReporter(total_images=100)
        reporter.report_batch_start()

        # Clear batch start output
        capsys.readouterr()

        # Should print at index 10 (default interval)
        reporter.report_progress_update(10, update_interval=10)

        output = capsys.readouterr().out
        assert "Temps restant" in output or "minutes" in output

    def test_report_progress_update_skip_non_interval(self, capsys):
        """Test progress update skips non-interval indices"""
        reporter = ProgressReporter(total_images=100)
        reporter.report_batch_start()

        # Clear batch start output
        capsys.readouterr()

        # Should NOT print at index 5 (not multiple of 10)
        reporter.report_progress_update(5, update_interval=10)

        output = capsys.readouterr().out
        # Should be empty or not contain time estimate
        assert "Temps restant" not in output

    def test_report_batch_complete(self, capsys):
        """Test batch completion summary"""
        reporter = ProgressReporter(
            total_images=10,
            output_dir=Path("/tmp/test")
        )
        reporter.report_batch_start()
        reporter.success_count = 8

        # Clear batch start output
        capsys.readouterr()

        reporter.report_batch_complete()

        output = capsys.readouterr().out
        assert "8/10" in output
        assert "Temps total" in output or "minutes" in output

    def test_get_summary(self):
        """Test summary dictionary"""
        reporter = ProgressReporter(total_images=10)
        reporter.report_batch_start()
        reporter.success_count = 7

        summary = reporter.get_summary()

        assert summary['total'] == 10
        assert summary['success'] == 7
        assert summary['failed'] == 3
        assert 'elapsed_seconds' in summary
        assert 'elapsed_minutes' in summary

    def test_get_summary_before_start(self):
        """Test summary before batch starts"""
        reporter = ProgressReporter(total_images=10)

        summary = reporter.get_summary()

        assert summary['elapsed_seconds'] == 0.0
        assert summary['elapsed_minutes'] == 0.0

    def test_increment_counters(self):
        """Test counter increment methods"""
        reporter = ProgressReporter(total_images=10)

        assert reporter.completed_count == 0
        assert reporter.success_count == 0

        reporter.increment_completed()
        assert reporter.completed_count == 1

        reporter.increment_success()
        assert reporter.success_count == 1

    def test_verbose_flag(self, capsys):
        """Test verbose flag controls all output"""
        reporter = ProgressReporter(total_images=5, verbose=False)

        reporter.report_batch_start()
        reporter.report_image_start(1, "test.png")
        reporter.report_image_success("test.png")
        reporter.report_batch_complete()

        output = capsys.readouterr().out
        assert output == ""


class TestSilentProgressReporter:
    """Test silent progress reporter"""

    def test_init(self):
        """Test silent reporter initialization"""
        reporter = SilentProgressReporter(total_images=10)

        assert reporter.total == 10
        assert reporter.verbose is False

    def test_all_methods_silent(self, capsys):
        """Test all methods produce no output"""
        reporter = SilentProgressReporter(total_images=5)

        reporter.report_batch_start()
        reporter.report_image_start(1, "test.png")
        reporter.report_image_success("test.png")
        reporter.report_image_failure("test.png", "error")
        reporter.report_progress_update(1)
        reporter.report_batch_complete()

        # Check no output was produced
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""
