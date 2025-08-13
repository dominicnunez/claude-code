# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is the **main Claude Code configuration repository** - a centralized, version-controlled source of truth for all Claude Code configurations, agents, hooks, workflows, and commands. This repository serves as:

- **Central Agent Library** - All non-project-specific agents are defined and maintained here
- **Workflow Templates** - Reusable orchestration patterns and multi-agent workflows
- **Hook System** - Standardized hooks for controlling Claude Code behavior across all projects
- **Command Center** - Custom slash commands available system-wide
- **Configuration Hub** - Settings and preferences for Claude Code operations

## Key Architecture

### Sub-Agent System
**This repository is the authoritative source for all user-level agents**

**Agent Management:**
- Agents defined here are available across ALL projects via `~/.claude/agents/` symlink
- Project-specific agents can still be created in individual project `.claude/agents/` directories
- This repo maintains the master copies for version control and distribution

**Core Agents Maintained Here:**
- **meta-agent** - Creates and modifies other agents (model: opus)
- **gad** - Go architecture design specialist
- **god** - Go implementation specialist
- **go-learn** - Analyzes Go codebases to extract patterns
- **go-project-agent** - Enhances Go agents with project patterns
- **nixa** - NixOS configuration specialist
- **rick-sanchez-coder** - Cynical but effective coding assistant
- **horror-writer** - Creative writing specialist
- **prompt-engineer-agent** - Prompt engineering and agent design
- **llm-ai-agents-and-eng-research** - AI research and news aggregator
- **work-completion-summary** - Audio summary generator with TTS
- **performance-toptimizer** - Performance optimization specialist

### Hook System
**Centralized hook implementations for consistent behavior across all projects**

**Hook Files:** `.claude/hooks/`
- All hooks use UV single-file scripts for portability
- Can be symlinked or copied to project-specific `.claude/hooks/` directories
- Provides consistent security, logging, and enhancement across all Claude Code usage

**Standard Hooks:**
- `user_prompt_submit.py` - Validates/enhances prompts before processing
- `pre_tool_use.py` - Security validation before tool execution
- `post_tool_use.py` - Result logging and transcript conversion
- `stop.py` - Completion messages with TTS
- `session_start.py` - Development context loading
- `notification.py` - Notification handling with optional TTS
- `subagent_stop.py` - Subagent completion handling
- `pre_compact.py` - Pre-compaction backup and logging

### Multi-Agent Orchestration Patterns
**Reusable workflow templates for complex tasks**

Python orchestration scripts:
- `hooks/multi_agent/multi_agent_design.py` - Parallel design exploration pattern
- `hooks/multi_agent/multi_agent_base.py` - Base class for custom orchestrations
- `hooks/multi_agent/single_feature_design.py` - Feature-focused design workflow
- `hooks/multi_agent/single_feature_implementer.py` - Implementation workflow
- `hooks/multi_agent/iterative_design_system.py` - Iterative refinement pattern
- `hooks/multi_agent/readme_generator.py` - Documentation generation workflow

### Custom Commands
**System-wide slash commands defined in `commands/`**

General Commands:
- `/start` - Initialize with CLAUDE.md and TODO.md
- `/prime` - Load development context
- `/all_tools` - List available tools
- `/git_status` - Check git status

Go Development Commands:
- `/gad` - Go architecture design
- `/god` - Go implementation
- `/glearn` - Learn project patterns
- `/gpa` - Apply project patterns
- `/gcode` - Go code generation
- `/gtg` - Go test generation

Workflow Commands:
- `/ma` - Multi-agent design
- `/design` - Single feature design
- `/feat` - Feature implementation
- `/code` - Code implementation
- `/readme` - Generate README

## Repository Structure

```
.claude/
├── agents/                 # Master agent definitions
├── commands/              # Slash command definitions
├── hooks/                 # Hook implementations
│   ├── utils/            # Shared utilities (TTS, LLM)
│   ├── multi_agent/      # Multi-agent orchestration scripts
│   └── discord/          # Discord bot integration files
├── logs/                 # Hook execution logs
├── docs/                 # Documentation and guides
│   └── ai_docs/         # AI-specific documentation
├── projects/             # Project-specific data
├── todos/                # Task tracking
├── settings.json         # Core configuration
└── settings.local.json   # Local overrides (not in git)
```

## Deployment and Usage

### Setting Up New Machines
1. Clone this repository to `~/.claude`
2. Symlink or copy needed components to project `.claude/` directories
3. Configure `settings.local.json` for machine-specific settings

### Creating Project-Specific Configurations
1. Create `.claude/` in project root
2. Symlink agents: `ln -s ~/.claude/agents .claude/agents`
3. Copy and customize hooks as needed
4. Add project-specific `CLAUDE.md`

### Version Control Strategy
- This repo is the single source of truth for all agents
- Commit agent improvements here, not in individual projects
- Use branches for experimental agents/workflows
- Tag stable releases for deployment

## Development Workflow

### Adding New Agents
1. Design agent in this repository
2. Test locally with various prompts
3. Commit and push to version control
4. Available immediately via `~/.claude/agents/`

### Improving Existing Agents
1. Edit agent file in `agents/`
2. Test changes thoroughly
3. Commit with descriptive message
4. Changes propagate to all projects

### Creating New Workflows
1. Develop orchestration script in repository root
2. Create corresponding command in `commands/`
3. Document usage in this file
4. Test across different project types

## Best Practices

### For This Repository
- **Keep agents generic** - Project-specific logic belongs in project repos
- **Document changes** - Update CLAUDE.md when adding features
- **Test thoroughly** - Changes affect all Claude Code usage
- **Use semantic commits** - Clear commit messages for tracking changes

### For Agent Development
- **One agent, one purpose** - Keep agents focused and specialized
- **Use opus model** - Set `model: opus` for maximum capability
- **Clear descriptions** - Enable automatic delegation with good descriptions
- **Minimal tools** - Only request necessary tools for security

### For Hook Development
- **Fail safely** - Never break Claude Code with hook errors
- **Log everything** - Comprehensive logging for debugging
- **Use exit code 2 wisely** - Only block when absolutely necessary
- **Keep hooks fast** - 60-second timeout limit

## Integration with Projects

When working in any project with Claude Code:
1. This repository provides the base agents and hooks
2. Project-specific `.claude/` directories can override or extend
3. Use `/start` command to load both this CLAUDE.md and project CLAUDE.md
4. Agents from this repo are always available as fallbacks

## Maintenance

### Regular Tasks
- Review and update agent descriptions for clarity
- Archive deprecated agents to `agents/archive/`
- Update documentation for new features
- Clean old logs periodically
- Test hooks after Claude Code updates

### Versioning
- Major versions for breaking changes
- Minor versions for new agents/features
- Patch versions for bug fixes
- Tag releases for stable deployments

## Critical Git Reminders
- NEVER include "Generated with Claude Code" in commit messages.
- NEVER include "Co-Authored-By Claude" in commit messages
- NEVER refer to "phases" in commit messages
- NEVER force-add gitignored files
- NEVER commit sensitive data (API keys, passwords)
