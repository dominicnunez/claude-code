#!/usr/bin/env python3
"""
Single Feature Go Implementation with Smart Retry
Runs 3 GOD agents in parallel, reviews, and can retry once if needed
Based on single_feature_design.py but for actual Go code implementation
"""

import asyncio
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple
from claude_sdk import ClaudeSDKClient

class SingleFeatureImplementer:
    def __init__(self, feature: str, work_dir: Path):
        self.feature = feature
        self.work_dir = work_dir
        self.attempt = 0
        self.max_retries = 1
        
    async def run_implementation_agent(self, client, agent_num: int, attempt: int, feedback: str = "") -> bool:
        """Run a single GOD agent with specific focus"""
        
        focus_areas = {
            1: ("SIMPLE and MAINTAINABLE", [
                "Write clean, readable Go code",
                "Minimize complexity",
                "Clear variable and function names",
                "Straightforward logic flow",
                "Easy to understand and modify"
            ]),
            2: ("PERFORMANT and OPTIMIZED", [
                "Optimize for speed and efficiency",
                "Minimize allocations",
                "Use appropriate data structures",
                "Consider concurrency where beneficial",
                "Profile-guided optimizations"
            ]),
            3: ("FLEXIBLE and EXTENSIBLE", [
                "Design for future changes",
                "Use interfaces appropriately",
                "Enable easy extension points",
                "Modular, composable design",
                "Configuration-driven behavior"
            ])
        }
        
        focus, requirements = focus_areas[agent_num]
        
        # Determine file names based on feature
        import re
        feature_name = re.sub(r'[^\w\s-]', '', self.feature.lower())
        feature_name = re.sub(r'[-\s]+', '_', feature_name)[:30]
        
        impl_file = self.work_dir / f"attempt_{attempt}" / f"impl_agent{agent_num}.go"
        test_file = self.work_dir / f"attempt_{attempt}" / f"impl_agent{agent_num}_test.go"
        impl_file.parent.mkdir(parents=True, exist_ok=True)
        
        retry_context = ""
        if attempt > 1 and feedback:
            retry_context = f"""
## IMPORTANT: Retry Attempt {attempt}
The previous implementations were inadequate. The reviewer's feedback:
{feedback}

You MUST address these specific issues in your implementation.
"""
        
        prompt = f"""You are GOD agent #{agent_num} implementing a SINGLE FEATURE in Go. Focus on {focus}.

Feature to Implement: {self.feature}

{retry_context}

Requirements:
{chr(10).join(f"{i+1}. {req}" for i, req in enumerate(requirements))}

## Implementation Requirements:
1. Create production-ready Go code
2. Include comprehensive tests
3. Follow Go best practices and idioms
4. Handle errors properly
5. Add appropriate documentation
6. Create/update README.md with full documentation
7. Focus on this SINGLE FEATURE only

Create your implementation in:
- Main code: {impl_file}
- Tests: {test_file}
- Documentation: README.md in the same directory

The README.md should include:
- Overview of the feature or component
- Installation and setup instructions
- API documentation
- Usage examples
- Testing instructions
- Configuration details
- Dependencies

Remember: This is ONE feature implementation, not a full system."""

        print(f"  🚀 GOD Agent #{agent_num} (Focus: {focus})...")
        
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
        Run review agent to analyze implementations
        Returns: (decision, selected_implementation, feedback)
        decision can be: ACCEPT, RETRY, ESCALATE
        """
        
        attempt_dir = self.work_dir / f"attempt_{attempt}"
        
        # Read all implementation files
        implementations = {}
        tests = {}
        for i in range(1, 4):
            impl_file = attempt_dir / f"impl_agent{i}.go"
            test_file = attempt_dir / f"impl_agent{i}_test.go"
            
            if impl_file.exists():
                implementations[i] = impl_file.read_text()
            else:
                implementations[i] = "// Implementation not available - agent failed"
                
            if test_file.exists():
                tests[i] = test_file.read_text()
            else:
                tests[i] = "// Tests not available"
        
        review_file = attempt_dir / "review.md"
        
        review_prompt = f"""You are a senior Go engineer reviewing implementations for a SINGLE FEATURE.

Feature: {self.feature}
Attempt: {attempt}/{self.max_retries + 1}

## Implementations to Review:

### AGENT 1 IMPLEMENTATION (Simple & Maintainable):
```go
{implementations[1]}
```
Tests:
```go
{tests[1]}
```

### AGENT 2 IMPLEMENTATION (Performant & Optimized):
```go
{implementations[2]}
```
Tests:
```go
{tests[2]}
```

### AGENT 3 IMPLEMENTATION (Flexible & Extensible):
```go
{implementations[3]}
```
Tests:
```go
{tests[3]}
```

## Your Review Tasks:

1. **Code Quality Assessment**
   - Is the code production-ready?
   - Are Go idioms and best practices followed?
   - Is error handling comprehensive?
   - Are tests adequate?

