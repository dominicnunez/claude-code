#!/usr/bin/env python3
"""
README.md Generator with Smart Retry
Runs 3 GOD agents in parallel to create comprehensive documentation
"""

import asyncio
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple
from claude_sdk import ClaudeSDKClient

class ReadmeGenerator:
    def __init__(self, target_dir: str, work_dir: Path):
        self.target_dir = target_dir if target_dir else "current directory"
        self.work_dir = work_dir
        self.cwd = Path.cwd()
        self.attempt = 0
        self.max_retries = 1
        
    async def analyze_codebase(self) -> Dict[str, list]:
        """Analyze the current directory for code files"""
        analysis = {
            "go_files": list(self.cwd.glob("*.go")),
            "test_files": list(self.cwd.glob("*_test.go")),
            "config_files": list(self.cwd.glob("*.yaml")) + list(self.cwd.glob("*.yml")) + 
                          list(self.cwd.glob("*.json")) + list(self.cwd.glob("*.toml")),
            "existing_readme": (self.cwd / "README.md").exists(),
            "directories": [d for d in self.cwd.iterdir() if d.is_dir() and not d.name.startswith('.')]
        }
        return analysis
        
    async def run_documentation_agent(self, client, agent_num: int, attempt: int, analysis: Dict, feedback: str = "") -> bool:
        """Run a single GOD agent with specific documentation focus"""
        
        focus_areas = {
            1: ("USER-FOCUSED", [
                "Write for developers who will USE this code",
                "Clear, simple explanations",
                "Plenty of practical examples",
                "Step-by-step setup instructions",
                "Common use cases and patterns",
                "Troubleshooting section"
            ]),
            2: ("TECHNICAL-FOCUSED", [
                "Write for developers who need DEEP UNDERSTANDING",
                "Detailed API documentation",
                "Architecture and design decisions",
                "Performance characteristics",
                "Implementation details",
                "Advanced configuration options"
            ]),
            3: ("MAINTAINER-FOCUSED", [
                "Write for developers who will MAINTAIN/EXTEND this code",
                "Contributing guidelines",
                "Testing strategies and coverage",
                "Development setup and workflow",
                "Code organization and structure",
                "Debugging and monitoring"
            ])
        }
        
        focus, requirements = focus_areas[agent_num]
        readme_file = self.work_dir / f"attempt_{attempt}" / f"README_agent{agent_num}.md"
        readme_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Build file list for context
        go_files_list = "\n".join([f"- {f.name}" for f in analysis["go_files"][:10]])  # Limit to 10 files
        
        retry_context = ""
        if attempt > 1 and feedback:
            retry_context = f"""
## IMPORTANT: Retry Attempt {attempt}
The previous documentation was inadequate. The reviewer's feedback:
{feedback}

You MUST address these specific issues in your documentation.
"""
        
        prompt = f"""You are GOD agent #{agent_num} creating README.md documentation. Focus: {focus}.

Directory to document: {self.target_dir}

Code files found:
{go_files_list}

Test files: {len(analysis['test_files'])} found
Config files: {len(analysis['config_files'])} found
Existing README: {'Yes - UPDATE it' if analysis['existing_readme'] else 'No - CREATE new'}

{retry_context}

Requirements for {focus} documentation:
{chr(10).join(f"{i+1}. {req}" for i, req in enumerate(requirements))}

## Documentation Structure Required:

# [Project/Feature Name]

## Overview
[Clear description of what this code does]

## Installation
```bash
[Installation commands]
```

## Quick Start
[Immediate usage example]

## API Documentation
[Document all public interfaces based on your focus]

## Usage Examples
```go
[Practical code examples suited to your audience]
```

## Configuration
[Environment variables, settings, options]

## Testing
```bash
[How to run tests]
```

## Architecture
[Design and structure - depth based on your focus]

## Dependencies
[External packages and requirements]

## Contributing
[Guidelines for contributions]

## Troubleshooting
[Common issues and solutions]

Create comprehensive documentation in: {readme_file}

Analyze the actual Go code files to understand the feature/component and document it accurately."""

        print(f"  📝 GOD Agent #{agent_num} (Focus: {focus})...")
        
        try:
            await client.query(prompt, agent="god")
            
            async for message in client.receive_response():
                if message.status == "success":
                    return True
                elif message.status == "error":
                    print(f"    ❌ Agent #{agent_num} failed: {message.content}")
                    return False
                    
        except Exception as e:
            print(f"    ❌ Agent #{agent_num} error: {e}")
            return False
        
        return True

    async def run_review_agent(self, client, attempt: int) -> Tuple[str, str, str]:
        """
        Run review agent to analyze documentation versions
        Returns: (decision, selected_readme, feedback)
        decision can be: ACCEPT, RETRY, MERGE
        """
        
        attempt_dir = self.work_dir / f"attempt_{attempt}"
        
        # Read all README versions
        readmes = {}
        for i in range(1, 4):
            readme_file = attempt_dir / f"README_agent{i}.md"
            if readme_file.exists():
                readmes[i] = readme_file.read_text()
            else:
                readmes[i] = "# Documentation not available - agent failed"
        
        review_file = attempt_dir / "review.md"
        final_readme = self.cwd / "README.md"
        
        review_prompt = f"""You are a senior technical writer reviewing README documentation.

Directory documented: {self.target_dir}
Attempt: {attempt}/{self.max_retries + 1}

## Documentation Versions to Review:

### AGENT 1 - USER-FOCUSED:
{readmes[1]}

### AGENT 2 - TECHNICAL-FOCUSED:
{readmes[2]}

### AGENT 3 - MAINTAINER-FOCUSED:
{readmes[3]}

## Your Review Tasks:

1. **Documentation Quality Assessment**
   - Is the documentation comprehensive?
   - Are all important sections covered?
   - Is it accurate and clear?
   - Does each version serve its intended audience?

2. **Make a Decision**:
   
   **ACCEPT** - If one version is excellent as-is:
   - Select the best complete documentation
   
   **MERGE** - If combining sections would be better:
   - Take best sections from each version
   - Create optimal synthesized documentation
   
   **RETRY** - If ALL versions need improvement (only if attempt {attempt} == 1):
   - Identify what's missing or wrong
   - Provide specific improvement guidance

3. **Create Final README** in {final_readme}:

If ACCEPT or MERGE, create the final README.md with the best content.
If RETRY, document what needs improvement in {review_file}.

## Quality Criteria:
- Completeness: All necessary sections present
- Clarity: Easy to understand for target audience
- Accuracy: Correctly describes the code
- Examples: Practical, working examples
- Structure: Well-organized and formatted

Remember: Good documentation helps users succeed with the code."""

        print(f"🔍 Running documentation review for attempt {attempt}...")
        
        try:
            await client.query(review_prompt, agent="god")
            
            async for message in client.receive_response():
                if message.status == "success":
                    # Check if final README was created
                    if final_readme.exists():
                        return "ACCEPT", final_readme.read_text(), ""
                    
                    # Otherwise check review file for decision
                    if review_file.exists():
                        review_content = review_file.read_text()
                        
                        if "RETRY" in review_content and attempt == 1:
                            # Extract feedback for retry
                            import re
                            feedback_match = re.search(r'improvement.*?\n(.*?)(?=\n#|\Z)', 
                                                     review_content, re.DOTALL | re.IGNORECASE)
                            feedback = feedback_match.group(1).strip() if feedback_match else "Improve the documentation"
                            return "RETRY", "", feedback
                    
                    # Default to accept if unclear
                    return "ACCEPT", readmes[1], ""  # Use first version as fallback
                    
        except Exception as e:
            print(f"  ❌ Review error: {e}")
            return "ACCEPT", readmes[1], ""  # Fallback to first version
        
        return "ACCEPT", readmes[1], ""

    async def generate_readme(self) -> Tuple[bool, Path]:
        """Main documentation generation process with smart retry"""
        
        # First analyze the codebase
        print("📂 Analyzing codebase...")
        analysis = await self.analyze_codebase()
        print(f"  Found: {len(analysis['go_files'])} Go files, {len(analysis['test_files'])} test files")
        if analysis['existing_readme']:
            print("  📄 Existing README.md found - will update")
        
        feedback = ""
        
        for attempt in range(1, self.max_retries + 2):
            print(f"\n{'='*60}")
            print(f"📚 DOCUMENTATION ATTEMPT {attempt}")
            print(f"{'='*60}\n")
            
            # Run 3 agents in parallel
            print("🔄 Running 3 GOD agents with different documentation focuses...")
            
            async with ClaudeSDKClient() as client1, \
                       ClaudeSDKClient() as client2, \
                       ClaudeSDKClient() as client3:
                
                results = await asyncio.gather(
                    self.run_documentation_agent(client1, 1, attempt, analysis, feedback),
                    self.run_documentation_agent(client2, 2, attempt, analysis, feedback),
                    self.run_documentation_agent(client3, 3, attempt, analysis, feedback),
                    return_exceptions=True
                )
            
            successful = sum(1 for r in results if r is True)
            
            if successful == 0:
                print(f"  ❌ All agents failed. Cannot proceed.")
                return False, None
            
            print(f"  ✅ {successful}/3 agents completed")
            
            # Run review agent
            async with ClaudeSDKClient() as review_client:
                decision, selected_readme, feedback = await self.run_review_agent(review_client, attempt)
            
            print(f"  📊 Review Decision: {decision}")
            
            readme_path = self.cwd / "README.md"
            
            if decision in ["ACCEPT", "MERGE"]:
                if readme_path.exists():
                    print(f"  ✨ README.md updated successfully!")
                else:
                    # Create it from selected content
                    if selected_readme:
                        readme_path.write_text(selected_readme)
                        print(f"  ✨ README.md created successfully!")
                    else:
                        print(f"  ⚠️ No README content generated")
                        return False, None
                
                return True, readme_path
            
            elif decision == "RETRY" and attempt == 1:
                print(f"  🔄 Retry requested. Incorporating feedback...")
                print(f"  💡 Feedback: {feedback[:200]}..." if len(feedback) > 200 else f"  💡 Feedback: {feedback}")
                continue
            
            else:
                # Shouldn't reach here, but accept what we have
                if readme_path.exists():
                    print(f"  ✅ Documentation completed")
                    return True, readme_path
                else:
                    print(f"  ⚠️ Documentation process incomplete")
                    return False, None
        
        # If we exhausted retries
        readme_path = self.cwd / "README.md"
        if readme_path.exists():
            print(f"  ⚠️ Max retries reached. Using existing README.")
            return True, readme_path
        else:
            print(f"  ❌ Failed to generate README after retries")
            return False, None


