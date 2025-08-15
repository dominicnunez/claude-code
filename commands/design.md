# /design - Multi-Agent Architecture Design Command

Generate high-level system architecture using parallel architect agents with competitive evaluation and selection.

## Usage

```bash
/design [language] <description>
```

## Examples

```bash
/design go pomodoro timer          # Language-specific design (uses gad)
/design pomodoro timer             # Auto-detect language from project
/design microservice-architecture  # Multi-service system design
/design python web scraper         # Python-specific web scraper
/design rust cli tool              # Rust command-line application
```

## Description

The `/design` command orchestrates parallel execution of multiple architect agents to generate comprehensive system architecture designs. The system uses competitive evaluation to select the best design from multiple candidates.

### Key Features

- **Parallel Agent Execution**: Runs 5 architect agents simultaneously for diverse perspectives
- **Language Detection**: Automatically detects target language from project context
- **Competitive Evaluation**: Uses weighted criteria to select optimal design
- **User Approval**: Optional interactive approval process
- **Automatic Archiving**: Non-selected designs are archived for reference

### Execution Flow

1. **Parse Command**: Extract language and description parameters
2. **Language Detection**: Auto-detect if not specified via project analysis
3. **Agent Selection**: Choose appropriate architect agents for the language
4. **Parallel Generation**: Execute multiple agents with identical prompts
5. **Evaluation**: Rank designs using weighted quality criteria
6. **User Approval**: Present selected design for review (if enabled)
7. **Persistence**: Save selected design as `app.md`, archive alternatives

### Evaluation Criteria

Designs are evaluated using weighted criteria:

- **Language Idioms (25%)**: Adherence to language conventions and best practices
- **Architecture (25%)**: Technical correctness, scalability, and soundness
- **Implementability (20%)**: Practical implementation feasibility and clarity
- **Completeness (15%)**: Thoroughness of architectural coverage
- **Innovation (10%)**: Creative and elegant solutions
- **Documentation (5%)**: Clarity and comprehensiveness

### Output

The command generates:

- **`app.md`**: Selected architectural design document
- **Archive**: Non-selected alternatives with evaluation metadata
- **Metadata**: Execution metrics and evaluation scores

### Language Support

Automatic agent selection for supported languages:

- **Go**: Uses `gad` (Go Architecture Design) agent
- **Python**: Uses `pyad` (Python Architecture Design) agent
- **Rust**: Uses `rustarch` agent
- **JavaScript**: Uses `jsad` agent
- **TypeScript**: Uses `tsad` agent
- **Java**: Uses `javaarch` agent
- **C#**: Uses `csarch` agent
- **C++**: Uses `cpparch` agent

For unsupported languages or when no language is specified, the system uses generic architecture agents or falls back to main Claude.

### Configuration

Behavior can be customized via `orchestration_config.json`:

```json
{
  "orchestration": {
    "design_parallel_agent_count": 5,
    "execution_timeout_seconds": 300
  },
  "user_approval": {
    "user_design_approval": true
  }
}
```

### Error Handling

- **No Agents Available**: Falls back to main Claude with appropriate context
- **Language Detection Failed**: Prompts user for language specification
- **All Agents Failed**: Returns error with diagnostic information
- **User Rejection**: Allows selection of alternative designs

### Integration

The `/design` command integrates with the complete multi-agent workflow:

1. **Design Phase**: `/design` creates high-level architecture
2. **Feature Phase**: `/feat` elaborates specific sections
3. **Development Phase**: `/dev` generates working code

Each phase builds upon the previous, ensuring consistency and traceability throughout the development process.

## Implementation

The command is implemented by the `DesignWorkflow` class in `/hooks/multi_agent/workflows/design_workflow.py`, which orchestrates:

- Command parsing and validation
- Language detection and agent selection
- Parallel agent execution via subprocess isolation
- Competitive evaluation and ranking
- User interaction and approval workflow
- File persistence and archiving

This ensures reliable, high-quality architectural designs through collaborative AI agent workflows.