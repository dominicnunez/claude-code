# /dev - Multi-Agent Code Development Command

Generate working source code from feature specifications using parallel developer agents with comprehensive quality evaluation.

## Usage

```bash
/dev [language] feat <section_identifier>
/dev [language] feat <section_list>
```

## Examples

```bash
/dev feat 1                # Generate code for feat_1.md (auto-detect language)
/dev go feat timer-core    # Generate Go code for timer-core specification
/dev feat 1,3,5           # Generate code for multiple specifications
/dev python feat auth     # Generate Python code for authentication feature
/dev rust feat 2.1        # Generate Rust code for specific subsection
```

## Description

The `/dev` command generates complete, working source code from detailed feature specifications. It uses specialized developer agents to create production-ready codebases with comprehensive test suites, documentation, and proper project structure.

### Key Features

- **Working Code Generation**: Creates complete, executable project structures
- **Developer Agent Specialization**: Uses language-specific implementation agents
- **Quality Evaluation**: Comprehensive code quality assessment and ranking
- **Test Coverage**: Generates comprehensive test suites alongside implementation
- **Project Structure**: Creates appropriate directory organization for each language
- **Build Configuration**: Includes build files and dependency management

### Execution Flow

1. **Parse Command**: Extract language, target specification, and section identifiers
2. **Language Determination**: Auto-detect or validate specified language
3. **Specification Loading**: Load feature specification content from `feat_*.md`
4. **Agent Selection**: Choose appropriate developer agents for the language
5. **Parallel Generation**: Execute multiple developer agents with identical context
6. **Code Evaluation**: Assess code quality, testing, and project structure
7. **Selection**: Choose best implementation based on comprehensive criteria
8. **Persistence**: Save code to structured directory, archive alternatives

### Target Languages

The command supports comprehensive code generation for:

#### Go Development
- **Agent**: `god` (Go Developer)
- **Structure**: `cmd/`, `internal/`, `pkg/`, `test/`
- **Build**: `go.mod`, `go.sum`, `Makefile`
- **Features**: Goroutines, channels, interfaces, proper error handling

#### Python Development
- **Agent**: `pydv` (Python Developer)
- **Structure**: `src/`, `tests/`, `docs/`
- **Build**: `pyproject.toml`, `requirements.txt`, `setup.py`
- **Features**: Type hints, async/await, proper packaging

#### Rust Development
- **Agent**: `rustdev` (Rust Developer)
- **Structure**: `src/`, `tests/`, `examples/`, `benches/`
- **Build**: `Cargo.toml`, `Cargo.lock`
- **Features**: Ownership, borrowing, traits, memory safety

#### JavaScript Development
- **Agent**: `jsdev` (JavaScript Developer)
- **Structure**: `src/`, `lib/`, `test/`, `dist/`
- **Build**: `package.json`, `webpack.config.js`
- **Features**: Modern ES6+, async/await, modules

#### TypeScript Development
- **Agent**: `tsdev` (TypeScript Developer)
- **Structure**: `src/`, `lib/`, `test/`, `dist/`, `types/`
- **Build**: `tsconfig.json`, `package.json`
- **Features**: Strong typing, interfaces, generics

### Code Quality Evaluation

Generated code is evaluated using weighted criteria:

- **Code Quality (25%)**: Syntax, style, complexity, and maintainability
- **Test Coverage (20%)**: Presence and quality of test files
- **Documentation (15%)**: Comments, README, and code documentation
- **Project Structure (15%)**: Proper organization and file layout
- **Language Idioms (15%)**: Language-specific best practices
- **Build Readiness (10%)**: Build configuration and dependencies

### Quality Metrics

The system analyzes multiple code quality dimensions:

#### Code Analysis
- Syntax error detection
- Code complexity scoring
- Style guideline adherence
- Security vulnerability scanning

#### Test Coverage
- Test file presence and structure
- Test case comprehensiveness
- Integration test inclusion
- Performance test consideration

#### Documentation Quality
- README file presence and quality
- Code comment adequacy
- API documentation completeness
- Usage example provision

