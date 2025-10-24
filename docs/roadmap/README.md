# Roadmap

Feature planning and implementation tracking for SD Image Generator.

## 📊 Project Planning - Now on GitHub Issues

**All roadmap items have been migrated to GitHub Issues** for better tracking, collaboration, and visibility.

🔗 **View Roadmap:** https://github.com/oinant/local-sd-generator/issues

## 🏷️ Issue Organization

Issues are organized using labels:

### Status Labels
- `status: done` - Completed features (closed)
- `status: next` - Priority features for current/next sprint (open)
- `status: backlog` - Future features to be prioritized (open)
- `status: wip` - Work in progress (open)

### Type Labels
- `type: feature` - New functionality
- `type: bug` - Bug fixes
- `type: refactor` - Code refactoring
- `type: chore` - Maintenance and tooling
- `type: docs` - Documentation improvements

### Priority Labels
- `priority: critical` (P1-3) - Critical features/bugs
- `priority: high` (P4-6) - Important enhancements
- `priority: medium` (P7-8) - Nice-to-have features
- `priority: low` (P9-10) - Research/experimental

### Component Labels
- `component: cli` - CLI tool
- `component: api` - Backend API
- `component: webapp` - Web UI
- `component: tooling` - Development tools

### Area Labels (Sub-components)
- `area: templating` - Template system
- `area: execution` - Execution and orchestration
- `area: api-client` - SD API client
- `area: config` - Configuration management

## 📋 Quick Links

### Current Work
- [🚀 Next Sprint](https://github.com/oinant/local-sd-generator/issues?q=is%3Aopen+label%3A%22status%3A+next%22)
- [🔄 In Progress](https://github.com/oinant/local-sd-generator/issues?q=is%3Aopen+label%3A%22status%3A+wip%22)

### Backlog
- [📦 Backlog](https://github.com/oinant/local-sd-generator/issues?q=is%3Aopen+label%3A%22status%3A+backlog%22)
- [High Priority](https://github.com/oinant/local-sd-generator/issues?q=is%3Aopen+label%3A%22priority%3A+high%22)
- [Critical](https://github.com/oinant/local-sd-generator/issues?q=is%3Aopen+label%3A%22priority%3A+critical%22)

### History
- [✅ Completed Features](https://github.com/oinant/local-sd-generator/issues?q=is%3Aclosed+label%3A%22status%3A+done%22)

### By Component
- [CLI Issues](https://github.com/oinant/local-sd-generator/issues?q=is%3Aopen+label%3A%22component%3A+cli%22)
- [Templating Issues](https://github.com/oinant/local-sd-generator/issues?q=is%3Aopen+label%3A%22area%3A+templating%22)
- [WebApp Issues](https://github.com/oinant/local-sd-generator/issues?q=is%3Aopen+label%3A%22component%3A+webapp%22)

## 📝 Creating New Issues

When creating a new feature request or bug report:

1. **Use appropriate labels** (type, priority, component, area)
2. **Include clear description** of what and why
3. **Add acceptance criteria** for definition of done
4. **Link related issues** if applicable

## 🎯 Priority Guidelines

- **Critical (P1-3)**: Blocking bugs, essential features for current sprint
- **High (P4-6)**: Important enhancements, planned for next sprint
- **Medium (P7-8)**: Nice-to-have features, future consideration
- **Low (P9-10)**: Research, experimental ideas

## 📊 Statistics

Total GitHub Issues: **45**
- ✅ Completed: **29** (closed)
- 🔄 Active: **16** (open)
  - Next sprint: **3**
  - Backlog: **12**
  - Others: **1**

_Last updated: 2025-10-24_

## 📖 Local Notes & Braindump

**Ongoing ideas and braindump tracking:**
- 📋 [braindump.md](../../.claude/braindump.md) - Captures ideas during Claude Code sessions
  - Survives context compaction
  - Tracks items through lifecycle: 🆕 Pending → 🔍 Analyzing → 📋 Tracked → ✅ Done
  - Always check "🆕 Pending Analysis" section for ideas awaiting structuring

**Usage:**
- Add rough ideas to "💭 Unstructured Notes"
- Agent PO processes "🆕 Pending" items into GitHub Issues
- Links back to GitHub Issues once created
