---
description: Single feature architecture design - 3 parallel GAD agents with smart retry
model: opus
allowed-tools: Bash, Write, Read, Task
---

# Single Feature Architecture Design

I'll orchestrate 3 GAD agents to design architecture for a **single feature**, with intelligent retry if needed.

## Feature to Design
$ARGUMENTS

## Smart Process

1. **Parallel Design Phase**: 3 GAD agents with different approaches:
   - Agent 1: Simplicity & Maintainability
   - Agent 2: Scalability & Performance  
   - Agent 3: Flexibility & Extensibility

2. **Review & Decision**:
   - Review agent evaluates all designs
   - Can make one of three decisions:
     - **ACCEPT**: Select/synthesize best design
     - **RETRY**: Request new attempt with specific feedback
     - **ESCALATE**: Recommend using `/design` for complex features

3. **Smart Retry** (if needed):
   - Maximum 1 retry with targeted feedback
   - Agents incorporate reviewer's specific guidance
   - Prevents accepting subpar designs

This is optimized for **single features** (e.g., "authentication system", "caching layer", "notification service").

For **complete applications**, use `/design` instead.

```bash
python ~/.claude/hooks/multi_agent/single_feature_design.py "$ARGUMENTS"
```