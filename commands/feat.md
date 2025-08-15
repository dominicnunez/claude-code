# /feat - Multi-Agent Feature Implementation Command

Transform architecture sections into detailed implementation specifications with exact structural preservation and parallel evaluation.

## Usage

```bash
/feat <section_identifier>
```

## Examples

```bash
/feat 1            # Implement section 1 from app.md
/feat timer-core   # Implement named section "timer-core"
/feat 2.3          # Implement specific subsection 2.3
/feat user-auth    # Implement user authentication section
```

## Description

The `/feat` command generates detailed implementation specifications from high-level architecture sections. It maintains exact structural preservation of subsections while providing comprehensive implementation guidance through parallel agent evaluation.

### Key Features

- **Structural Preservation**: Maintains exact subsection structure from `app.md`
- **Parallel Agent Execution**: Uses same architect agents as `/design` for consistency
- **Implementation Focus**: Transforms architecture into actionable implementation specs
- **Language Specificity**: Incorporates language-specific patterns and practices
- **Quality Validation**: Enforces structural integrity and implementation detail

### Critical Constraint

**Output `feat_N.md` MUST preserve exact subsection structure from `app.md` section N.**

The system validates:
- Exact subsection match (no missing, no extra)
- Consistent numbering and titles
- Structural integrity enforcement

### Execution Flow

1. **Parse Command**: Extract section identifier (numeric or named)
2. **Load Context**: Read `app.md` for architectural context
3. **Extract Structure**: Identify expected subsection structure
4. **Language Detection**: Determine target language from context
5. **Agent Selection**: Use same architect agents as design phase
6. **Parallel Generation**: Execute agents with structural constraints
7. **Structural Validation**: Verify exact subsection preservation
8. **Evaluation**: Rank specifications using implementation-focused criteria
9. **Persistence**: Save as `feat_N.md`, archive alternatives

### Evaluation Criteria

Feature specifications are evaluated using implementation-focused weights:

- **Structural Integrity (30%)**: Exact subsection structure preservation
- **Implementation Detail (25%)**: Depth and specificity of implementation guidance
- **Language Specificity (20%)**: Language-specific patterns and approaches
- **Technical Accuracy (15%)**: Technical correctness and feasibility
- **Clarity (10%)**: Readability and comprehensiveness

### Section Identification

The command supports multiple section identifier formats:

#### Numeric Sections
- `1` - Top-level section 1
- `2.3` - Subsection 2.3
- `1.2.3` - Nested subsection 1.2.3

#### Named Sections
- `timer-core` - Section with "timer-core" in title
- `user_auth` - Section matching "user_auth" pattern
- `configuration` - Section containing "configuration"

### Output Structure

For section identifier `N`, generates `feat_N.md` with:

```markdown
# Feature Implementation: Section N

## N.1 First Subsection
[Detailed implementation specifications]

## N.2 Second Subsection  
[Detailed implementation specifications]

## N.3 Third Subsection
[Detailed implementation specifications]
```

The structure exactly mirrors the subsections found in `app.md` section N.

### Language Integration

Feature specifications incorporate language-specific guidance:

#### Go Features
- Interface-based design patterns
- Goroutine and channel usage
- Error handling conventions
- Package organization

#### Python Features
- Class and module structure
- Async/await patterns
- Type hint specifications
- Package management

#### Rust Features
- Ownership and borrowing
- Error handling with Result/Option
- Trait implementations
- Memory safety considerations

### Validation Framework

The system enforces multiple validation layers:

1. **Syntax Validation**: Ensure descriptions are clear and complete
2. **Consistency Validation**: Check alignment with language best practices
3. **Completeness Validation**: Verify all required aspects are covered
4. **Structure Validation**: Enforce exact subsection preservation

### Error Handling

- **Missing app.md**: Generates specification without structural constraints
- **Section Not Found**: Returns error with available sections
- **Structural Violations**: Reports missing/extra subsections
- **No Agents Available**: Falls back to main Claude with context

### Integration Workflow

The `/feat` command fits into the three-tier development workflow:

1. **Architecture**: `/design` creates `app.md` with section structure
2. **Implementation**: `/feat N` creates detailed `feat_N.md` specifications
3. **Development**: `/dev feat N` generates working code from specifications

This ensures traceability from high-level architecture through detailed specifications to working code.

### Configuration

Behavior customization via `orchestration_config.json`:

```json
{
  "orchestration": {
    "feat_parallel_agent_count": 5,
    "execution_timeout_seconds": 300
  },
  "user_approval": {
    "user_feat_approval": false
  }
}
```

### Quality Assurance

The command includes comprehensive quality checks:

- **Structural Validation**: Verifies exact subsection match
- **Implementation Depth**: Ensures actionable implementation guidance
- **Language Appropriateness**: Validates language-specific patterns
- **Technical Feasibility**: Confirms implementation practicality

### Examples

#### Input: app.md Section 2
```markdown
2. Timer Core Engine
   2.1 State Management
   2.2 Event Handling  
   2.3 Configuration
```

#### Command: `/feat 2`

#### Output: feat_2.md
```markdown
# Timer Core Engine Implementation

## 2.1 State Management
[Detailed implementation for timer states, transitions, validation]

## 2.2 Event Handling
[Detailed event system implementation, handlers, dispatching]

## 2.3 Configuration  
[Detailed configuration management, validation, defaults]
```

## Implementation

The command is implemented by the `FeatWorkflow` class in `/hooks/multi_agent/workflows/feat_workflow.py`, which manages:

- Section identification and structure extraction
- Structural validation and preservation
- Language-aware implementation specifications
- Parallel agent coordination with identical prompts
- Quality evaluation with implementation focus
- Integration with the broader development workflow

This ensures high-quality, implementable specifications that maintain architectural coherence while providing actionable development guidance.