---
description: Generate or update README.md - 3 parallel GOD agents with smart retry
model: opus
allowed-tools: Bash, Write, Read, Task, MultiEdit, Grep, Glob
---

# README Documentation Generator

I'll orchestrate 3 GOD agents to create or update README.md documentation, with intelligent retry if needed.

## Directory/Feature to Document
$ARGUMENTS

## Smart Process

1. **Parallel Documentation Phase**: 3 GOD agents with different focuses:
   - Agent 1: **User-Focused** (clear, beginner-friendly, examples)
   - Agent 2: **Technical-Focused** (detailed API, architecture, performance)
   - Agent 3: **Maintainer-Focused** (contributing, testing, debugging)

2. **Review & Decision**:
   - Review agent evaluates all documentation versions
   - Can make one of three decisions:
     - **ACCEPT**: Select/synthesize best documentation
     - **RETRY**: Request improvements with specific feedback
     - **MERGE**: Combine best sections from each

3. **Smart Retry** (if needed):
   - Maximum 1 retry with targeted feedback
   - Agents incorporate reviewer's guidance
   - Ensures comprehensive, high-quality documentation

This analyzes the current directory's code and creates documentation that serves all audiences.

```bash
python ~/.claude/readme_generator.py "$ARGUMENTS"
```