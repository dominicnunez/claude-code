# Appendix: Multi-Agent Orchestration System Reference

## 1. System Overview

The multi-agent orchestration system enables collaborative architectural design, detailed implementation specifications, and working code generation through parallel agent execution, competitive evaluation, and intelligent delegation. This three-tier system transforms simple commands into sophisticated multi-agent workflows:

1. **Architecture Design** (`/design`) - High-level system architecture
2. **Implementation Specifications** (`/feat`) - Detailed implementation designs with exact section structure preservation
3. **Code Generation** (`/dev`) - Working source code files

### Key Principles
- **Agent Consistency**: Same agents (e.g., `gad`, `pyad`) handle both `/design` and `/feat` for coherence
- **Structure Preservation**: `/feat N` generates exact subsection structure as section N in `app.md`
- **Quality Assurance**: Competitive evaluation selects best designs from parallel candidates

### System Components
- **Command Router**: Parses user input and determines execution strategy
- **Language Detection Engine**: Identifies target language and maps to appropriate agents  
- **Agent Orchestration Engine**: Manages parallel agent execution and coordination
- **Evaluation System**: Coordinates design evaluation and selection processes
- **Quality Assurance System**: Validates code quality, testing, and integration

## 2. Core Architecture

### Orchestration Engine
The core orchestration engine manages parallel agent execution using subprocess calls to Claude Code:

```python
# Agent spawning pattern
process = await asyncio.create_subprocess_exec(
    'claude-code', '--agent', agent_name, '--input', prompt_file,
    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
)
```

### Language Detection
Automatic language detection analyzes project context:
- **Primary indicators** (config files): 90% confidence
- **Secondary indicators** (source files): 70% confidence
- **Minimum threshold**: 60% confidence
- **Fallback**: Prompt user or use main Claude

### Agent Isolation
- **Process Isolation**: Each agent runs in separate Claude Code session
- **Context Isolation**: No shared memory or state between parallel agents
- **Output Isolation**: Temporary files prevent cross-contamination
- **Time Isolation**: Parallel execution prevents temporal bias

### Evaluation Framework
Competitive evaluation using weighted criteria:
- **Language Idioms**: 25% - Adherence to language conventions
- **Architecture**: 25% - Technical correctness and scalability
- **Implementability**: 20% - Practical implementation feasibility
- **Completeness**: 15% - Thoroughness of coverage
- **Innovation**: 10% - Creative and elegant solutions
- **Documentation**: 5% - Clarity and comprehensiveness

## 3. Command Reference

### `/design` Command
Generate high-level system architecture using parallel **architect agents** (e.g., `gad` for Go, `pyad` for Python).

**Usage:**
```bash
/design go pomodoro timer          # Language-specific (uses gad)
/design pomodoro timer             # Auto-detect language
/design microservice-architecture  # Multi-service design
```

**Execution Flow:**
1. **Parse** language and description
2. **Deploy** 5 parallel architect agents with identical prompt
3. **Evaluate** all candidates using same architect agent
4. **Generate** final `app.md` with selected design
5. **Archive** non-selected candidates with metadata

### `/feat` Command
Transform architecture sections into detailed implementation specifications using **architect agents** (same as `/design`).

**Usage:**
```bash
/feat 1            # Implement section 1 from app.md
/feat timer-core   # Implement named section
/feat 2.3          # Implement specific subsection
```

**Critical Constraint:**
Output `feat_N.md` MUST preserve exact subsection structure from `app.md` section N.

**Validation:**
- Exact subsection match (no missing, no extra)
- Consistent numbering and titles
- Structural preservation enforced

### `/dev` Command
Generate working source code from feature specifications using **developer agents** (e.g., `god` for Go, `pydv` for Python).

**Usage:**
```bash
/dev feat 1                # Generate code for feat_1_*.md (uses god/pydv)
/dev go feat timer-core    # Language-specific generation (uses god)
/dev feat 1,3,5           # Multiple specifications
```

**Output:**
Complete language-appropriate directory structure with:
- Working source code files
- Comprehensive test suites
- Documentation and configuration
- Build and deployment scripts

## 4. Configuration Reference

### Orchestration Configuration
```json
// /hooks/multi_agent/config/orchestration_config.json
{
  "orchestration": {
    "design_parallel_agent_count": 5,
    "feat_parallel_agent_count": 5,
    "dev_parallel_agent_count": 5,
    "execution_timeout_seconds": 300,
    "minimum_agents_for_orchestration": 3
  },
  "language_detection": {
    "confidence_threshold": 0.6,
    "file_scan_depth": 3
  },
  "user_approval": {
    "user_design_approval": true,
    "user_feat_approval": false,
    "user_dev_approval": false
  },
  "fallback_strategies": {
    "enable_main_claude_fallback": true,
    "prompt_user_on_low_confidence": true
  }
}
```

### Language-Agent Mapping
```json
// /hooks/multi_agent/config/language_agents.json
{
  "languages": {
    "go": {
      "architect": "gad",
      "developer": "god",
      "confidence_threshold": 0.8,
      "file_extensions": [".go"],
      "config_files": ["go.mod", "go.sum"]
    },
    "python": {
      "architect": "pyad",
      "developer": "pydv",
      "confidence_threshold": 0.8,
      "file_extensions": [".py"],
      "config_files": ["pyproject.toml", "requirements.txt"]
    }
  }
}
```

### Agent Capabilities Matrix
| Agent | Architecture | Implementation | Code Review | Microservices |
|-------|-------------|----------------|-------------|---------------|
| gad   | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| pyad  | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| jsad  | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| tsad  | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

## 5. File Organization

