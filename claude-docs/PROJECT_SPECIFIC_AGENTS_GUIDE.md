# Project-Specific Agents Guide: Scaling with Your Codebase

As your codebase grows, your agents should evolve from generic helpers to specialized experts that understand your specific patterns, frameworks, and conventions. This guide shows how to create increasingly sophisticated agents that encode your project's tribal knowledge.

## Evolution of Project-Specific Agents

### Stage 1: Generic Go Agents (Early Project)
```
go-architect → General Go patterns
go-coder → Standard Go implementation
```

### Stage 2: Framework-Aware Agents (Growing Codebase)
```
"Create a Go coder agent that uses our custom error framework at pkg/errors. It should wrap errors with context using errors.Wrap(), check errors with errors.Is(), and extract error codes using errors.Code(). The agent should be aware that all HTTP handlers must return errors.APIError type."
```

### Stage 3: Domain-Specific Agents (Mature Codebase)
```
"Create a Go API endpoint agent that knows our authentication middleware at pkg/auth, our database models at internal/models, our custom validation framework at pkg/validate, and our error handling patterns. It should follow our REST conventions where GET /resources lists, POST /resources creates, and all responses use our standard envelope format."
```

## Pattern Evolution Examples

### Custom Error Framework Agent
```
"Create a Go error-handling specialist that understands our custom error framework where:
- All errors must be wrapped with stack traces using pkg/errors.Wrap()
- HTTP errors use internal/apierrors with status codes
- Database errors are wrapped with query context
- All errors must include correlation IDs from context
- Error messages for users vs logs are separated
This agent should be used when implementing error handling or debugging error flows."
```

### Microservice Integration Agent
```
"Create a Go microservice integration agent that knows:
- Our service discovery uses internal/discovery
- All inter-service calls use pkg/client with circuit breakers
- Tracing context must be propagated via pkg/tracing
- Our protobuf definitions are in api/proto
- Service health checks follow internal/health patterns
Use when building service-to-service integrations."
```

### Database Operations Agent
```
"Create a Go database specialist that understands:
- We use sqlx with our wrapper at pkg/database
- Migrations are in migrations/ using golang-migrate
- All queries must use named parameters
- Transaction helpers are in pkg/database/tx
- Our model pattern separates DB models from API models
- Soft deletes use deleted_at timestamps
Use for any database-related implementation."
```

## Project Knowledge Embedding Strategies

### 1. Living Documentation Agents
Create agents that update themselves:
```
"Create a codebase-knowledge agent that reads our README.md, docs/architecture.md, and CONVENTIONS.md on SessionStart. It should understand our naming conventions, project structure, and design decisions. Use proactively to answer questions about our codebase patterns."
```

### 2. Layer-Specific Agents
```
"Create a Go repository-layer agent that:
- Knows all interfaces are defined in internal/repository/interfaces
- Implements using our base repository at internal/repository/base
- Uses our query builder patterns
- Handles caching with internal/cache
- Follows our pagination patterns using pkg/pagination"
```

### 3. Convention Enforcement Agents
```
"Create a Go code-reviewer agent that enforces:
- Our error handling must use pkg/errors
- All public functions need comments
- Tests must use testify/suite
- Mocks go in mocks/ subdirectory
- Context must be first parameter
- No panic() in production code"
```

## Advanced Project-Aware Patterns

### The Learning Agent
```
"Create a project-learning agent that:
1. Scans our codebase for patterns using Grep
2. Identifies our common imports and utilities
3. Learns our naming conventions
4. Documents discovered patterns
5. Updates a PATTERNS.md file
Use this periodically to keep project knowledge current."
```

### The Migration Agent
```
"Create a migration specialist that knows:
- Old error handling uses pkg/v1/errors
- New error handling uses pkg/v2/errors  
- Migration involves updating imports and error wrapping
- Must maintain backwards compatibility
- Tests need updating to new assertion methods"
```

### The Integration Test Agent
```
"Create an integration test specialist that:
- Uses our test containers setup in test/containers
- Follows our fixture patterns in test/fixtures
- Knows our test database is reset using test/db/reset()
- Uses our custom assertions in test/assertions
- Implements our golden file testing for API responses
- Handles our test environment variables from test/.env"
```

## Real-World Examples by Project Type

### For a Web API Project
```
"Create a REST API endpoint agent that:
- Uses our router setup with chi at internal/server/routes
- Implements handlers in internal/handlers following our pattern
- Uses our middleware chain from internal/middleware
- Validates requests using internal/validation
- Returns responses using internal/response.JSON()
- Handles errors with internal/errors.HandleHTTP()
- Implements OpenAPI documentation in docs/openapi
- Follows our RESTful conventions in docs/api-guidelines.md"
```

