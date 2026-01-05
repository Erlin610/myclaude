# Claude Code Multi-Agent Workflow System Makefile
# Quick deployment for BMAD and Requirements workflows

.PHONY: help install deploy-bmad deploy-requirements deploy-essentials deploy-advanced deploy-all deploy-commands deploy-agents clean test

# Default target
help:
	@echo "Claude Code Multi-Agent Workflow - Quick Deployment"
	@echo ""
	@echo "Recommended installation: python3 install.py --install-dir ~/.claude"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install              - LEGACY: install all configurations (prefer install.py)"
	@echo "  deploy-bmad          - Deploy BMAD workflow (bmad-pilot)"
	@echo "  deploy-requirements  - Deploy Requirements workflow (requirements-pilot)"
	@echo "  deploy-essentials    - Deploy Development Essentials workflow"
	@echo "  deploy-advanced      - Deploy Advanced AI Agents"
	@echo "  deploy-commands      - Deploy all slash commands"
	@echo "  deploy-agents        - Deploy all agent configurations"
	@echo "  deploy-all           - Deploy everything (commands + agents)"
	@echo "  test-bmad            - Test BMAD workflow with sample"
	@echo "  test-requirements    - Test Requirements workflow with sample"
	@echo "  clean                - Clean generated artifacts"
	@echo "  help                 - Show this help message"

# Configuration paths
CLAUDE_CONFIG_DIR = ~/.claude
SPECS_DIR = .claude/specs

# Workflow directories
BMAD_DIR = bmad-agile-workflow
REQUIREMENTS_DIR = requirements-driven-workflow
ESSENTIALS_DIR = development-essentials
ADVANCED_DIR = advanced-ai-agents
OUTPUT_STYLES_DIR = output-styles

# Install all configurations
install: deploy-all
	@echo "⚠️  LEGACY PATH: make install will be removed in future versions."
	@echo "    Prefer: python3 install.py --install-dir ~/.claude"
	@echo "✅ Installation complete!"

