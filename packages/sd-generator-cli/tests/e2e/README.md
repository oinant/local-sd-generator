# End-to-End Tests

These tests verify the CLI commands work correctly when the package is fully installed.

## Requirements

The package **must be installed** before running these tests:

```bash
# From packages/sd-generator-cli/
pip install -e .
```

## Running E2E Tests

```bash
# Run only e2e tests
pytest tests/e2e/ -v

# Run with marker
pytest -m e2e -v

# Skip e2e tests (useful for CI)
pytest -m "not e2e" -v
# OR
pytest --ignore=tests/e2e/ -v
```

## What These Tests Do

- Verify `sdgen` command is available in PATH
- Test all CLI commands and subcommands
- Verify help text displays correctly
- Test command flags and options
- Test error handling for invalid inputs

## CI Integration

In CI pipelines without package installation, skip e2e tests:

```yaml
# .github/workflows/test.yml
- name: Run tests (skip e2e)
  run: pytest --ignore=tests/e2e/ --cov
```

Or run them in a separate job after installation:

```yaml
- name: Install package
  run: pip install -e .

- name: Run e2e tests
  run: pytest tests/e2e/ -v
```
