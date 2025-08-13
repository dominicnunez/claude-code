## Backwards Compatibility Reminder
- Backwards compatibility with legacy code is tech debt waiting to break
- Migration code to bridge from legacy to new feature is tech debt waiting to break
- NEVER maintain backwards compatibility when making changes
- Fast Fail approach is always better than hidden problems

## Critical Git Reminders
- NEVER include "Generated with Claude Code" in commit messages.
- NEVER include "Co-Authored-By Claude" in commit messages
- NEVER refer to "phases" in commit messages
- NEVER force-add gitignored files
- NEVER commit sensitive data (API keys, passwords)