#### Project Organization
- Language-appropriate directory structure
- Proper file naming conventions
- Configuration file completeness
- Dependency management setup

### Output Structure

The command generates complete project structures:

#### Go Project Example
```
src/
├── cmd/
│   └── main.go              # Application entry point
├── internal/
│   ├── timer/
│   │   ├── timer.go         # Core implementation
│   │   └── timer_test.go    # Unit tests
│   └── config/
│       ├── config.go        # Configuration management
│       └── config_test.go   # Configuration tests
├── pkg/
│   └── api/                 # Public API packages
├── test/
│   └── integration/         # Integration tests
├── docs/
│   └── README.md           # Project documentation
├── go.mod                  # Go module definition
├── go.sum                  # Dependency checksums
└── Makefile               # Build automation
```

#### Python Project Example
```
src/
├── project_name/
│   ├── __init__.py         # Package initialization
│   ├── main.py            # Application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── timer.py       # Core implementation
│   │   └── config.py      # Configuration
│   └── utils/
│       └── helpers.py     # Utility functions
├── tests/
│   ├── __init__.py
│   ├── test_timer.py      # Unit tests
│   ├── test_config.py     # Configuration tests
│   └── integration/       # Integration tests
├── docs/
│   └── README.md          # Project documentation
├── pyproject.toml         # Project metadata
├── requirements.txt       # Dependencies
└── setup.py              # Installation script
```

### Multiple Specification Handling

The command can process multiple feature specifications:

```bash
/dev feat 1,3,5           # Generates integrated code for multiple features
```

This creates a unified codebase that implements all specified features with:
- Integrated architecture
- Shared components and utilities
- Comprehensive test coverage
- Unified documentation

### Error Handling and Fallback

The system includes robust error handling:

#### Agent Availability
- **Preferred**: Use specialized developer agents (e.g., `god`, `pydv`)
- **Fallback**: Use generic development agents
- **Last Resort**: Main Claude with enhanced context

#### Specification Issues
- **Missing Specifications**: Generate basic project structure with TODOs
- **Invalid Specifications**: Report errors and provide guidance
- **Partial Content**: Generate best-effort implementation with warnings

#### Language Detection
- **Project Analysis**: Scan for language indicators
- **Specification Content**: Extract language from feature descriptions
- **User Prompt**: Request language specification if detection fails

### Integration with Workflow

The `/dev` command completes the three-tier development process:

1. **Architecture**: `/design` → `app.md` (high-level system design)
2. **Specifications**: `/feat N` → `feat_N.md` (detailed implementation specs)
3. **Implementation**: `/dev feat N` → working code (executable implementation)

This ensures full traceability from architectural vision through detailed specifications to working code.

### Configuration

Behavior can be customized via `orchestration_config.json`:

```json
{
  "orchestration": {
    "dev_parallel_agent_count": 5,
    "execution_timeout_seconds": 300
  },
  "user_approval": {
    "user_dev_approval": false
  },
  "quality_standards": {
    "minimum_code_score": 0.5,
    "require_tests": true,
    "require_documentation": true
  }
}
```

### Performance Optimization

The system includes several performance optimizations:

- **Parallel Execution**: Multiple agents generate code simultaneously
- **Efficient Evaluation**: Streamlined quality assessment pipeline
- **Caching**: Results caching for repeated operations
- **Resource Management**: Automatic cleanup of temporary files

### Security Considerations

Code generation includes security measures:

- **Input Validation**: Sanitize all inputs and file paths
- **Output Scanning**: Check generated code for security issues
- **File Restrictions**: Limit file types and sizes
- **Sandboxing**: Isolated execution environments for agents

## Implementation

The command is implemented by the `DevWorkflow` class in `/hooks/multi_agent/workflows/dev_workflow.py`, which coordinates:

- Multi-specification processing and integration
- Language-specific developer agent selection
- Parallel code generation with context sharing
- Comprehensive quality evaluation and ranking
- Project structure creation and file organization
- Build configuration and dependency management

This ensures production-ready code that implements the specified features while following language best practices and maintaining high quality standards.