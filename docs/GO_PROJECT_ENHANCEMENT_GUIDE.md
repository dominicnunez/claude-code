# Go Project Enhancement Guide

## Overview
This guide explains how to use `go-learn` and `go-project-agent` together to enhance your Go agents with project-specific patterns and conventions.

## The Two-Agent System

### 1. `go-learn` (`/glearn`)
- **Purpose**: Analyzes your Go codebase to extract patterns, conventions, and architectural decisions
- **Output**: Structured YAML enhancement specifications
- **When to use**: When you want to capture your project's unique patterns

### 2. `go-project-agent` (`/gpa`)
- **Purpose**: Takes go-learn's output and enhances any Go agent with project-specific knowledge
- **How it works**: Edits existing agent files in-place, adding "Project-Specific Enhancements" sections
- **When to use**: After running go-learn, to customize agents for your project

## Step-by-Step Workflow

### Step 1: Analyze Your Project
```bash
/glearn analyze my crypto trading bot project
```

This will output a YAML specification containing:
- Architecture patterns (layered, hexagonal, microservices, etc.)
- Coding conventions (naming, organization, error handling)
- Implementation patterns (testing, logging, dependencies)
- Domain-specific logic and constraints

### Step 2: Review the Output
The go-learn agent will provide structured data like:
```yaml
# Project Analysis & Enhancement Specifications

## Architecture Overview
pattern: hexagonal
packages:
  - name: internal/domain
    responsibility: Core business logic
    patterns: Entity models, value objects

## Enhancement Specifications for gad.md
### Architecture Decisions
- decision: Use hexagonal architecture
  rationale: Clean separation of concerns
  example: |
    internal/
      domain/     # Core business logic
      ports/      # Interfaces
      adapters/   # External implementations

## Enhancement Specifications for go-code.md
### Coding Conventions
- pattern: Use 'Repo' suffix for repositories
  example: OrderRepo, UserRepo
```

### Step 3: Enhance Your Target Agent
Choose which agent to enhance based on your needs:

#### For Architecture Decisions (gad):
```bash
/gpa enhance gad with the project patterns
```

#### For Code Implementation (go-code):
```bash
/gpa enhance go-code with the project patterns
```

#### For Any Custom Agent:
```bash
/gpa enhance [agent-name] with the project patterns
```

### Step 4: Verify the Enhancement
The enhanced agent will now include a clearly marked section:
```markdown
## Project-Specific Enhancements
_Last updated: 2024-01-15 from crypto-trading-bot analysis_
_Target agent: gad_

### Architecture Decisions
[Your project's specific patterns]

### Project Guidelines
[Your team's conventions]
```

## Common Use Cases

### Use Case 1: New Team Member Onboarding
1. Run go-learn on your production codebase
2. Enhance gad and go-code with project patterns
3. New developers can use `/gad` and `/gcode` with built-in knowledge of your conventions

### Use Case 2: Maintaining Consistency
1. Periodically run go-learn to capture evolving patterns
2. Update agents with latest conventions
3. All code generation follows current best practices

### Use Case 3: Project-Specific Debugging
1. Analyze your error handling patterns with go-learn
2. Create or enhance a debugging agent with your patterns
3. Get project-aware debugging assistance

## Best Practices

### Running go-learn
- **Be specific about scope**: "analyze internal/ directory" vs "analyze entire project"
- **Run periodically**: Patterns evolve, update quarterly or after major refactors
- **Review output**: Ensure captured patterns align with your intentions

### Enhancing Agents
- **Start with core agents**: Enhance gad and go-code first
- **Be selective**: Only enhance agents you actively use
- **Document changes**: The enhancement date and project name are automatically added
- **Keep base functionality**: Enhancements add to, never replace, core capabilities

### Maintaining Enhancements
- **Re-run after major changes**: Architecture shifts, new patterns adopted
- **Version control**: Commit enhanced agents to your project repo
- **Team alignment**: Share enhanced agents with your team

## Advanced Workflows

### Creating Project-Specific Agent Suite
```bash
# 1. Analyze your project comprehensively
/glearn analyze entire codebase including tests and docs

# 2. Enhance all relevant agents
/gpa enhance gad with architecture patterns
/gpa enhance go-code with implementation patterns
/gpa enhance go-debugger with error patterns

# 3. Create shortcuts for your team
# Now your team can use project-aware commands:
/gad    # Architecture decisions with your patterns
/gcode  # Code generation following your conventions
```

### Migrating Between Projects
```bash
# Working on Project A
/glearn analyze project-a
/gpa enhance gad with project-a patterns

# Switching to Project B
/glearn analyze project-b
/gpa enhance gad with project-b patterns
# Note: This replaces project-a enhancements
```

## Troubleshooting

### Issue: Enhancements seem generic
**Solution**: Ensure your codebase has consistent patterns before running go-learn. Inconsistent code yields vague patterns.

### Issue: Agent not using project patterns
**Solution**: Verify the enhancement section exists in the agent file and the agent was enhanced after the latest go-learn run.

### Issue: Patterns conflict with Go best practices
**Solution**: go-learn captures what exists, not what should be. Review and potentially refactor before capturing patterns.

## Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `/glearn` | Analyze codebase | `/glearn analyze my project` |
| `/gpa` | Enhance agent | `/gpa enhance gad with patterns` |
| `/gad` | Use enhanced gad | `/gad design a new service` |
| `/gcode` | Use enhanced go-code | `/gcode implement user repository` |

## Summary

The go-learn + go-project-agent workflow enables:
1. **Automatic pattern extraction** from your codebase
2. **Agent customization** with your specific conventions
3. **Consistency enforcement** across your team
4. **Knowledge preservation** of architectural decisions

By following this guide, your Go agents become project-aware assistants that understand and follow your team's unique patterns and conventions.