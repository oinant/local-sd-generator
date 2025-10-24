#!/usr/bin/env python3
"""
Migrate roadmap specs from docs/roadmap/done/ to GitHub Issues.

This script:
1. Parses all .md files in docs/roadmap/done/
2. Extracts metadata (title, status, priority, component, commits)
3. Creates GitHub issues with appropriate labels
4. Uses commit dates to date the issues
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class RoadmapSpec:
    """Represents a roadmap specification"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.title = ""
        self.status = ""
        self.priority = 0
        self.component = ""
        self.created = ""
        self.completed = ""
        self.description = ""
        self.commits = []
        self.full_content = ""

    def parse(self):
        """Parse the markdown file and extract metadata"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.full_content = content

        # Extract title (first # heading)
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if title_match:
            self.title = title_match.group(1).strip()
        else:
            self.title = self.file_path.stem.replace('-', ' ').title()

        # Extract metadata fields
        self.status = self._extract_field(content, 'Status')
        priority_str = self._extract_field(content, 'Priority')
        self.priority = int(priority_str) if priority_str.isdigit() else 5
        self.component = self._extract_field(content, 'Component')
        self.created = self._extract_field(content, 'Created')
        self.completed = self._extract_field(content, 'Completed')

        # Extract description (text between metadata and first ## heading)
        desc_match = re.search(
            r'\*\*Created:\*\*.*?\n\n(.+?)(?=\n##|\Z)',
            content,
            re.DOTALL
        )
        if desc_match:
            self.description = desc_match.group(1).strip()

        # Extract commit hashes
        commits_match = re.search(r'##\s+Commits.*?\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
        if commits_match:
            commits_text = commits_match.group(1)
            # Match patterns like "- abc1234: message" or "717e176 feat: message"
            for line in commits_text.split('\n'):
                hash_match = re.search(r'[a-f0-9]{7,40}', line)
                if hash_match:
                    self.commits.append(hash_match.group(0))

    def _extract_field(self, content: str, field_name: str) -> str:
        """Extract a metadata field value"""
        pattern = rf'\*\*{field_name}:\*\*\s*(.+?)(?:\s|$)'
        match = re.search(pattern, content)
        return match.group(1).strip() if match else ''

    def get_labels(self, target_status: str = 'done') -> List[str]:
        """Generate GitHub labels based on spec metadata"""
        # Map directory to status label
        status_map = {
            'done': 'status: done',
            'next': 'status: next',
            'future': 'status: backlog'
        }
        labels = [status_map.get(target_status, 'status: backlog')]

        # Type label (guess from title/content)
        title_lower = self.title.lower()
        if 'bug' in title_lower or 'fix' in title_lower:
            labels.append('type: bug')
        elif 'refactor' in title_lower or 'chore' in title_lower:
            if 'refactor' in title_lower:
                labels.append('type: refactor')
            else:
                labels.append('type: chore')
        elif 'doc' in title_lower:
            labels.append('type: docs')
        else:
            labels.append('type: feature')

        # Priority label
        if self.priority <= 3:
            labels.append('priority: critical')
        elif self.priority <= 6:
            labels.append('priority: high')
        elif self.priority <= 8:
            labels.append('priority: medium')
        else:
            labels.append('priority: low')

        # Component label
        if self.component:
            comp_lower = self.component.lower()
            if comp_lower in ['cli', 'webapp', 'api', 'tooling']:
                labels.append(f'component: {comp_lower}')

            # Area labels (sub-components)
            if 'templating' in self.title.lower() or 'template' in self.title.lower():
                labels.append('area: templating')
            elif 'config' in self.title.lower():
                labels.append('area: config')
            elif 'api' in self.title.lower() and comp_lower == 'cli':
                labels.append('area: api-client')
            elif 'execution' in self.title.lower() or 'manifest' in self.title.lower():
                labels.append('area: execution')

        return labels

    def get_commit_date(self) -> Optional[str]:
        """Get the date of the first commit (earliest date)"""
        if not self.commits:
            return None

        dates = []
        for commit_hash in self.commits:
            try:
                result = subprocess.run(
                    ['git', 'show', '-s', '--format=%ci', commit_hash],
                    capture_output=True,
                    text=True,
                    check=True
                )
                date_str = result.stdout.strip()
                if date_str:
                    dates.append(date_str)
            except subprocess.CalledProcessError:
                continue

        if dates:
            # Return earliest date
            dates.sort()
            return dates[0]
        return None

    def to_github_issue_body(self) -> str:
        """Format the spec content as a GitHub issue body"""
        body_parts = []

        # Add metadata section
        body_parts.append("## Metadata")
        body_parts.append(f"- **Status:** {self.status}")
        body_parts.append(f"- **Priority:** {self.priority}")
        body_parts.append(f"- **Component:** {self.component}")
        if self.created:
            body_parts.append(f"- **Created:** {self.created}")
        if self.completed:
            body_parts.append(f"- **Completed:** {self.completed}")
        if self.commits:
            body_parts.append(f"- **Commits:** {', '.join(self.commits[:5])}")  # First 5

        body_parts.append("")
        body_parts.append("---")
        body_parts.append("")

        # Add original spec content (skip first heading and metadata)
        content_lines = self.full_content.split('\n')
        skip_until_description = True

        for line in content_lines:
            # Skip title and metadata
            if skip_until_description:
                if line.startswith('## Description') or line.startswith('## Problem'):
                    skip_until_description = False
                    body_parts.append(line)
                continue
            body_parts.append(line)

        body_parts.append("")
        body_parts.append("---")
        # Use relative path from project root
        try:
            rel_path = self.file_path.relative_to(Path.cwd())
        except ValueError:
            rel_path = self.file_path
        body_parts.append(f"_Migrated from roadmap: `{rel_path}`_")

        return '\n'.join(body_parts)


def find_specs(directory: str) -> List[Path]:
    """Find all .md files in specified roadmap directory"""
    spec_dir = Path(f'docs/roadmap/{directory}')
    if not spec_dir.exists():
        print(f"Error: {spec_dir} not found")
        sys.exit(1)

    specs = list(spec_dir.glob('**/*.md'))
    # Filter out README files
    specs = [s for s in specs if s.name.lower() != 'readme.md']
    return specs


def create_github_issue(spec: RoadmapSpec, target_status: str = 'done', dry_run: bool = True, close_after: bool = True):
    """Create a GitHub issue from a spec"""
    title = spec.title
    body = spec.to_github_issue_body()
    labels = spec.get_labels(target_status)

    # Build gh command
    cmd = [
        'gh', 'issue', 'create',
        '--title', title,
        '--body', body,
        '--repo', 'oinant/local-sd-generator'
    ]

    # Add labels
    for label in labels:
        cmd.extend(['--label', label])

    if dry_run:
        print(f"\n{'='*80}")
        print(f"Would create issue: {title}")
        print(f"Labels: {', '.join(labels)}")
        if spec.commits:
            commit_date = spec.get_commit_date()
            if commit_date:
                print(f"Commit date: {commit_date}")
        print(f"Command: {' '.join(cmd)}")
        print(f"Body preview (first 300 chars):")
        print(body[:300] + "...")
    else:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            issue_url = result.stdout.strip()
            print(f"✓ Created: {issue_url}")

            # Add commit date comment if available
            if spec.commits:
                commit_date = spec.get_commit_date()
                if commit_date:
                    issue_number = issue_url.split('/')[-1]
                    comment = f"📅 This feature was completed on: {commit_date}\n\nCommits: {', '.join(spec.commits[:3])}"
                    subprocess.run([
                        'gh', 'issue', 'comment', issue_number,
                        '--body', comment,
                        '--repo', 'oinant/local-sd-generator'
                    ], check=True)

            # Close issue if requested (for done specs)
            if close_after and target_status == 'done':
                issue_number = issue_url.split('/')[-1]
                subprocess.run([
                    'gh', 'issue', 'close', issue_number,
                    '--repo', 'oinant/local-sd-generator',
                    '--reason', 'completed',
                    '--comment', '✅ Cette feature est complétée et provient de la roadmap.'
                ], check=True)
                print(f"  ✓ Closed as completed")

        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to create issue: {e}")
            print(f"  stdout: {e.stdout}")
            print(f"  stderr: {e.stderr}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate roadmap specs to GitHub issues')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be created without creating')
    parser.add_argument('--limit', type=int, help='Limit number of issues to create')
    parser.add_argument('--directory', default='done', help='Roadmap directory (done, next, future)')
    parser.add_argument('--close', action='store_true', help='Close issues after creation (for done/ specs)')
    args = parser.parse_args()

    print(f"Finding specs in docs/roadmap/{args.directory}/...")
    spec_files = find_specs(args.directory)
    print(f"Found {len(spec_files)} specs")

    if args.limit:
        spec_files = spec_files[:args.limit]
        print(f"Limiting to first {args.limit} specs")

    specs = []
    for file_path in spec_files:
        spec = RoadmapSpec(file_path)
        spec.parse()
        specs.append(spec)

    # Sort by priority (lower = more critical)
    specs.sort(key=lambda s: s.priority)

    print(f"\n{'='*80}")
    print("Creating GitHub issues...")
    print(f"{'='*80}")

    for i, spec in enumerate(specs, 1):
        print(f"\n[{i}/{len(specs)}] {spec.title}")
        create_github_issue(spec, target_status=args.directory, dry_run=args.dry_run, close_after=args.close)

    print(f"\n{'='*80}")
    if args.dry_run:
        print("DRY RUN: No issues were created")
        print("Run without --dry-run to actually create issues")
    else:
        print(f"✓ Created {len(specs)} issues")


if __name__ == '__main__':
    main()