### For a CLI Tool Project
```
"Create a CLI command agent that:
- Uses cobra for commands in cmd/
- Implements command logic in internal/commands
- Uses our config system with viper at internal/config
- Handles output formatting with internal/output
- Implements our progress bars using internal/progress
- Follows our flag naming conventions
- Uses our custom completion scripts in scripts/completion"
```

### For a gRPC Service Project
```
"Create a gRPC service implementation agent that:
- Implements services from api/proto definitions
- Uses our interceptors at internal/grpc/interceptors
- Handles auth with internal/grpc/auth
- Implements health checks per internal/grpc/health
- Uses our custom error mapping in internal/grpc/errors
- Follows our protobuf style guide in docs/proto-style.md
- Generates mocks using our make proto-mocks command"
```

## Best Practices for Project-Specific Agents

### 1. Start Generic, Get Specific
Begin with general agents, then specialize as patterns emerge:
```
go-coder (generic)
├── go-api-coder (HTTP patterns)
├── go-db-coder (database patterns)
├── go-grpc-coder (gRPC patterns)
└── go-worker-coder (background jobs)
```

### 2. Document Your Patterns First
Create CONVENTIONS.md, then create agents that enforce them:
```
"Create an agent that enforces our conventions from CONVENTIONS.md, including:
[paste key conventions]
Use this agent for code reviews and ensuring consistency."
```

### 3. Version Your Agents
As your framework evolves, version your agents:
```
.claude/agents/
├── go-coder-v1.md      # Uses old error framework
├── go-coder-v2.md      # Uses new error framework
└── go-coder-latest.md  # Symlink to current version
```

### 4. Include Example Code
In your agent prompts, include actual code examples:
```
"...uses our error pattern like:
if err != nil {
    return errors.Wrap(err, 'failed to fetch user').
        WithCode(errors.NotFound).
        WithContext(ctx)
}"
```

### 5. Create Agent Hierarchies
Build specialized agents for different layers:
```
project-expert (knows everything)
├── api-layer-expert
│   ├── rest-handler-expert
│   └── graphql-resolver-expert
├── business-layer-expert
│   ├── service-expert
│   └── workflow-expert
└── data-layer-expert
    ├── repository-expert
    └── cache-expert
```

## Templates for Common Project-Specific Agents

### Template: Custom Framework Agent
```
"Create a [framework-name] specialist agent that:
- Knows our [framework] is at [path]
- Uses [specific methods/patterns]
- Follows conventions: [list key conventions]
- Common imports: [list imports]
- Example usage: [provide code example]
Use when working with [framework-name]."
```

### Template: Team Standards Agent
```
"Create a team-standards enforcer that knows:
- Our style guide at docs/style-guide.md
- Naming conventions: [list them]
- Required comments: [specify]
- Test requirements: [minimum coverage, patterns]
- PR checklist: [list items]
Use for code reviews and maintaining standards."
```

### Template: Dependency-Aware Agent
```
"Create a [library-name] integration agent that:
- Knows we use [library] version [X.Y.Z]
- Our wrapper is at [path]
- Configuration is in [config-path]
- Common patterns: [list patterns]
- Gotchas to avoid: [list gotchas]
Use when integrating with [library-name]."
```

## The Compound Effect

As your codebase grows:

1. **Each agent becomes more valuable** - They encode more context and tribal knowledge
2. **New developers onboard faster** - Agents act as interactive documentation
3. **Consistency improves** - Agents enforce patterns automatically
4. **Velocity increases** - Agents handle boilerplate and common patterns
5. **Technical debt decreases** - Agents ensure new code follows current best practices

## Maintenance Strategy

### Regular Updates
- Review agents quarterly
- Update when frameworks change
- Add new patterns as they emerge
- Deprecate outdated agents

### Knowledge Capture
- After each sprint, consider: "What patterns could be encoded in an agent?"
- During code reviews: "Could an agent have caught this?"
- When onboarding: "What knowledge could an agent provide?"

### Agent Documentation
Create an AGENTS.md file listing all project agents:
```markdown
# Project Agents

## Core Agents
- `go-coder`: General Go implementation
- `go-tester`: Test writing specialist

## Framework Agents  
- `error-handler`: Custom error framework
- `db-specialist`: Database operations

## Workflow Agents
- `api-endpoint`: Creates new API endpoints
- `migration-runner`: Database migrations
```

## Success Metrics

Track the effectiveness of your project-specific agents:

1. **Time saved** on repetitive tasks
2. **Consistency** in code patterns
3. **Onboarding time** for new developers
4. **Reduction** in code review comments
5. **Decrease** in pattern-related bugs

## Conclusion

Project-specific agents transform from simple helpers into a living, executable knowledge base. They encode your team's decisions, enforce your standards, and accelerate development while maintaining consistency. As your project grows, your agents become increasingly valuable, creating a compound effect that scales your engineering excellence.

Remember: **Build agents that encode your project's wisdom, not just its syntax.**