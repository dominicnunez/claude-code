---
description: Single feature Go implementation - 3 parallel GOD agents with smart retry
model: opus
allowed-tools: Bash, Write, Read, Task, MultiEdit, Grep, Glob
---

# Single Feature Go Implementation

I'll orchestrate 3 GOD agents to implement Go code for a **single feature**, with intelligent retry if needed.

## Feature to Implement
$ARGUMENTS

## Smart Process

1. **Parallel Implementation Phase**: 3 GOD agents with different approaches:
   - Agent 1: Simple & Maintainable (clean, readable code)
   - Agent 2: Performant & Optimized (fast, efficient)
   - Agent 3: Flexible & Extensible (adaptable, modular)

2. **Review & Decision**:
   - Review agent evaluates all implementations
   - Can make one of three decisions:
     - **ACCEPT**: Select/synthesize best implementation
     - **RETRY**: Request new attempt with specific feedback
     - **ESCALATE**: Recommend architectural review first

3. **Smart Retry** (if needed):
   - Maximum 1 retry with targeted feedback
   - Agents incorporate reviewer's specific guidance
   - Prevents accepting subpar implementations

This is optimized for **single feature implementation** (e.g., "auth middleware", "cache service", "rate limiter").

For **complete system implementation**, use `/designcode` (coming soon).

```bash
python ~/.claude/single_feature_implementer.py "$ARGUMENTS"
```