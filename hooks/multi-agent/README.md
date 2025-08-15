# Multi-Agent Orchestration System

A comprehensive multi-agent orchestration system for collaborative architectural design, detailed implementation specifications, and working code generation through parallel agent execution, competitive evaluation, and intelligent delegation.

## Overview

This system transforms simple commands into sophisticated multi-agent workflows across three tiers:

1. **Architecture Design** (`/design`) - High-level system architecture
2. **Implementation Specifications** (`/feat`) - Detailed implementation designs with exact section structure preservation
3. **Code Generation** (`/dev`) - Working source code files

## Quick Start

```bash
# Generate system architecture
./orchestrate.py design go pomodoro timer

# Create detailed implementation specification for section 1
./orchestrate.py feat 1

# Generate working Go code for the timer core feature
./orchestrate.py dev go feat timer-core
```

## Architecture

### Directory Structure

```
/hooks/multi_agent/
├── core/                          # Core orchestration components
│   ├── command_parser.py          # Command parsing and validation
│   ├── orchestration_engine.py    # Agent coordination and execution
│   ├── language_detection.py      # Project language detection
│   ├── agent_registry.py          # Agent discovery and management
│   └── persistence.py             # State persistence and archiving
├── config/                        # Configuration files
│   ├── orchestration_config.json  # Main orchestration settings
│   └── language_agents.json       # Language-to-agent mappings
├── evaluators/                    # Evaluation logic components
│   ├── design_evaluator.py        # Design quality assessment
│   ├── feat_evaluator.py          # Feature implementation assessment
│   └── code_evaluator.py          # Code quality assessment
├── workflows/                     # Workflow orchestration scripts
│   ├── design_workflow.py         # /design command workflow
│   ├── feat_workflow.py           # /feat command workflow
│   └── dev_workflow.py            # /dev command workflow
├── utils/                         # Shared utility functions
│   ├── file_manager.py            # File operations and cleanup
│   └── validation.py              # Input and output validation
├── orchestrate.py                 # Main command-line interface
├── app.md                         # Detailed system specification
└── README.md                      # This file
```

### Key Components

#### Command Parser
- Parses `/design`, `/feat`, and `/dev` commands
- Validates syntax and extracts parameters
- Supports language specification and auto-detection

#### Language Detection Engine
- Analyzes project context for language identification
- Uses config files (90% confidence), source files (70% confidence), and patterns (50% confidence)
- Falls back to user prompts or main Claude when confidence is low

#### Agent Registry
- Discovers and validates available agents
- Maps languages to appropriate architect and developer agents
- Tracks agent performance and health metrics

#### Orchestration Engine
- Manages parallel agent execution using subprocess isolation
- Handles timeouts, resource management, and process monitoring
- Coordinates agent tasks with proper input/output handling

#### Evaluation System
- **Design Evaluator**: Assesses architectural quality using weighted criteria
- **Feature Evaluator**: Validates implementation specifications with structural preservation
- **Code Evaluator**: Analyzes code quality, testing, and project structure

#### Persistence Manager
- Manages file lifecycle: generation → selection → placement → cleanup
- Archives non-selected candidates with metadata
- Handles `.docs/plan/` structure for permanent files

## Command Reference

### `/design` Command

Generate high-level system architecture using parallel architect agents.

```bash
/design [language] <description>
```

**Examples:**
```bash
/design go pomodoro timer          # Language-specific (uses gad)
/design pomodoro timer             # Auto-detect language
/design microservice-architecture  # Multi-service design
```

**Output:** `app.md` with selected architectural design

### `/feat` Command

Transform architecture sections into detailed implementation specifications.

```bash
/feat <section_identifier>
```

**Examples:**
```bash
/feat 1            # Implement section 1 from app.md
/feat timer-core   # Implement named section
/feat 2.3          # Implement specific subsection
```

**Critical Constraint:** Output `feat_N.md` MUST preserve exact subsection structure from `app.md` section N.