2. **Make a Decision**:
   
   **ACCEPT** - If at least one implementation is good enough:
   - Select the best implementation or synthesize from multiple
   - Ensure it's production-ready
   
   **RETRY** - If ALL implementations are inadequate but fixable (only if attempt {attempt} == 1):
   - Identify specific problems
   - Provide clear guidance for improvement
   - Be specific about what's missing
   
   **ESCALATE** - If the feature needs architectural design first:
   - Recommend using /feat for architecture
   - Explain why implementation needs design

3. **Create Output Document** in {review_file}:

# Go Implementation Review - Attempt {attempt}

## Decision: [ACCEPT/RETRY/ESCALATE]

## Code Quality Evaluation
[Brief evaluation of each implementation]

{"{"}
"IF ACCEPT:"{"}
## Selected Implementation

### Main Code (save to appropriate .go file):
```go
[Final production code - either selected or synthesized]
```

### Tests (save to appropriate _test.go file):
```go
[Comprehensive test suite]
```

## Implementation Notes
[Key points about the implementation]
{"}"}

{"{"}
"IF RETRY:"{"}
## Problems Identified
[Specific issues with current implementations]

## Required Improvements
[Clear guidance for next attempt]
{"}"}

{"{"}
"IF ESCALATE:"{"}
## Architecture Needed
[Why this needs design first]

## Recommendation
Use `/feat {self.feature}` for architectural design first
{"}"}

Remember: This is for a SINGLE FEATURE. If the implementations adequately solve the feature, ACCEPT them even if not perfect."""

        print(f"🔍 Running code review for attempt {attempt}...")
        
        try:
            await client.query(review_prompt, agent="god")
            
            async for message in client.receive_response():
                if message.status == "success":
                    # Parse the review to extract decision
                    if review_file.exists():
                        review_content = review_file.read_text()
                        
                        # Extract decision
                        if "Decision: ACCEPT" in review_content:
                            return "ACCEPT", review_content, ""
                        elif "Decision: RETRY" in review_content and attempt == 1:
                            # Extract feedback for retry
                            import re
                            feedback_match = re.search(r'## Required Improvements.*?\n(.*?)(?=\n#|\Z)', 
                                                     review_content, re.DOTALL)
                            feedback = feedback_match.group(1).strip() if feedback_match else "Improve the implementations"
                            return "RETRY", "", feedback
                        elif "Decision: ESCALATE" in review_content:
                            return "ESCALATE", review_content, ""
                        else:
                            # Default to ACCEPT if unclear
                            return "ACCEPT", review_content, ""
                    
                    return "ACCEPT", "Review file not created", ""
                    
        except Exception as e:
            print(f"  ❌ Review error: {e}")
            return "ACCEPT", f"Review failed: {e}", ""
        
        return "ACCEPT", "Review failed", ""

    async def implement_feature(self) -> Tuple[bool, Path]:
        """Main implementation process with smart retry"""
        
        feedback = ""
        
        for attempt in range(1, self.max_retries + 2):
            print(f"\n{'='*60}")
            print(f"💻 IMPLEMENTATION ATTEMPT {attempt}")
            print(f"{'='*60}\n")
            
            # Run 3 agents in parallel
            print("🔄 Running 3 GOD agents in parallel...")
            
            async with ClaudeSDKClient() as client1, \
                       ClaudeSDKClient() as client2, \
                       ClaudeSDKClient() as client3:
                
                results = await asyncio.gather(
                    self.run_implementation_agent(client1, 1, attempt, feedback),
                    self.run_implementation_agent(client2, 2, attempt, feedback),
                    self.run_implementation_agent(client3, 3, attempt, feedback),
                    return_exceptions=True
                )
            
            successful = sum(1 for r in results if r is True)
            
            if successful == 0:
                print(f"  ❌ All agents failed. Cannot proceed.")
                return False, None
            
            print(f"  ✅ {successful}/3 agents completed")
            
            # Run review agent
            async with ClaudeSDKClient() as review_client:
                decision, selected_impl, feedback = await self.run_review_agent(review_client, attempt)
            
            print(f"  📊 Review Decision: {decision}")
            
            if decision == "ACCEPT":
                print(f"  ✨ Implementation ACCEPTED!")
                
                # Extract code from review and save to actual Go files
                import re
                
                # Extract main code
                code_match = re.search(r'### Main Code.*?```go\n(.*?)```', selected_impl, re.DOTALL)
                test_match = re.search(r'### Tests.*?```go\n(.*?)```', selected_impl, re.DOTALL)
                
                if code_match:
                    # Create proper Go file name
                    feature_name = re.sub(r'[^\w\s-]', '', self.feature.lower())
                    feature_name = re.sub(r'[-\s]+', '_', feature_name)[:30]
                    
                    # Save implementation
                    impl_file = Path.cwd() / f"{feature_name}.go"
                    impl_file.write_text(code_match.group(1))
                    print(f"  📄 Created: {impl_file.name}")
                    
                    # Save tests if available
                    if test_match:
                        test_file = Path.cwd() / f"{feature_name}_test.go"
                        test_file.write_text(test_match.group(1))
                        print(f"  🧪 Created: {test_file.name}")
                    
                    # Create README.md - prompt GOD to generate it
                    readme_prompt = f"""Based on the implemented feature, create a comprehensive README.md file.

Feature: {self.feature}

Implementation file: {impl_file.name}
Test file: {feature_name}_test.go

Create a README.md with:
# {self.feature.title()}

## Overview
[Describe what this feature or component does]

## Installation
```bash
go get [package path]
```

## API Documentation
[Document all public functions, types, and interfaces]

## Usage Examples
```go
// Show practical examples of using this feature
```

## Configuration
[Any environment variables or settings]

## Testing
```bash
go test ./...
```

## Architecture
[Design decisions and structure]

## Dependencies
[List any external dependencies]

## Contributing
[Guidelines for modifications]"""

                    # Run a quick GOD agent to generate README
                    async with ClaudeSDKClient() as readme_client:
                        await readme_client.query(readme_prompt, agent="god")
                        async for message in readme_client.receive_response():
                            if message.status == "success":
                                # GOD should have created README.md
                                readme_file = Path.cwd() / "README.md"
                                if readme_file.exists():
                                    print(f"  📚 Created: README.md")
                                break
                    
                    # Also save review in work directory
                    final_file = self.work_dir / "final_implementation.md"
                    final_file.write_text(selected_impl)
                    
                    return True, impl_file
                else:
                    # Fallback: save review as-is
                    final_file = self.work_dir / "final_implementation.md"
                    final_file.write_text(selected_impl)
                    print(f"  📄 Review saved to: {final_file}")
                    return True, final_file
            
            elif decision == "RETRY" and attempt == 1:
                print(f"  🔄 Retry requested. Incorporating feedback...")
                print(f"  💡 Feedback: {feedback[:200]}..." if len(feedback) > 200 else f"  💡 Feedback: {feedback}")
                continue
            
            elif decision == "ESCALATE":
                print(f"  ⚠️ Feature needs architectural design first")
                print(f"  💡 Recommendation: Use /feat command for architecture")
                escalate_file = self.work_dir / "escalation_notice.md"
                escalate_file.write_text(selected_impl)
                return False, escalate_file
            
            else:
                # Shouldn't reach here, but default to accepting
                print(f"  ✅ Implementation completed (default accept)")
                final_file = self.work_dir / "final_implementation.md"
                final_file.write_text(selected_impl if selected_impl else "Implementation completed")
                return True, final_file
        
        # If we exhausted retries, take the last attempt
        print(f"  ⚠️ Max retries reached. Using latest implementation.")
        final_file = self.work_dir / "final_implementation.md"
        if selected_impl:
            final_file.write_text(selected_impl)
        return True, final_file


async def main():
    """Main orchestration function"""
    
    if len(sys.argv) < 2:
        print("Usage: python single_feature_implementer.py '<feature_description>'")
        print("\nExamples:")
        print("  python single_feature_implementer.py 'JWT authentication middleware'")
        print("  python single_feature_implementer.py 'Redis cache service'")
        print("  python single_feature_implementer.py 'Rate limiter with token bucket'")
        print("\nFor architectural design, use /feat command first")
        print("For complete system implementation, use /designcode (coming soon)")
        sys.exit(1)
    
    feature = sys.argv[1]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = Path(tempfile.gettempdir()) / f"feature_impl_{timestamp}"
    work_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("🚀 SINGLE FEATURE GO IMPLEMENTATION")
    print("="*60)
    print(f"📋 Feature: {feature}")
    print(f"📁 Working directory: {work_dir}")
    print(f"🔄 Smart retry enabled (max 1 retry)")
    print("="*60)
    
    # Create implementer and run
    implementer = SingleFeatureImplementer(feature, work_dir)
    success, result_file = await implementer.implement_feature()
    
    # Display results
    print("\n" + "="*60)
    
    if success and result_file:
        print("              FEATURE IMPLEMENTATION COMPLETE              ")
        print("="*60 + "\n")
        
        if result_file.suffix == ".go":
            print(f"✨ Go implementation complete!")
            print(f"📄 Implementation: {result_file}")
            
            # Check for test file
            test_file = result_file.parent / f"{result_file.stem}_test.go"
            if test_file.exists():
                print(f"🧪 Tests: {test_file}")
            
            print(f"\n💡 Next steps:")
            print(f"   1. Run tests: go test ./{result_file.stem}*")
            print(f"   2. Format code: go fmt {result_file.name}")
            print(f"   3. Check: go vet {result_file.name}")
        else:
            print(f"📄 Implementation review: {result_file}")
    else:
        print("              IMPLEMENTATION NOTICE              ")
        print("="*60 + "\n")
        
        if result_file and result_file.exists():
            content = result_file.read_text()
            print(content[:500] + "..." if len(content) > 500 else content)
        else:
            print("❌ Implementation process did not produce final code")
        
        print("\n" + "="*60)
        
        if not success:
            print("💡 Consider using: /feat " + feature)
            print("   for architectural design first")
    
    print(f"📁 All attempts saved in: {work_dir}")

if __name__ == "__main__":
    asyncio.run(main())