# Deploy BMAD workflow
deploy-bmad:
	@echo "🚀 Deploying BMAD workflow..."
	@mkdir -p $(CLAUDE_CONFIG_DIR)/commands
	@mkdir -p $(CLAUDE_CONFIG_DIR)/agents
	@mkdir -p $(CLAUDE_CONFIG_DIR)/output-styles
	@cp $(BMAD_DIR)/commands/bmad-pilot.md $(CLAUDE_CONFIG_DIR)/commands/
	@cp $(BMAD_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@cp $(OUTPUT_STYLES_DIR)/bmad.md $(CLAUDE_CONFIG_DIR)/output-styles/ 2>/dev/null || true
	@echo "✅ BMAD workflow deployed successfully!"
	@echo "   Usage: /bmad-pilot \"your feature description\""

# Deploy Requirements workflow
deploy-requirements:
	@echo "🚀 Deploying Requirements workflow..."
	@mkdir -p $(CLAUDE_CONFIG_DIR)/commands
	@mkdir -p $(CLAUDE_CONFIG_DIR)/agents
	@cp $(REQUIREMENTS_DIR)/commands/requirements-pilot.md $(CLAUDE_CONFIG_DIR)/commands/
	@cp $(REQUIREMENTS_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@echo "✅ Requirements workflow deployed successfully!"
	@echo "   Usage: /requirements-pilot \"your feature description\""

# Deploy Development Essentials workflow
deploy-essentials:
	@echo "🚀 Deploying Development Essentials workflow..."
	@mkdir -p $(CLAUDE_CONFIG_DIR)/commands
	@mkdir -p $(CLAUDE_CONFIG_DIR)/agents
	@cp $(ESSENTIALS_DIR)/commands/*.md $(CLAUDE_CONFIG_DIR)/commands/
	@cp $(ESSENTIALS_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@echo "✅ Development Essentials deployed successfully!"
	@echo "   Available commands: /ask, /code, /debug, /test, /review, /optimize, /bugfix, /refactor, /docs, /think"

# Deploy Advanced AI Agents
deploy-advanced:
	@echo "🚀 Deploying Advanced AI Agents..."
	@mkdir -p $(CLAUDE_CONFIG_DIR)/agents
	@cp $(ADVANCED_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@echo "✅ Advanced AI Agents deployed successfully!"


# Deploy all commands
deploy-commands:
	@echo "📦 Deploying all slash commands..."
	@mkdir -p $(CLAUDE_CONFIG_DIR)/commands
	@cp $(BMAD_DIR)/commands/*.md $(CLAUDE_CONFIG_DIR)/commands/
	@cp $(REQUIREMENTS_DIR)/commands/*.md $(CLAUDE_CONFIG_DIR)/commands/
	@cp $(ESSENTIALS_DIR)/commands/*.md $(CLAUDE_CONFIG_DIR)/commands/
	@echo "✅ All commands deployed!"
	@echo "   Available commands:"
	@echo "   - /bmad-pilot (Full agile workflow)"
	@echo "   - /requirements-pilot (Requirements-driven)"
	@echo "   - /ask, /code, /debug, /test, /review"
	@echo "   - /optimize, /bugfix, /refactor, /docs, /think"

# Deploy all agents
deploy-agents:
	@echo "🤖 Deploying all agents..."
	@mkdir -p $(CLAUDE_CONFIG_DIR)/agents
	@cp $(BMAD_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@cp $(REQUIREMENTS_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@cp $(ESSENTIALS_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@cp $(ADVANCED_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@echo "✅ All agents deployed!"

# Deploy everything
deploy-all: deploy-commands deploy-agents
	@mkdir -p $(CLAUDE_CONFIG_DIR)/output-styles
	@cp $(OUTPUT_STYLES_DIR)/*.md $(CLAUDE_CONFIG_DIR)/output-styles/ 2>/dev/null || true
	@echo "✨ Full deployment complete!"
	@echo ""
	@echo "Quick Start:"
	@echo "  BMAD:         /bmad-pilot \"build user authentication\""
	@echo "  Requirements: /requirements-pilot \"implement JWT auth\""
	@echo "  Manual:       /ask → /code → /test → /review"

# Test BMAD workflow
test-bmad:
	@echo "🧪 Testing BMAD workflow..."
	@echo "Run in Claude Code:"
	@echo '/bmad-pilot "Simple todo list with add/delete functions"'

# Test Requirements workflow
test-requirements:
	@echo "🧪 Testing Requirements workflow..."
	@echo "Run in Claude Code:"
	@echo '/requirements-pilot "Basic CRUD API for products"'

# Clean generated artifacts
clean:
	@echo "🧹 Cleaning artifacts..."
	@rm -rf $(SPECS_DIR)
	@echo "✅ Cleaned!"

# Quick deployment shortcuts
bmad: deploy-bmad
requirements: deploy-requirements
essentials: deploy-essentials
advanced: deploy-advanced
all: deploy-all

# Version info
version:
	@echo "Claude Code Multi-Agent Workflow System v3.1"
	@echo "BMAD + Requirements-Driven Development"

# Claude Code Multi-Agent Workflow System Makefile
# Quick deployment for BMAD and Requirements workflows

.PHONY: help install deploy-bmad deploy-requirements deploy-essentials deploy-advanced deploy-alin deploy-all deploy-commands deploy-agents clean test install-workflow alin-dev-to alin-dev-to-cc alin-dev-to-droid
.ONESHELL:

# Default target
help:
	@echo "Claude Code Multi-Agent Workflow - Quick Deployment"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install              - Install all configurations to Claude Code"
	@echo "  deploy-bmad          - Deploy BMAD workflow (bmad-pilot)"
	@echo "  deploy-requirements  - Deploy Requirements workflow (requirements-pilot)"
	@echo "  deploy-essentials    - Deploy Development Essentials workflow"
	@echo "  deploy-advanced      - Deploy Advanced AI Agents"
	@echo "  deploy-commands      - Deploy all slash commands"
	@echo "  deploy-agents        - Deploy all agent configurations"
	@echo "  deploy-all           - Deploy everything (commands + agents)"
	@echo "  install-workflow     - Install a workflow into a TARGET project"
	@echo "  alin-dev-to          - Convenience: install alin-dev to TARGET (ENV=cc|droid)"
	@echo "  alin-dev-to-cc       - Convenience: install alin-dev to TARGET for CC"
	@echo "  alin-dev-to-droid    - Convenience: install alin-dev to TARGET for Droid"
	@echo "  test-bmad            - Test BMAD workflow with sample"
	@echo "  test-requirements    - Test Requirements workflow with sample"
	@echo "  clean                - Clean generated artifacts"
	@echo "  help                 - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make install-workflow WORKFLOW=alin-dev ENV=cc TARGET=/path/to/project"
	@echo "  make install-workflow WORKFLOW=alin-dev ENV=droid TARGET=/path/to/project"
	@echo "  make alin-dev-to ENV=droid TARGET=/path/to/project"
	@echo "  make alin-dev-to-cc TARGET=/path/to/project"
	@echo "  make alin-dev-to-droid TARGET=/path/to/project"

# Configuration paths
CLAUDE_CONFIG_DIR = ~/.claude
SPECS_DIR = .claude/specs

# Workflow directories
BMAD_DIR = bmad-agile-workflow
REQUIREMENTS_DIR = requirements-driven-workflow
ESSENTIALS_DIR = development-essentials
ADVANCED_DIR = advanced-ai-agents
OUTPUT_STYLES_DIR = output-styles

# Install all configurations
install: deploy-all
	@echo "✅ Installation complete!"

# Deploy BMAD workflow
deploy-bmad:
	@echo "🚀 Deploying BMAD workflow..."
	@mkdir -p $(CLAUDE_CONFIG_DIR)/commands
	@mkdir -p $(CLAUDE_CONFIG_DIR)/agents
	@mkdir -p $(CLAUDE_CONFIG_DIR)/output-styles
	@cp $(BMAD_DIR)/commands/bmad-pilot.md $(CLAUDE_CONFIG_DIR)/commands/
	@cp $(BMAD_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@cp $(OUTPUT_STYLES_DIR)/bmad.md $(CLAUDE_CONFIG_DIR)/output-styles/ 2>/dev/null || true
	@echo "✅ BMAD workflow deployed successfully!"
	@echo "   Usage: /bmad-pilot \"your feature description\""

# Deploy Requirements workflow
deploy-requirements:
	@echo "🚀 Deploying Requirements workflow..."
	@mkdir -p $(CLAUDE_CONFIG_DIR)/commands
	@mkdir -p $(CLAUDE_CONFIG_DIR)/agents
	@cp $(REQUIREMENTS_DIR)/commands/requirements-pilot.md $(CLAUDE_CONFIG_DIR)/commands/
	@cp $(REQUIREMENTS_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@echo "✅ Requirements workflow deployed successfully!"
	@echo "   Usage: /requirements-pilot \"your feature description\""

# Deploy Development Essentials workflow
deploy-essentials:
	@echo "🚀 Deploying Development Essentials workflow..."
	@mkdir -p $(CLAUDE_CONFIG_DIR)/commands
	@mkdir -p $(CLAUDE_CONFIG_DIR)/agents
	@cp $(ESSENTIALS_DIR)/commands/*.md $(CLAUDE_CONFIG_DIR)/commands/
	@cp $(ESSENTIALS_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@echo "✅ Development Essentials deployed successfully!"
	@echo "   Available commands: /ask, /code, /debug, /test, /review, /optimize, /bugfix, /refactor, /docs, /think"

# Deploy Advanced AI Agents
deploy-advanced:
	@echo "🚀 Deploying Advanced AI Agents..."
	@mkdir -p $(CLAUDE_CONFIG_DIR)/agents
	@cp $(ADVANCED_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@echo "✅ Advanced AI Agents deployed successfully!"


# Deploy all commands
deploy-commands:
	@echo "📦 Deploying all slash commands..."
	@mkdir -p $(CLAUDE_CONFIG_DIR)/commands
	@cp $(BMAD_DIR)/commands/*.md $(CLAUDE_CONFIG_DIR)/commands/
	@cp $(REQUIREMENTS_DIR)/commands/*.md $(CLAUDE_CONFIG_DIR)/commands/
	@cp $(ESSENTIALS_DIR)/commands/*.md $(CLAUDE_CONFIG_DIR)/commands/
	@echo "✅ All commands deployed!"
	@echo "   Available commands:"
	@echo "   - /bmad-pilot (Full agile workflow)"
	@echo "   - /requirements-pilot (Requirements-driven)"
	@echo "   - /ask, /code, /debug, /test, /review"
	@echo "   - /optimize, /bugfix, /refactor, /docs, /think"

# Deploy all agents
deploy-agents:
	@echo "🤖 Deploying all agents..."
	@mkdir -p $(CLAUDE_CONFIG_DIR)/agents
	@cp $(BMAD_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@cp $(REQUIREMENTS_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@cp $(ESSENTIALS_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@cp $(ADVANCED_DIR)/agents/*.md $(CLAUDE_CONFIG_DIR)/agents/
	@echo "✅ All agents deployed!"

# Deploy everything
deploy-all: deploy-commands deploy-agents
	@mkdir -p $(CLAUDE_CONFIG_DIR)/output-styles
	@cp $(OUTPUT_STYLES_DIR)/*.md $(CLAUDE_CONFIG_DIR)/output-styles/ 2>/dev/null || true
	@echo "✨ Full deployment complete!"
	@echo ""
	@echo "Quick Start:"
	@echo "  BMAD:         /bmad-pilot \"build user authentication\""
	@echo "  Requirements: /requirements-pilot \"implement JWT auth\""
	@echo "  Manual:       /ask → /code → /test → /review"

# Test BMAD workflow
test-bmad:
	@echo "🧪 Testing BMAD workflow..."
	@echo "Run in Claude Code:"
	@echo '/bmad-pilot "Simple todo list with add/delete functions"'

# Test Requirements workflow
test-requirements:
	@echo "🧪 Testing Requirements workflow..."
	@echo "Run in Claude Code:"
	@echo '/requirements-pilot "Basic CRUD API for products"'

# Clean generated artifacts
clean:
	@echo "🧹 Cleaning artifacts..."
	@rm -rf $(SPECS_DIR)
	@echo "✅ Cleaned!"

# Quick deployment shortcuts
bmad: deploy-bmad
requirements: deploy-requirements
essentials: deploy-essentials
advanced: deploy-advanced
all: deploy-all

# Version info
version:
	@echo "Claude Code Multi-Agent Workflow System v3.1"
	@echo "BMAD + Requirements-Driven Development"

# Generic installer: copy workflow to a target project for cc/droid
# Usage:
#   make install-workflow WORKFLOW=alin-dev ENV=cc TARGET=/abs/path
#   make install-workflow WORKFLOW=alin-dev ENV=droid TARGET=/abs/path
install-workflow:
	@ENV="$(ENV)" TARGET="$(TARGET)" WORKFLOW="$(WORKFLOW)" sh -eu -c ' \
	  if [ -z "$$ENV" ]; then echo "ENV is required (cc|droid)"; exit 1; fi; \
	  if [ -z "$$TARGET" ]; then echo "TARGET is required (absolute path)"; exit 1; fi; \
	  if [ -z "$$WORKFLOW" ]; then echo "WORKFLOW is required (e.g., alin-dev)"; exit 1; fi; \
	  WF_DIR="$$WORKFLOW-$$ENV-workflow"; \
	  if [ ! -d "$$WF_DIR" ]; then \
	    WF_DIR="$$WORKFLOW-workflow"; \
	    if [ ! -d "$$WF_DIR" ]; then echo "Workflow directory not found: $$WF_DIR"; exit 1; fi; \
	    echo "Using fallback directory: $$WF_DIR"; \
	  fi; \
	  TARGET_DIR="$$TARGET"; \
	  if [ ! -d "$$TARGET_DIR" ]; then echo "TARGET does not exist: $$TARGET_DIR"; exit 1; fi; \
	  if [ "$$ENV" = "cc" ]; then \
	    echo "Installing $$WF_DIR to $$TARGET_DIR/.claude"; \
	    mkdir -p "$$TARGET_DIR/.claude/commands" "$$TARGET_DIR/.claude/agents"; \
	    cp "$$WF_DIR/commands/"*.md "$$TARGET_DIR/.claude/commands/"; \
	    cp "$$WF_DIR/agents/"*.md "$$TARGET_DIR/.claude/agents/"; \
	    echo "Installed for CC at $$TARGET_DIR/.claude"; \
	  elif [ "$$ENV" = "droid" ]; then \
	    echo "Installing $$WF_DIR to $$TARGET_DIR/.factory"; \
	    mkdir -p "$$TARGET_DIR/.factory/commands" "$$TARGET_DIR/.factory/droids"; \
	    cp "$$WF_DIR/commands/"*.md "$$TARGET_DIR/.factory/commands/"; \
	    cp "$$WF_DIR/agents/"*.md "$$TARGET_DIR/.factory/droids/"; \
	    echo "Installed for Droid at $$TARGET_DIR/.factory"; \
	  else \
	    echo "Unknown ENV: $$ENV. Use cc or droid."; exit 1; \
	  fi; \
	'

# Convenience wrappers for alin-dev
alin-dev-to:
	@$(MAKE) install-workflow WORKFLOW=alin-dev ENV=$(ENV) TARGET="$(TARGET)"

alin-dev-to-cc:
	@$(MAKE) install-workflow WORKFLOW=alin-dev ENV=cc TARGET="$(TARGET)"

alin-dev-to-droid:
	@$(MAKE) install-workflow WORKFLOW=alin-dev ENV=droid TARGET="$(TARGET)"