**Output:** `feat_N.md` with detailed implementation specifications

### `/dev` Command

Generate working source code from feature specifications.

```bash
/dev [language] feat <section_identifier>
```

**Examples:**
```bash
/dev feat 1                # Generate code for feat_1.md (uses god/pydv)
/dev go feat timer-core    # Language-specific generation (uses god)
/dev feat 1,3,5           # Multiple specifications
```

**Output:** Complete language-appropriate directory structure with working code files

## Language Support

### Supported Languages

| Language   | Architect Agent | Developer Agent | Project Structure |
|------------|----------------|------------------|-------------------|
| Go         | `gad`          | `god`           | `cmd/`, `internal/`, `pkg/`, `test/` |
| Python     | `pyad`         | `pydv`          | `src/`, `tests/`, `docs/` |
| Rust       | `rustarch`     | `rustdev`       | `src/`, `tests/`, `examples/` |
| JavaScript | `jsad`         | `jsdev`         | `src/`, `lib/`, `test/`, `dist/` |
| TypeScript | `tsad`         | `tsdev`         | `src/`, `lib/`, `test/`, `dist/`, `types/` |

### Agent Capabilities Matrix

| Agent | Architecture | Implementation | Code Review | Microservices |
|-------|-------------|----------------|-------------|---------------|
| gad   | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| pyad  | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| jsad  | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

## Evaluation Framework

### Design Quality Matrix
- **Language Idioms (25%)**: Adherence to language conventions and best practices
- **Architecture (25%)**: Technical correctness, scalability, and soundness
- **Implementability (20%)**: Practical implementation feasibility and clarity
- **Completeness (15%)**: Thoroughness of architectural coverage
- **Innovation (10%)**: Creative and elegant solutions
- **Documentation (5%)**: Clarity and comprehensiveness

### Feature Specification Criteria
- **Structural Integrity (30%)**: Exact subsection structure preservation
- **Implementation Detail (25%)**: Depth and specificity of implementation guidance
- **Language Specificity (20%)**: Language-specific patterns and approaches
- **Technical Accuracy (15%)**: Technical correctness and feasibility
- **Clarity (10%)**: Readability and comprehensiveness

### Code Quality Assessment
- **Code Quality (25%)**: Syntax, style, complexity, and maintainability
- **Test Coverage (20%)**: Presence and quality of test files
- **Documentation (15%)**: Comments, README, and code documentation
- **Project Structure (15%)**: Proper organization and file layout
- **Language Idioms (15%)**: Language-specific best practices
- **Build Readiness (10%)**: Build configuration and dependencies

## Configuration

### Orchestration Settings

Edit `/config/orchestration_config.json`:

```json
{
  "orchestration": {
    "design_parallel_agent_count": 5,
    "feat_parallel_agent_count": 5,
    "dev_parallel_agent_count": 5,
    "execution_timeout_seconds": 300
  },
  "user_approval": {
    "user_design_approval": true,
    "user_feat_approval": false,
    "user_dev_approval": false
  }
}
```

### Language-Agent Mapping

Edit `/config/language_agents.json` to customize agent assignments and capabilities.

## File Organization

### Output Structure

```
.docs/
├── plan/
│   ├── app.md              # Selected architecture design
│   ├── feat_1.md           # Selected feature implementations
│   └── feat_2.md
└── archive/
    ├── designs/[timestamp]/    # Archived design alternatives
    ├── feats/[timestamp]/      # Archived feature alternatives
    └── code/[timestamp]/       # Archived code alternatives
```

### Generated Code Structure

**Go Projects:**
```
src/
├── cmd/                    # Application entry points
├── internal/               # Private packages
├── pkg/                    # Public API packages
├── test/                   # Integration tests
└── docs/                   # Generated documentation
```

**Python Projects:**
```
src/
├── [project_name]/         # Main package
├── tests/                  # Test suites
├── docs/                   # Documentation
└── pyproject.toml          # Project metadata
```

