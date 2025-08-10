# Architecture Review

Review and analyze the Big Meanie trading system architecture, either comprehensively or for specific areas.

## Usage
- `/arch_review` - Comprehensive architecture review
- `/arch_review <focus_area>` - Review specific area (e.g., `/arch_review errors`, `/arch_review indicators`)
- `/arch_review <package_path>` - Review specific package (e.g., `/arch_review pkg/indicators/common`)

## Instructions
- Delegate to the go-architect agent to perform the architecture review
- If a parameter is provided, focus the review on that specific area/package
- For focused reviews, still consider how the area integrates with the rest of the system
- The agent should analyze the existing package structure, interfaces, and patterns
- Identify architectural strengths and areas following Go best practices
- Highlight any anti-patterns or areas needing refactoring
- Suggest improvements while maintaining existing functionality
- Focus on package cohesion, interface design, and concurrency patterns
- Ensure shopspring/decimal usage for all numeric operations
- Validate naming conventions follow ultra-concise patterns

## Review Areas (for comprehensive review)
- Package organization (internal vs pkg separation)
- Interface definitions and their usage
- Dependency management and coupling
- Concurrency patterns and goroutine safety
- Error handling consistency
- Test structure and coverage
- Performance bottlenecks in architecture
- Module boundaries and responsibilities

## Focused Review Examples
- `/arch_review errors` - Review error handling architecture
- `/arch_review indicators` - Review indicator package design
- `/arch_review strategy` - Review strategy pattern implementation
- `/arch_review backtest` - Review backtesting architecture
- `/arch_review concurrency` - Review goroutine and channel patterns
- `/arch_review internal/common` - Review shared types and interfaces

## Output Format
Provide a structured review including:
1. Scope (comprehensive or focused area)
2. Current Architecture Overview
3. Strengths (what's working well)
4. Issues and Anti-patterns
5. Improvement Recommendations
6. Refactoring Priority List
7. Migration Path (if major changes needed)
8. Integration Points (for focused reviews)