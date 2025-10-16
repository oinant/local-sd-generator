#!/usr/bin/env python3
"""
Build Tool - Complete project quality checks and builds

Runs linting, type checking, tests, complexity analysis, security scans,
and builds in one command with a detailed report.

Usage:
    python3 tools/build.py                    # Full build
    python3 tools/build.py --skip-tests       # Skip tests
    python3 tools/build.py --skip-frontend    # Skip frontend
    python3 tools/build.py --verbose          # Show full output
    python3 tools/build.py --fail-fast        # Stop on first failure
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("Error: rich library not found. Install with: pip install rich")
    sys.exit(2)


console = Console()


@dataclass
class StepResult:
    """Result of a build step"""
    name: str
    status: str  # "success", "warning", "error", "skipped"
    duration: float
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class Action:
    """Priority action to take"""
    priority: int  # 1-10 (10 = highest)
    category: str  # "SECURITY", "TYPE", "COVERAGE", "COMPLEXITY", "DEAD_CODE"
    description: str
    location: Optional[str] = None
    current_value: Optional[str] = None
    target_value: Optional[str] = None


class BuildRunner:
    """Runs build steps and generates reports"""

    def __init__(
        self,
        project_root: Path,
        skip_tests: bool = False,
        skip_frontend: bool = False,
        skip_package: bool = False,
        verbose: bool = False,
        fail_fast: bool = False
    ):
        self.project_root = project_root
        self.skip_tests = skip_tests
        self.skip_frontend = skip_frontend
        self.skip_package = skip_package
        self.verbose = verbose
        self.fail_fast = fail_fast
        self.results: List[StepResult] = []

        # Use venv binaries
        self.venv_bin = project_root / "venv/bin"

    def run(self) -> int:
        """Run all build steps and return exit code"""
        console.print(Panel(
            "[bold]Running Complete Build Process[/bold]",
            border_style="cyan"
        ))

        start_time = time.time()

        # Python checks
        self._run_step("Python Linting", self._lint_python)
        self._run_step("Python Type Checking", self._typecheck_python)

        if not self.skip_tests:
            self._run_step("Python Tests + Coverage", self._test_python)
        else:
            self._skip_step("Python Tests + Coverage")

        self._run_step("Complexity Analysis", self._analyze_complexity)
        self._run_step("Dead Code Detection", self._detect_dead_code)
        self._run_step("Security Scan", self._scan_security)

        # Frontend checks
        if not self.skip_frontend:
            self._run_step("Frontend Linting", self._lint_frontend)
            self._run_step("Frontend Build", self._build_frontend)
        else:
            self._skip_step("Frontend Linting")
            self._skip_step("Frontend Build")

        # Packaging
        if not self.skip_package:
            self._run_step("Python Packaging", self._package_python)
        else:
            self._skip_step("Python Packaging")

        total_duration = time.time() - start_time

        # Generate report
        self._generate_report(total_duration)

        # Determine exit code
        has_errors = any(r.status == "error" for r in self.results)
        return 1 if has_errors else 0

    def _run_step(self, name: str, func):
        """Run a build step and track result"""
        if self.fail_fast and any(r.status == "error" for r in self.results):
            self._skip_step(name)
            return

        console.print(f"\n[cyan]Running {name}...[/cyan]")
        start = time.time()

        try:
            result = func()
            result.duration = time.time() - start
            self.results.append(result)

            # Print status
            status_symbol = {
                "success": "[green]✓[/green]",
                "warning": "[yellow]⚠[/yellow]",
                "error": "[red]✗[/red]"
            }[result.status]

            console.print(f"{status_symbol} {name}: {result.message}")

        except Exception as e:
            duration = time.time() - start
            result = StepResult(
                name=name,
                status="error",
                duration=duration,
                message=f"Exception: {e}"
            )
            self.results.append(result)
            console.print(f"[red]✗ {name}: Exception occurred[/red]")
            if self.verbose:
                console.print(f"[dim]{e}[/dim]")

    def _skip_step(self, name: str):
        """Mark step as skipped"""
        result = StepResult(
            name=name,
            status="skipped",
            duration=0.0,
            message="Skipped"
        )
        self.results.append(result)

    def _run_command(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
        capture_json: bool = False
    ) -> subprocess.CompletedProcess:
        """Run a shell command and return result"""
        if self.verbose:
            console.print(f"[dim]$ {' '.join(cmd)}[/dim]")

        result = subprocess.run(
            cmd,
            cwd=cwd or self.project_root,
            capture_output=True,
            text=True
        )

        if self.verbose and result.stdout:
            console.print(f"[dim]{result.stdout}[/dim]")

        if self.verbose and result.stderr:
            console.print(f"[dim]{result.stderr}[/dim]")

        return result

    # ==================== Python Checks ====================

    def _lint_python(self) -> StepResult:
        """Run flake8 linting"""
        cmd = [
            str(self.venv_bin / "flake8"),
            "packages/sd-generator-cli/sd_generator_cli",
            "--exclude=tests,__pycache__",
            "--max-line-length=120",
            "--count",
            "--statistics"
        ]

        result = self._run_command(cmd)

        # Parse output to get error count
        lines = result.stdout.strip().split('\n')
        error_count = 0
        for line in lines:
            if line.strip().isdigit():
                error_count = int(line.strip())
                break

        if result.returncode == 0:
            return StepResult(
                name="Python Linting",
                status="success",
                duration=0,
                message=f"{error_count} errors",
                details={"error_count": error_count}
            )
        else:
            return StepResult(
                name="Python Linting",
                status="error",
                duration=0,
                message=f"{error_count} errors found",
                details={"error_count": error_count, "output": result.stdout}
            )

    def _typecheck_python(self) -> StepResult:
        """Run mypy type checking"""
        cmd = [
            str(self.venv_bin / "mypy"),
            "packages/sd-generator-cli/sd_generator_cli",
            "--show-error-codes"
        ]

        result = self._run_command(cmd)

        # Count errors in output
        error_count = result.stdout.count("error:")

        if result.returncode == 0:
            return StepResult(
                name="Python Type Checking",
                status="success",
                duration=0,
                message=f"{error_count} errors",
                details={"error_count": error_count}
            )
        else:
            return StepResult(
                name="Python Type Checking",
                status="error",
                duration=0,
                message=f"{error_count} errors found",
                details={"error_count": error_count, "output": result.stdout}
            )

    def _test_python(self) -> StepResult:
        """Run pytest with coverage"""
        cmd = [
            str(self.venv_bin / "pytest"),
            "tests/",
            "-v",
            "--cov=sd_generator_cli",
            "--cov-report=term-missing"
        ]

        cli_dir = self.project_root / "packages/sd-generator-cli"
        result = self._run_command(cmd, cwd=cli_dir)

        # Parse output for test counts and coverage
        output = result.stdout + result.stderr

        # Parse test summary line: "26 failed, 371 passed in 16.00s"
        passed = 0
        failed = 0
        for line in output.split('\n'):
            if 'passed' in line or 'failed' in line:
                # Look for summary line
                import re
                # Match patterns like "26 failed, 371 passed" or "371 passed"
                failed_match = re.search(r'(\d+)\s+failed', line)
                passed_match = re.search(r'(\d+)\s+passed', line)

                if failed_match:
                    failed = int(failed_match.group(1))
                if passed_match:
                    passed = int(passed_match.group(1))

        # Extract coverage percentage from TOTAL line
        coverage_pct = 0
        for line in output.split('\n'):
            if "TOTAL" in line:
                # Line format: "TOTAL    2595   1035    60%"
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        # Last column is coverage percentage
                        coverage_str = parts[-1].rstrip('%')
                        coverage_pct = int(coverage_str)
                    except (ValueError, IndexError):
                        pass

        total_tests = passed + failed

        # Determine status
        if result.returncode == 0:
            status = "success"
            message = f"{passed} passed, {coverage_pct}% coverage"
        else:
            if failed > 0:
                status = "error"
                message = f"{failed} failed, {passed} passed, {coverage_pct}% coverage"
            else:
                status = "error"
                message = "tests failed"

        return StepResult(
            name="Python Tests + Coverage",
            status=status,
            duration=0,
            message=message,
            details={
                "passed": passed,
                "failed": failed,
                "total": total_tests,
                "coverage_pct": coverage_pct
            }
        )

    def _analyze_complexity(self) -> StepResult:
        """Analyze cyclomatic complexity with radon"""
        cmd = [
            str(self.venv_bin / "radon"),
            "cc",
            "packages/sd-generator-cli/sd_generator_cli",
            "--exclude=tests,__pycache__",
            "-a",
            "-nb",
            "--json"
        ]

        result = self._run_command(cmd)

        if result.returncode != 0:
            return StepResult(
                name="Complexity Analysis",
                status="warning",
                duration=0,
                message="radon not found or failed"
            )

        try:
            data = json.loads(result.stdout)

            # Calculate average complexity and find high complexity functions
            complexities = []
            high_complexity = []

            for file_path, functions in data.items():
                for func in functions:
                    complexity = func.get('complexity', 0)
                    complexities.append(complexity)
                    if complexity > 10:
                        high_complexity.append({
                            'file': file_path,
                            'function': func.get('name', 'unknown'),
                            'line': func.get('lineno', 0),
                            'complexity': complexity
                        })

            avg_complexity = sum(complexities) / len(complexities) if complexities else 0
            high_count = len(high_complexity)

            # Sort by complexity
            high_complexity.sort(key=lambda x: x['complexity'], reverse=True)

            status = "success" if avg_complexity < 5 and high_count == 0 else "warning"
            message = f"avg {avg_complexity:.1f}, {high_count} functions > 10"

            return StepResult(
                name="Complexity Analysis",
                status=status,
                duration=0,
                message=message,
                details={
                    "avg_complexity": avg_complexity,
                    "high_complexity_count": high_count,
                    "high_complexity_functions": high_complexity[:5]
                }
            )

        except json.JSONDecodeError:
            return StepResult(
                name="Complexity Analysis",
                status="warning",
                duration=0,
                message="Failed to parse radon output"
            )

    def _detect_dead_code(self) -> StepResult:
        """Detect dead code with vulture"""
        cmd = [
            str(self.venv_bin / "vulture"),
            "packages/sd-generator-cli/sd_generator_cli",
            "--min-confidence=80",
            "--exclude=tests"
        ]

        result = self._run_command(cmd)

        # Count unused items
        lines = [l for l in result.stdout.split('\n') if l.strip() and not l.startswith('#')]
        unused_count = len(lines)

        status = "success" if unused_count == 0 else "warning"
        message = f"{unused_count} unused items" if unused_count > 0 else "no dead code"

        return StepResult(
            name="Dead Code Detection",
            status=status,
            duration=0,
            message=message,
            details={
                "unused_count": unused_count,
                "unused_items": lines[:5]  # Top 5
            }
        )

    def _scan_security(self) -> StepResult:
        """Run security scan with bandit"""
        cmd = [
            str(self.venv_bin / "bandit"),
            "-r",
            "packages/sd-generator-cli/sd_generator_cli",
            "-ll",
            "-f",
            "json"
        ]

        result = self._run_command(cmd)

        if result.returncode == 1 and not result.stdout:
            # bandit not found
            return StepResult(
                name="Security Scan",
                status="warning",
                duration=0,
                message="bandit not found or failed"
            )

        try:
            data = json.loads(result.stdout)
            results = data.get('results', [])

            high = len([r for r in results if r.get('issue_severity') == 'HIGH'])
            medium = len([r for r in results if r.get('issue_severity') == 'MEDIUM'])
            low = len([r for r in results if r.get('issue_severity') == 'LOW'])

            if high > 0 or medium > 0:
                status = "error"
                message = f"{high} high, {medium} medium, {low} low"
            elif low > 0:
                status = "warning"
                message = f"{low} low severity issues"
            else:
                status = "success"
                message = "no vulnerabilities"

            return StepResult(
                name="Security Scan",
                status=status,
                duration=0,
                message=message,
                details={
                    "high": high,
                    "medium": medium,
                    "low": low,
                    "issues": results[:5]
                }
            )

        except json.JSONDecodeError:
            return StepResult(
                name="Security Scan",
                status="warning",
                duration=0,
                message="Failed to parse bandit output"
            )

    # ==================== Frontend Checks ====================

    def _lint_frontend(self) -> StepResult:
        """Run ESLint on frontend"""
        frontend_dir = self.project_root / "packages/sd-generator-webui/front"

        if not frontend_dir.exists():
            return StepResult(
                name="Frontend Linting",
                status="warning",
                duration=0,
                message="frontend directory not found"
            )

        cmd = ["npm", "run", "lint"]
        result = self._run_command(cmd, cwd=frontend_dir)

        if result.returncode == 0:
            return StepResult(
                name="Frontend Linting",
                status="success",
                duration=0,
                message="0 errors"
            )
        else:
            # Count errors in output
            error_count = result.stdout.count("error")
            return StepResult(
                name="Frontend Linting",
                status="error",
                duration=0,
                message=f"{error_count} errors",
                details={"error_count": error_count}
            )

    def _build_frontend(self) -> StepResult:
        """Build frontend with Vue.js"""
        frontend_dir = self.project_root / "packages/sd-generator-webui/front"

        if not frontend_dir.exists():
            return StepResult(
                name="Frontend Build",
                status="warning",
                duration=0,
                message="frontend directory not found"
            )

        cmd = ["npm", "run", "build"]
        result = self._run_command(cmd, cwd=frontend_dir)

        if result.returncode == 0:
            # Try to get build size
            dist_dir = frontend_dir / "dist"
            size_mb = 0.0
            if dist_dir.exists():
                total_bytes = sum(
                    f.stat().st_size for f in dist_dir.rglob('*') if f.is_file()
                )
                size_mb = total_bytes / (1024 * 1024)

            return StepResult(
                name="Frontend Build",
                status="success",
                duration=0,
                message=f"{size_mb:.1f} MB" if size_mb > 0 else "completed",
                details={"size_mb": size_mb}
            )
        else:
            return StepResult(
                name="Frontend Build",
                status="error",
                duration=0,
                message="build failed"
            )

    # ==================== Packaging ====================

    def _package_python(self) -> StepResult:
        """Build Python package with Poetry"""
        cli_dir = self.project_root / "packages/sd-generator-cli"

        cmd = ["poetry", "build"]
        result = self._run_command(cmd, cwd=cli_dir)

        if result.returncode == 0:
            # Find generated files
            dist_dir = cli_dir / "dist"
            files = list(dist_dir.glob("*")) if dist_dir.exists() else []
            file_names = [f.name for f in files]

            return StepResult(
                name="Python Packaging",
                status="success",
                duration=0,
                message=f"{len(files)} files created",
                details={"files": file_names}
            )
        else:
            return StepResult(
                name="Python Packaging",
                status="error",
                duration=0,
                message="packaging failed"
            )

    # ==================== Reporting ====================

    def _generate_report(self, total_duration: float):
        """Generate final report"""
        console.print("\n")

        # Build summary table
        table = Table(title="Build Report", border_style="cyan")
        table.add_column("Step", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Message", style="white")

        for result in self.results:
            status_symbol = {
                "success": "[green]✓[/green]",
                "warning": "[yellow]⚠[/yellow]",
                "error": "[red]✗[/red]",
                "skipped": "[dim]-[/dim]"
            }[result.status]

            table.add_row(
                result.name,
                status_symbol,
                result.message
            )

        console.print(table)

        # Overall status
        error_count = sum(1 for r in self.results if r.status == "error")
        warning_count = sum(1 for r in self.results if r.status == "warning")

        if error_count > 0:
            overall = f"[red]✗ FAILED ({error_count} errors)[/red]"
        elif warning_count > 0:
            overall = f"[yellow]⚠ WARNING ({warning_count} warnings)[/yellow]"
        else:
            overall = "[green]✓ SUCCESS[/green]"

        console.print(f"\nOverall: {overall}")
        console.print(f"Total duration: {total_duration:.1f}s\n")

        # Priority actions
        actions = self._get_priority_actions()
        if actions:
            self._print_priority_actions(actions)

    def _get_priority_actions(self) -> List[Action]:
        """Calculate top 5 priority actions"""
        actions = []

        for result in self.results:
            if not result.details:
                continue

            # Security issues
            if result.name == "Security Scan":
                high = result.details.get('high', 0)
                medium = result.details.get('medium', 0)
                if high > 0 or medium > 0:
                    for issue in result.details.get('issues', [])[:3]:
                        actions.append(Action(
                            priority=10 if issue.get('issue_severity') == 'HIGH' else 8,
                            category="SECURITY",
                            description=f"Fix {issue.get('issue_severity', '').lower()} severity: {issue.get('issue_text', 'unknown')}",
                            location=f"{issue.get('filename', 'unknown')}:{issue.get('line_number', 0)}"
                        ))

            # Type errors
            if result.name == "Python Type Checking":
                error_count = result.details.get('error_count', 0)
                if error_count > 0:
                    actions.append(Action(
                        priority=8,
                        category="TYPE",
                        description=f"Fix {error_count} type checking errors",
                        current_value=str(error_count),
                        target_value="0"
                    ))

            # Complexity
            if result.name == "Complexity Analysis":
                high_funcs = result.details.get('high_complexity_functions', [])
                for func in high_funcs[:3]:
                    actions.append(Action(
                        priority=6,
                        category="COMPLEXITY",
                        description=f"Reduce complexity in {func['function']}()",
                        location=f"{Path(func['file']).name}:{func['line']}",
                        current_value=str(func['complexity']),
                        target_value="< 10"
                    ))

            # Coverage
            if result.name == "Python Tests + Coverage":
                coverage = result.details.get('coverage_pct', 100)
                if coverage < 80:
                    actions.append(Action(
                        priority=7,
                        category="COVERAGE",
                        description="Improve overall test coverage",
                        current_value=f"{coverage}%",
                        target_value="> 80%"
                    ))

                # Add specific modules with low coverage
                # Parse coverage output for modules < 80%
                # This would require storing the full coverage table in details
                # For now, just flag overall coverage

            # Dead code
            if result.name == "Dead Code Detection":
                unused_items = result.details.get('unused_items', [])
                for item in unused_items[:2]:
                    if item.strip():
                        actions.append(Action(
                            priority=3,
                            category="DEAD_CODE",
                            description=f"Remove unused: {item.strip()}"
                        ))

        # Sort by priority and take top 5
        actions.sort(key=lambda a: a.priority, reverse=True)
        return actions[:5]

    def _print_priority_actions(self, actions: List[Action]):
        """Print priority actions panel"""
        lines = []
        for i, action in enumerate(actions, 1):
            lines.append(f"[bold]{i}. [{action.category}][/bold] {action.description}")
            if action.location:
                lines.append(f"   Location: {action.location}")
            if action.current_value and action.target_value:
                lines.append(f"   Current: {action.current_value}, Target: {action.target_value}")
            if i < len(actions):
                lines.append("")

        console.print(Panel(
            "\n".join(lines),
            title="Top 5 Priority Actions",
            border_style="yellow"
        ))


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Complete build and quality checks for local-sd-generator"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip tests and coverage"
    )
    parser.add_argument(
        "--skip-frontend",
        action="store_true",
        help="Skip frontend linting and build"
    )
    parser.add_argument(
        "--skip-package",
        action="store_true",
        help="Skip Python packaging"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full command output"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure"
    )

    args = parser.parse_args()

    # Determine project root (script is in tools/, root is parent)
    project_root = Path(__file__).parent.parent.resolve()

    runner = BuildRunner(
        project_root=project_root,
        skip_tests=args.skip_tests,
        skip_frontend=args.skip_frontend,
        skip_package=args.skip_package,
        verbose=args.verbose,
        fail_fast=args.fail_fast
    )

    exit_code = runner.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
