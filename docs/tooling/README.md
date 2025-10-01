# Development Tooling Documentation

**Development tools and testing infrastructure.**

---

## Overview

This section covers development setup, testing, and tooling for contributors.

---

## Quick Start

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd local-sd-generator

# Create virtual environment (optional)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install pytest pytest-cov
```

---

## Running Tests

### All Tests

```bash
pytest tests/ -v
```

### Specific Test Files

```bash
# Output system tests
pytest tests/test_output_namer.py tests/test_metadata_generator.py -v

# Config system tests
pytest tests/test_global_config.py tests/test_config_schema.py tests/test_config_loader.py -v

# Placeholder tests
pytest tests/test_placeholder*.py -v
```

### With Coverage

```bash
pytest tests/ --cov=CLI --cov-report=html
```

View coverage report: `open htmlcov/index.html`

---

## Test Structure

```
tests/
├── conftest.py                  # Pytest fixtures
├── test_output_namer.py         # SF-4 tests (27 tests)
├── test_metadata_generator.py   # SF-5 tests (22 tests)
├── test_global_config.py        # SF-7 tests (26 tests)
├── test_config_schema.py        # SF-1 tests (29 tests)
├── test_config_loader.py        # SF-1 tests (31 tests)
├── test_placeholder_options.py  # Placeholder syntax tests
├── test_placeholder_priority.py # Priority system tests
├── test_nested_variations.py    # Nested variation tests
└── test_multiple_files.py       # Multiple file tests
```

**Total:** 135+ tests passing ✅

---

## Testing Guidelines

### Unit Tests

- Test individual functions/methods
- Mock external dependencies (SD API, file I/O where appropriate)
- Fast execution (< 1s per test)
- Clear test names (`test_sanitize_removes_special_characters`)

### Integration Tests

- Test complete workflows
- Use real files (in `tests/fixtures/`)
- Validate end-to-end behavior
- Acceptable longer execution time

### Test Fixtures

**File:** `tests/conftest.py`

Common fixtures for tests:
- Temporary directories
- Sample config files
- Sample variation files
- Mocked SD API responses

---

## Platform-Specific Notes

### WSL (Windows Subsystem for Linux)

**Important:** Use `python3` command, not `python`.

```bash
# Correct
python3 CLI/generator_cli.py

# May not work
python CLI/generator_cli.py
```

### Windows

Standard Python installation:
```bash
python CLI/generator_cli.py
```

### macOS / Linux

Use `python3`:
```bash
python3 CLI/generator_cli.py
```

---

## Code Quality

### Linting (Planned)

```bash
# To be implemented
pylint CLI/
flake8 CLI/
black CLI/ --check
```

### Type Checking (Planned)

```bash
# To be implemented
mypy CLI/
```

---

## Debugging

### Verbose Test Output

```bash
pytest tests/ -vv -s
```

### Run Single Test

```bash
pytest tests/test_output_namer.py::test_sanitize_filename_camelcase -vv
```

### Debug Mode

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Run test
pytest tests/test_output_namer.py -s
```

---

## Contributing

### Before Committing

1. Run all tests: `pytest tests/ -v`
2. Verify no regressions
3. Add tests for new features
4. Update documentation

### Adding New Tests

```python
# tests/test_new_feature.py
import pytest
from CLI.module import function_to_test

def test_feature_basic_case():
    """Test basic functionality."""
    result = function_to_test("input")
    assert result == "expected_output"

def test_feature_edge_case():
    """Test edge case handling."""
    result = function_to_test("")
    assert result == "default_value"
```

---

## CI/CD (Planned)

Future integration:
- GitHub Actions for automated testing
- Coverage reporting
- Linting checks
- Deployment automation

---

## Resources

- **pytest Documentation:** https://docs.pytest.org/
- **Python Testing Best Practices:** https://docs.python-guide.org/writing/tests/

---

**Last updated:** 2025-10-01