### Core Directory Structure
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
└── utils/                         # Shared utility functions
    ├── file_manager.py            # File operations and cleanup
    └── validation.py              # Input and output validation
```

### Output File Organization
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

## 6. Agent Management

### Agent Discovery
Automatic scanning of `/home/aural/.claude/agents/` for architecture agents:
- **Capability Detection**: Parse agent descriptions for architecture design capabilities
- **Language Affinity**: Identify language-specific agents by naming patterns  
- **Registry Update**: Automatically update language_agents.json with discovered agents
- **Validation**: Test agents with sample architecture tasks

### Agent Health Monitoring
- **Performance Metrics**: Track response times and success rates
- **Resource Usage**: Monitor memory and CPU consumption
- **Failure Handling**: Automatic fallback to secondary agents
- **Load Balancing**: Distribute workload across available agents

### Fallback Strategies
- **Agent Unavailable**: Route to main Claude with full language context
- **Low Confidence**: Prompt user for language specification
- **Partial Failure**: Proceed with available agent results
- **No Agents**: Use main Claude directly with enhanced prompting

## 7. Quality Framework

### Evaluation Criteria
Weighted assessment framework for competitive evaluation:

**Design Quality Matrix:**
- **Language Idioms (25%)**: Adherence to language conventions and best practices
- **Architecture (25%)**: Technical correctness, scalability, and soundness
- **Implementability (20%)**: Practical implementation feasibility and clarity
- **Completeness (15%)**: Thoroughness of architectural coverage
- **Innovation (10%)**: Creative and elegant solutions
- **Documentation (5%)**: Clarity and comprehensiveness

### Validation Framework
1. **Syntax Validation**: Ensure descriptions are clear and complete
2. **Consistency Validation**: Check alignment with language-specific best practices
3. **Completeness Validation**: Verify all required aspects are covered
4. **Structure Validation**: Enforce exact subsection preservation for `/feat`

### Section Structure Preservation
**Critical Constraint**: `/feat N` output must preserve exact subsection structure from `app.md` section N.

**Validation Rules:**
- Exact subsection match (no missing, no extra)
- Consistent numbering and titles
- Structural integrity enforced

### Performance Targets
- **Response Time**: <60 seconds for complete orchestration
- **Success Rate**: >95% successful completion
- **Quality Score**: >4.0/5.0 average rating
- **Agent Availability**: >99% uptime

## 8. Implementation Guide

### Agent Spawning Implementation
Proper agent invocation following Claude Code documentation:

```python
# Core agent spawning pattern
process = await asyncio.create_subprocess_exec(
    'claude-code', '--agent', agent_name, '--input', prompt_file,
    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
)
```

**Key Principles:**
- Use subprocess with claude-code CLI
- Pass agent name via --agent flag
- Handle timeouts through process management
- Clean up temporary files and processes
- Monitor execution via process status

### File Lifecycle Management
Four-stage workflow for candidate file management:

1. **Generation**: Temporary files in `.docs/` root during active generation
2. **Selection**: Evaluator analyzes candidates, user approval if enabled
3. **Placement**: Selected candidate moved to `plan/` folder as permanent file
4. **Cleanup**: Non-selected candidates archived with timestamp, temporaries removed

### User Approval Workflow
Optional interactive approval for design selection:

**Configuration Options:**
```json
{
  "user_approval": {
    "user_design_approval": true,     // Enable for /design command
    "user_feat_approval": false,      // Enable for /feat command  
    "user_dev_approval": false        // Enable for /dev command
  }
}
```

**Approval Process:**
1. System generates 5 candidates with automatic evaluation
2. Present selected candidate with evaluation rationale
3. User options: Approve, Select Different, Request Modification, Regenerate
4. Process repeats until approval or max iterations reached

## 9. Usage Examples

### Complete Three-Tier Workflow
```bash
# Tier 1: Architecture Design
/design go pomodoro timer
# Output: app.md with high-level system architecture

# Tier 2: Implementation Specifications  
/feat 1    # Timer Core Engine detailed implementation
/feat 3    # Configuration Management detailed implementation
# Output: feat_1_timer_core.md, feat_3_config_management.md

# Tier 3: Working Code Generation
/dev feat 1    # Generate timer core code
/dev feat 3    # Generate configuration code
# Output: Complete Go project structure with working code files
```

### Language-Specific Examples
```bash
# Explicit language specification
/design python web scraper
/design rust cli tool
/design javascript react app

# Auto-detection based on project context
/design web scraper          # Detects Python from pyproject.toml
/design cli tool             # Detects Go from go.mod
```

### Section Structure Preservation Example
```
app.md Section 2:
2. User Interface Layer
   2.1 CLI Interface Design
   2.2 Display System Architecture
   2.3 User Input Handling

/feat 2 generates feat_2.md with:
2.1 CLI Interface Design
[detailed implementation specs]
2.2 Display System Architecture  
[detailed implementation specs]  
2.3 User Input Handling
[detailed implementation specs]
```
**Validation**: Exact structural match enforced

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

---

This reference guide provides a comprehensive overview of the multi-agent orchestration system architecture and implementation. The system is designed to be extensible, resilient, and capable of delivering high-quality architectural designs through collaborative AI agent workflows.

**Key Benefits:**
- **Maintainability**: Single source of truth with clear file organization
- **Extensibility**: Easy addition of new workflow types and agent integration
- **Reliability**: Proper error handling, resource management, and process monitoring
- **Performance**: Efficient concurrent execution with resource pooling and optimization

For detailed implementation, refer to the organized file structure under `/hooks/multi_agent/` with proper separation between core components, configuration, workflows, evaluators, and utilities.
