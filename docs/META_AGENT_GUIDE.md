# How to Use the Meta-Agent: The Agent That Builds Agents

The meta-agent is a specialized sub-agent that **automatically generates new sub-agents** from simple descriptions. It's like having an expert agent architect on demand.

## What Makes It Special

1. **Automatic Invocation**: When you ask Claude Code to "create a new agent" or describe an agent you want, Claude automatically delegates to the meta-agent
2. **Self-Updating**: It fetches the latest Claude Code documentation to stay current with features
3. **Intelligent Tool Selection**: Analyzes your requirements and assigns only necessary tools
4. **Best Practices Built-In**: Generates agents following proven patterns

## How to Trigger the Meta-Agent

Simply ask Claude Code to create a new agent with a description:

```
"Create a new sub-agent that reviews Python code for security vulnerabilities"

"Build an agent that can analyze database performance issues"

"I need a sub-agent that monitors system resources and alerts on high usage"
```

Claude Code will automatically recognize this as a meta-agent task and delegate to it.

## What Happens Behind the Scenes

1. **Documentation Fetch**: Meta-agent scrapes latest docs from Anthropic
2. **Requirement Analysis**: Parses your description to understand the agent's purpose
3. **Name Generation**: Creates a kebab-case name (e.g., `security-code-reviewer`)
4. **Tool Selection**: Determines minimal toolset needed (e.g., Read, Grep, Glob for a reviewer)
5. **System Prompt Creation**: Writes detailed instructions for the new agent
6. **File Generation**: Creates the agent file at `.claude/agents/<agent-name>.md`

## Key Components of Generated Agents

The meta-agent creates agents with:

- **Frontmatter**: Name, description, tools, color, model
- **Purpose Section**: Clear role definition
- **Instructions**: Step-by-step workflow
- **Best Practices**: Domain-specific guidelines
- **Report Format**: How the agent should structure its output

## Example: Creating a Test Runner Agent

**You say**: "Create an agent that runs tests and fixes failing ones"

**Meta-agent generates**:
```markdown
---
name: test-runner-fixer
description: Use proactively to run tests and automatically fix failures
tools: Bash, Read, Edit, MultiEdit, Grep
color: green
model: sonnet
---

# Purpose
You are a test automation specialist that runs tests and fixes failures...

## Instructions
1. Run the test suite using appropriate commands
2. Parse test output for failures
3. Analyze error messages and stack traces
4. Fix the failing code
5. Re-run tests to verify fixes
...
```

## Pro Tips for Using Meta-Agent

1. **Be Specific**: "Create an agent that validates JSON schemas" is better than "create a validation agent"

2. **Mention Triggers**: Include when the agent should activate:
   - "Use proactively when..."
   - "Triggers on the phrase..."
   - "Automatically runs when..."

3. **Specify Model**: Add model preference if needed:
   - "Create a fast agent using haiku model..."
   - "Build a sophisticated agent with opus..."

4. **Chain Agents**: Create complementary agents:
   - First: "Create an agent that finds bugs"
   - Then: "Create an agent that fixes the bugs found by bug-finder"

5. **Iterate**: After creation, you can ask to modify:
   - "Update the test-runner agent to also generate coverage reports"

## Advanced Usage Patterns

### Pattern 1: Domain-Specific Suite
```
"Create a security-scanner agent"
"Create a vulnerability-fixer agent" 
"Create a security-report-generator agent"
```

### Pattern 2: Workflow Automation
```
"Create an agent that prepares releases by updating version numbers and changelogs"
```

### Pattern 3: Integration Agents
```
"Create an agent that syncs with external APIs and updates local data"
```

## The Power of Compound Growth

The meta-agent embodies the principle: "Build the thing that builds the thing." Instead of manually writing agent configurations, you describe what you need and the meta-agent handles the implementation details. This accelerates your ability to create specialized tools exponentially.

Each new agent you create becomes part of your toolkit, and you can create agents that work together, forming complex automated workflows. It's like having a team of specialists you can summon on demand.

## Quick Start Examples

### Example 1: Documentation Agent
```
"Create an agent that automatically generates API documentation from code comments"
```

### Example 2: Refactoring Agent
```
"Create an agent that identifies and refactors duplicate code"
```

### Example 3: Dependency Agent
```
"Create an agent that updates outdated dependencies and runs tests to ensure compatibility"
```

### Example 4: Performance Agent
```
"Create an agent that profiles code and suggests performance optimizations"
```

### Example 5: Migration Agent
```
"Create an agent that helps migrate code from one framework version to another"
```

## Understanding the Meta-Agent Configuration

Located at `.claude/agents/meta-agent.md`, the meta-agent itself has:

- **Model**: Uses Opus (most capable) for complex agent generation
- **Tools**: Write, WebFetch, and scraping tools for docs
- **Color**: Cyan for visibility in terminal
- **Description**: Tells Claude when to automatically invoke it

## Troubleshooting

### Agent Not Created?
- Check `.claude/agents/` directory for the new file
- Ensure your description was clear about creating an agent
- Look for error messages in the Claude Code output

### Agent Not Working as Expected?
- Review the generated agent file
- Modify the description field if delegation isn't working
- Adjust the tools list if capabilities are missing
- Refine the system prompt instructions

### Want to Modify an Existing Agent?
Simply ask: "Update the [agent-name] agent to also [new capability]"

## Best Practices

1. **Start Simple**: Create basic agents first, then iterate
2. **Test Immediately**: After creation, test the agent with a real task
3. **Document Purpose**: Be clear about what problem the agent solves
4. **Minimize Tools**: Only grant tools the agent actually needs
5. **Use Descriptive Names**: Make agent names self-documenting

## The Meta-Agent Philosophy

The meta-agent represents a fundamental principle in engineering: **leverage automation to build automation**. Instead of spending time writing boilerplate agent configurations, you focus on describing the problem you want solved. The meta-agent handles the implementation details, allowing you to rapidly scale your capabilities.

This approach enables:
- **Rapid Prototyping**: Test ideas quickly by generating agents
- **Consistent Quality**: All agents follow best practices
- **Knowledge Transfer**: The meta-agent embeds expertise in agent design
- **Scalable Workflows**: Build complex multi-agent systems easily

Remember: Every agent you create with the meta-agent becomes a reusable tool in your arsenal, compounding your productivity over time.