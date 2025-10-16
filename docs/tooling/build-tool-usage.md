# Build Tool - Usage Guide

## Overview

`tools/build.py` is a comprehensive quality assurance script that runs all code quality checks, tests, and builds in one command.

## Quick Start

```bash
# Full build (recommended before commit/push)
python3 tools/build.py

# Fast check (skip tests)
python3 tools/build.py --skip-tests

# Backend only (skip frontend)
python3 tools/build.py --skip-frontend
```

## What It Checks

### 1. Python Quality
- **Linting** (flake8) - PEP 8 compliance
- **Type Checking** (mypy) - Type safety
- **Tests + Coverage** (pytest) - 306 tests, coverage %
- **Complexity** (radon) - Cyclomatic complexity
- **Dead Code** (vulture) - Unused variables/functions
- **Security** (bandit) - Vulnerability scan

### 2. Frontend Quality
- **Linting** (ESLint) - JavaScript/Vue.js code quality
- **Build** (Vue CLI) - Production build

### 3. Packaging
- **Python** (Poetry) - Create distributable packages

## Command Options

```bash
python3 tools/build.py [OPTIONS]

Options:
  --skip-tests       Skip tests and coverage (faster)
  --skip-frontend    Skip frontend linting and build
  --skip-package     Skip Python packaging
  --verbose          Show full command output
  --fail-fast        Stop on first failure
  -h, --help         Show help message
```

## Output

### Build Report

```
╭──────────────────────── Build Report ────────────────────────╮
│                                                               │
│  ✓ Python Linting         0 errors                           │
│  ✓ Python Type Checking   0 errors                           │
│  ✓ Python Tests           306 passed, 98% coverage           │
│  ⚠ Complexity Analysis    avg 10.2, 15 functions > 10        │
│  ⚠ Dead Code Detection    3 unused variables                 │
│  ✓ Security Scan          0 vulnerabilities                  │
│  ✓ Frontend Linting       0 errors                           │
│  ✓ Frontend Build         2.3 MB                             │
│  ✓ Python Packaging       sdgen-0.1.0.tar.gz created         │
│                                                               │
│  Overall: ⚠ WARNING (2 warnings)                             │
│                                                               │
╰───────────────────────────────────────────────────────────────╯
```

### Priority Actions

The script automatically identifies the top 5 issues to fix, prioritized by severity:

```
╭───────────────── Top 5 Priority Actions ─────────────────────╮
│                                                               │
│  1. [SECURITY] Fix high severity: Use of weak MD5 hash       │
│     Location: hash_utils.py:29                               │
│     Current: MD5, Target: SHA256                             │
│                                                               │
│  2. [COMPLEXITY] Reduce complexity in _generate()            │
│     Location: cli.py:110                                     │
│     Current: 37, Target: < 10                                │
│                                                               │
│  3. [COVERAGE] Add tests for import_resolver.py              │
│     Current: 65%, Target: > 80%                              │
│                                                               │
│  4. [DEAD_CODE] Remove unused import in resolver.py:10       │
│     Variable: old_function                                   │
│                                                               │
│  5. [TYPE] Fix type checking error in orchestrator.py:45     │
│                                                               │
╰───────────────────────────────────────────────────────────────╯
```

## Exit Codes

- `0` - Success (all checks passed, warnings OK)
- `1` - Failure (critical checks failed)
- `2` - Script execution error

## Priority Levels

Actions are prioritized by severity:

| Priority | Category    | Weight | Description                           |
|----------|-------------|--------|---------------------------------------|
| 10       | SECURITY    | High   | High/medium severity vulnerabilities  |
| 8        | TYPE        | High   | Type checking errors                  |
| 7        | COVERAGE    | Medium | Test coverage < 80%                   |
| 6        | COMPLEXITY  | Medium | Functions with complexity > 10        |
| 3        | DEAD_CODE   | Low    | Unused variables/functions            |

## Usage Examples

### Pre-Commit Check

```bash
# Run full build before committing
python3 tools/build.py

# If all checks pass, commit
git add .
git commit -m "feat: add new feature"
```

### Fast Iteration

```bash
# Quick check during development
python3 tools/build.py --skip-tests --skip-frontend
```

### Debug Mode

```bash
# See full output of all commands
python3 tools/build.py --verbose
```

### CI/CD Integration

```bash
# Fail fast for CI pipelines
python3 tools/build.py --fail-fast

# Check exit code
if [ $? -eq 0 ]; then
  echo "Build passed!"
else
  echo "Build failed!"
  exit 1
fi
```

## Typical Workflow

### 1. Before Starting Work

```bash
# Ensure starting from clean state
python3 tools/build.py
```

### 2. During Development

```bash
# Quick checks (fast feedback)
python3 tools/build.py --skip-tests
```

### 3. Before Committing

```bash
# Full check with all tests
python3 tools/build.py

# Fix any issues shown in Priority Actions
```

### 4. Before Pushing

```bash
# Final verification
python3 tools/build.py --fail-fast
```

## Troubleshooting

### "Command not found" errors

**Problem**: Tools like `flake8`, `mypy`, etc. not found.

**Solution**: Ensure virtual environment is set up:
```bash
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Frontend build fails

**Problem**: `npm` commands fail.

**Solution**: Install frontend dependencies:
```bash
cd packages/sd-generator-webui/front
npm install
```

### Tests fail unexpectedly

**Problem**: Some tests fail that passed before.

**Solution**: Clean test cache and retry:
```bash
cd packages/sd-generator-cli
rm -rf .pytest_cache __pycache__
pytest tests/ -v
```

### Long execution time

**Problem**: Full build takes too long.

**Solution**: Use selective skips:
```bash
# Skip the slowest parts
python3 tools/build.py --skip-tests --skip-frontend
```

## Integration with Git Hooks

You can auto-run the build tool before commits using git hooks:

```bash
# .git/hooks/pre-commit
#!/bin/bash
python3 tools/build.py --skip-frontend --skip-package --fail-fast
exit $?
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Performance

Typical execution times (on WSL2, i7-10700K):

| Configuration                | Time    |
|------------------------------|---------|
| Full build                   | ~2m 30s |
| `--skip-tests`               | ~30s    |
| `--skip-frontend`            | ~2m 00s |
| `--skip-tests --skip-frontend` | ~20s    |

## Future Enhancements

Planned features:

- [ ] Parallel execution of independent steps
- [ ] Caching of results (only re-run changed code)
- [ ] `--watch` mode for continuous checking
- [ ] JSON output for CI/CD integration
- [ ] HTML report generation
- [ ] Integration with GitHub Actions

## See Also

- [Build Tool Specification](../roadmap/wip/build-tool.md) - Technical details
- [Code Review Guidelines](CODE_REVIEW_GUIDELINES.md) - Manual review process
- [Type Checking Guide](type-checking-guide.md) - mypy usage