async def main():
    """Main orchestration function"""
    
    target = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = Path(tempfile.gettempdir()) / f"readme_gen_{timestamp}"
    work_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("📚 README.MD DOCUMENTATION GENERATOR")
    print("="*60)
    print(f"📁 Target: {target if target else 'Current directory'}")
    print(f"📂 Working in: {Path.cwd()}")
    print(f"🔄 Smart retry enabled (max 1 retry)")
    print("="*60)
    
    # Create generator and run
    generator = ReadmeGenerator(target, work_dir)
    success, readme_file = await generator.generate_readme()
    
    # Display results
    print("\n" + "="*60)
    
    if success and readme_file:
        print("              DOCUMENTATION COMPLETE              ")
        print("="*60 + "\n")
        
        print(f"✨ README.md successfully {'updated' if readme_file.exists() else 'created'}!")
        print(f"📄 Location: {readme_file}")
        
        # Show first 20 lines of the README
        content = readme_file.read_text()
        lines = content.split('\n')[:20]
        print(f"\n📖 Preview:")
        print("-" * 40)
        print('\n'.join(lines))
        if len(content.split('\n')) > 20:
            print(f"... [{len(content.split('\n')) - 20} more lines]")
        print("-" * 40)
        
        print(f"\n💡 The README.md covers:")
        print("   ✓ User-focused documentation")
        print("   ✓ Technical API details")
        print("   ✓ Maintainer guidelines")
    else:
        print("              DOCUMENTATION NOTICE              ")
        print("="*60 + "\n")
        print("❌ Documentation generation did not complete")
        print("\n💡 Try running with more specific context:")
        print("   /readme 'Authentication middleware'")
        print("   /readme 'Cache service implementation'")
    
    print(f"\n📁 Work files saved in: {work_dir}")

if __name__ == "__main__":
    asyncio.run(main())