## Usage Examples

### Complete Three-Tier Workflow

```bash
# Tier 1: Architecture Design
./orchestrate.py design go pomodoro timer
# Output: app.md with high-level system architecture

# Tier 2: Implementation Specifications  
./orchestrate.py feat 1    # Timer Core Engine detailed implementation
./orchestrate.py feat 3    # Configuration Management detailed implementation
# Output: feat_1_timer_core.md, feat_3_config_management.md

# Tier 3: Working Code Generation
./orchestrate.py dev feat 1    # Generate timer core code
./orchestrate.py dev feat 3    # Generate configuration code
# Output: Complete Go project structure with working code files
```

### Language-Specific Examples

```bash
# Explicit language specification
./orchestrate.py design python web scraper
./orchestrate.py design rust cli tool
./orchestrate.py design javascript react app

# Auto-detection based on project context
./orchestrate.py design web scraper          # Detects Python from pyproject.toml
./orchestrate.py design cli tool             # Detects Go from go.mod
```

## Error Handling and Fallbacks

### Agent Availability
- **Primary**: Use specialized agents (e.g., `gad`, `god`)
- **Secondary**: Use generic architecture/development agents
- **Fallback**: Main Claude with enhanced context and prompting

### Quality Assurance
- **Validation**: Input validation, output verification, structural integrity
- **Evaluation**: Competitive ranking using weighted criteria
- **User Approval**: Optional interactive approval for design selection
- **Archiving**: Comprehensive archiving of alternatives with metadata

## Performance and Monitoring

### Execution Metrics
- **Response Time**: Target <60 seconds for complete orchestration
- **Success Rate**: >95% successful completion rate
- **Quality Score**: >4.0/5.0 average evaluation rating
- **Agent Availability**: >99% uptime for core agents

### Resource Management
- **Process Isolation**: Each agent runs in separate subprocess
- **Timeout Handling**: Configurable timeouts with graceful degradation
- **Memory Management**: Automatic cleanup of temporary files and processes
- **Concurrency Control**: Managed parallel execution with resource limits

## Integration

This system integrates with the broader Claude Code ecosystem:

- **Agent Discovery**: Automatic scanning of `~/.claude/agents/`
- **Command System**: Integrated with Claude Code slash commands
- **Hook System**: Compatible with existing Claude Code hooks
- **Persistence**: Uses standardized `.docs/` structure

## Development and Extension

### Adding New Languages

1. Update `language_agents.json` with new language configuration
2. Ensure appropriate architect and developer agents exist
3. Add language-specific evaluation patterns
4. Test with sample projects

### Creating Custom Agents

1. Create agent definition in `~/.claude/agents/`
2. Include capability descriptions for automatic discovery
3. Test agent performance with orchestration system
4. Update language mappings as needed

### Extending Evaluation Criteria

1. Modify evaluator classes in `evaluators/` directory
2. Update configuration files with new weights
3. Test evaluation changes with sample outputs
4. Document new criteria in appropriate command files

## Troubleshooting

### Common Issues

1. **No agents found**: Ensure agents exist in `~/.claude/agents/`
2. **Language detection failed**: Specify language explicitly or check project structure
3. **Structural validation failed**: Verify `app.md` exists and has proper section structure
4. **Agent timeout**: Increase timeout in configuration or check agent availability

### Debug Mode

```bash
./orchestrate.py --log-level DEBUG design go timer
```

### Log Files

Check logs in `/logs/orchestration.log` for detailed execution information.

## Contributing

When contributing to the multi-agent orchestration system:

1. Follow the modular architecture principles
2. Add comprehensive tests for new functionality
3. Update configuration files appropriately
4. Document new features in command definitions
5. Ensure backward compatibility with existing workflows

## License

This multi-agent orchestration system is part of the Claude Code configuration repository and follows the same licensing terms.