# ALIN-Maint Workflow Changelog

## [v2.1] - 2025-12-09

### Changed
- **Breaking Change**: Moved ops context directory from `.claude/ops-context` to `.alin/ops-context`
- **Breaking Change**: Moved ops documentation directory from `.claude/ops-docs` to `.alin/ops-docs`

### Rationale
- Consolidate ALIN-Maint specific data under `.alin/` namespace
- Separate operational context from Claude Code configuration
- Align with ALIN branding and organization structure

### Migration Guide

If you have existing ops context from v2.0, migrate it:

```bash
# Backup existing data
cp -r .claude/ops-context .alin/ops-context
cp -r .claude/ops-docs .alin/ops-docs

# Optional: Remove old location
rm -rf .claude/ops-context
rm -rf .claude/ops-docs
```

### Files Updated
- `commands/alin-maint.md` - Main orchestrator
- `agents/alin-maint-init.md` - Init agent
- `agents/alin-maint-monitor.md` - Monitor agent
- `agents/alin-maint-deploy.md` - Deploy agent
- `agents/alin-maint-incident.md` - Incident agent
- `agents/alin-maint-security.md` - Security agent
- `agents/alin-maint-optimize.md` - Optimize agent
- `README.md` - Documentation

### Total Changes
- 35 path references updated across 8 files
- 0 remaining references to `.claude/ops-*`

## [v2.0] - 2025-12-09

### Added
- Context7 MCP integration for real-time documentation
- Mandatory context loading workflow
- Interactive investigation mode (5 rounds max)
- Command approval system (read-only → confirmation → dangerous)
- Entity detection and knowledge base auto-update
- Incremental mode support (service/server/issue/config)

### Core Improvements
1. Mandatory context loading from infra-profile.md
2. Interactive investigation (not one-shot)
3. Command approval only (never auto-execute)
