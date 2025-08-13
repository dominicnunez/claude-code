#!/usr/bin/env python3
"""
Single Feature Architecture Design with Smart Retry
Runs 3 GAD agents in parallel, reviews, and can retry once if needed
"""

import asyncio
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple
from claude_sdk import ClaudeSDKClient

class SingleFeatureDesigner:
    def __init__(self, feature: str, work_dir: Path):
        self.feature = feature
        self.work_dir = work_dir
        self.attempt = 0
        self.max_retries = 1
        
    async def run_design_agent(self, client, agent_num: int, attempt: int, feedback: str = "") -> bool:
        """Run a single GAD agent with specific focus"""
        
        focus_areas = {
            1: ("SIMPLICITY and MAINTAINABILITY", [
                "Focus on simple, maintainable architecture",
                "Minimize complexity and moving parts",
                "Prioritize developer experience",
                "Consider operational simplicity",
                "Use standard Go patterns"
            ]),
            2: ("SCALABILITY and PERFORMANCE", [
                "Design for high scalability",
                "Optimize for performance",
                "Consider distributed systems patterns",
                "Plan for growth and load",
                "Include caching and optimization strategies"
            ]),
            3: ("FLEXIBILITY and EXTENSIBILITY", [
                "Design for future extensibility",
                "Create flexible abstractions",
                "Enable plugin/module architecture where appropriate",
                "Consider integration patterns",
                "Plan for evolving requirements"
            ])
        }
        
        focus, requirements = focus_areas[agent_num]
        design_file = self.work_dir / f"attempt_{attempt}" / f"design_agent{agent_num}.md"
        design_file.parent.mkdir(parents=True, exist_ok=True)
        
        retry_context = ""
        if attempt > 1 and feedback:
            retry_context = f"""
## IMPORTANT: Retry Attempt {attempt}
The previous designs were inadequate. The reviewer's feedback:
{feedback}

You MUST address these specific issues in your design.
"""
        
        prompt = f"""You are GAD agent #{agent_num} designing a SINGLE FEATURE. Focus on {focus}.

Feature to Design: {self.feature}

{retry_context}

Create your architectural design in {design_file}

Requirements:
{chr(10).join(f"{i+1}. {req}" for i, req in enumerate(requirements))}

## Design Output Requirements:
1. Focus on this SINGLE FEATURE only
2. Provide:
   - Component architecture
   - Interface definitions
   - Data models (if applicable)
   - Integration points
   - Implementation approach
3. Keep scope focused - this is ONE feature, not a full system

Output your design to {design_file}"""

        print(f"  🤖 Agent #{agent_num} (Focus: {focus})...")
        
        try:
            await client.query(prompt, agent="gad")
            
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
        Run review agent to analyze designs
        Returns: (decision, selected_design, feedback)
        decision can be: ACCEPT, RETRY, ESCALATE
        """
        
        attempt_dir = self.work_dir / f"attempt_{attempt}"
        
        # Read all design files
        designs = {}
        for i in range(1, 4):
            design_file = attempt_dir / f"design_agent{i}.md"
            if design_file.exists():
                designs[i] = design_file.read_text()
            else:
                designs[i] = "Design not available - agent failed"
        
        review_file = attempt_dir / "review.md"
        
        review_prompt = f"""You are a senior architecture review specialist reviewing designs for a SINGLE FEATURE.

Feature: {self.feature}
Attempt: {attempt}/{self.max_retries + 1}

## Designs to Review:

### AGENT 1 DESIGN (Simplicity Focus):
{designs[1]}

### AGENT 2 DESIGN (Scalability Focus):
{designs[2]}

### AGENT 3 DESIGN (Flexibility Focus):
{designs[3]}

## Your Review Tasks:

1. **Quality Assessment**
   - Are the designs adequate for this feature?
   - Do they provide actionable architecture?
   - Are interfaces and components well-defined?

2. **Make a Decision**:
   
   **ACCEPT** - If at least one design is good enough:
   - Select the best design or synthesize from multiple
   - Create final architecture
   
   **RETRY** - If ALL designs are inadequate but fixable (only if attempt {attempt} == 1):
   - Identify specific problems
   - Provide clear guidance for improvement
   - Be specific about what's missing
   
   **ESCALATE** - If the feature is too complex for this process:
   - Recommend using the comprehensive /design command
   - Explain why this feature needs deeper analysis

3. **Create Output Document** in {review_file}:

# Feature Architecture Review - Attempt {attempt}

## Decision: [ACCEPT/RETRY/ESCALATE]

## Evaluation
[Brief evaluation of each design]

{"{"}
"IF ACCEPT:"{"}
## Selected Architecture
[Final architecture - either selected design or synthesis]

## Implementation Guidance
[Key points for implementing this feature]
{"}"}

{"{"}
"IF RETRY:"{"}
## Problems Identified
[Specific issues with current designs]

## Required Improvements
[Clear guidance for next attempt]
{"}"}

{"{"}
"IF ESCALATE:"{"}
## Complexity Analysis
[Why this feature is too complex]

## Recommendation
Use `/design {self.feature}` for comprehensive multi-iteration design
{"}"}

Remember: This is for a SINGLE FEATURE. If the designs adequately address the feature, ACCEPT them even if not perfect."""

        print(f"🔍 Running review for attempt {attempt}...")
        
        try:
            await client.query(review_prompt, agent="gad")
            
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
                            feedback = feedback_match.group(1).strip() if feedback_match else "Improve the designs"
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

    async def design_feature(self) -> Tuple[bool, Path]:
        """Main design process with smart retry"""
        
        feedback = ""
        
        for attempt in range(1, self.max_retries + 2):
            print(f"\n{'='*60}")
            print(f"📐 DESIGN ATTEMPT {attempt}")
            print(f"{'='*60}\n")
            
            # Run 3 agents in parallel
            print("🔄 Running 3 GAD agents in parallel...")
            
            async with ClaudeSDKClient() as client1, \
                       ClaudeSDKClient() as client2, \
                       ClaudeSDKClient() as client3:
                
                results = await asyncio.gather(
                    self.run_design_agent(client1, 1, attempt, feedback),
                    self.run_design_agent(client2, 2, attempt, feedback),
                    self.run_design_agent(client3, 3, attempt, feedback),
                    return_exceptions=True
                )
            
            successful = sum(1 for r in results if r is True)
            
            if successful == 0:
                print(f"  ❌ All agents failed. Cannot proceed.")
                return False, None
            
            print(f"  ✅ {successful}/3 agents completed")
            
            # Run review agent
            async with ClaudeSDKClient() as review_client:
                decision, selected_design, feedback = await self.run_review_agent(review_client, attempt)
            
            print(f"  📊 Review Decision: {decision}")
            
            if decision == "ACCEPT":
                print(f"  ✨ Design ACCEPTED!")
                # Create or update feat_*_*.md file with appropriate naming
                import re
                feature_name = re.sub(r'[^\w\s-]', '', self.feature.lower())
                feature_name = re.sub(r'[-\s]+', '_', feature_name)[:30]  # Limit length
                
                # Check if a feat file for this feature already exists
                existing_feats = list(Path.cwd().glob("feat_*.md"))
                feat_file = None
                
                # Try to find existing file with similar name
                for existing in existing_feats:
                    # Extract the feature part of the filename
                    match = re.match(r'feat_\d+_(.*?)\.md', existing.name)
                    if match:
                        existing_feature = match.group(1)
                        # Check if it's the same feature (fuzzy match)
                        if feature_name.startswith(existing_feature[:10]) or existing_feature.startswith(feature_name[:10]):
                            feat_file = existing
                            print(f"  📝 Updating existing: {feat_file.name}")
                            break
                
                # If no existing file found, create new with next number
                if not feat_file:
                    next_num = 1
                    if existing_feats:
                        numbers = []
                        for f in existing_feats:
                            match = re.match(r'feat_(\d+)_', f.name)
                            if match:
                                numbers.append(int(match.group(1)))
                        if numbers:
                            next_num = max(numbers) + 1
                    
                    feat_file = Path.cwd() / f"feat_{next_num}_{feature_name}.md"
                    print(f"  📄 Created new: {feat_file.name}")
                
                # Write the design (creates or overwrites)
                feat_file.write_text(selected_design)
                
                # Also save in work directory for reference
                final_file = self.work_dir / "final_design.md"
                final_file.write_text(selected_design)
                
                return True, feat_file
            
            elif decision == "RETRY" and attempt == 1:
                print(f"  🔄 Retry requested. Incorporating feedback...")
                print(f"  💡 Feedback: {feedback[:200]}..." if len(feedback) > 200 else f"  💡 Feedback: {feedback}")
                continue
            
            elif decision == "ESCALATE":
                print(f"  ⚠️ Feature too complex for single-pass design")
                print(f"  💡 Recommendation: Use /design command for comprehensive architecture")
                escalate_file = self.work_dir / "escalation_notice.md"
                escalate_file.write_text(selected_design)
                return False, escalate_file
            
            else:
                # Shouldn't reach here, but default to accepting
                print(f"  ✅ Design completed (default accept)")
                final_file = self.work_dir / "final_design.md"
                final_file.write_text(selected_design if selected_design else "Design completed")
                return True, final_file
        
        # If we exhausted retries, take the last attempt
        print(f"  ⚠️ Max retries reached. Using latest design.")
        final_file = self.work_dir / "final_design.md"
        if selected_design:
            final_file.write_text(selected_design)
        return True, final_file


async def main():
    """Main orchestration function"""
    
    if len(sys.argv) < 2:
        print("Usage: python single_feature_design.py '<feature_description>'")
        print("\nExamples:")
        print("  python single_feature_design.py 'user authentication with JWT'")
        print("  python single_feature_design.py 'caching layer for API responses'")
        print("  python single_feature_design.py 'real-time notification system'")
        print("\nFor complete applications, use iterative_design_system.py instead")
        sys.exit(1)
    
    feature = sys.argv[1]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = Path(tempfile.gettempdir()) / f"feature_design_{timestamp}"
    work_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("🎯 SINGLE FEATURE ARCHITECTURE DESIGN")
    print("="*60)
    print(f"📋 Feature: {feature}")
    print(f"📁 Working directory: {work_dir}")
    print(f"🔄 Smart retry enabled (max 1 retry)")
    print("="*60)
    
    # Create designer and run
    designer = SingleFeatureDesigner(feature, work_dir)
    success, result_file = await designer.design_feature()
    
    # Display results
    print("\n" + "="*60)
    
    if success and result_file and result_file.exists():
        print("              FEATURE ARCHITECTURE DESIGN              ")
        print("="*60 + "\n")
        
        content = result_file.read_text()
        # Display first 80 lines or full if shorter
        lines = content.split('\n')
        if len(lines) > 80:
            print('\n'.join(lines[:80]))
            print(f"\n... [{len(lines) - 80} more lines] ...\n")
        else:
            print(content)
        
        print("\n" + "="*60)
        print(f"✨ Feature design complete!")
        print(f"📄 Final design: {result_file}")
    else:
        print("              DESIGN PROCESS NOTICE              ")
        print("="*60 + "\n")
        
        if result_file and result_file.exists():
            print(result_file.read_text())
        else:
            print("❌ Design process did not produce a final design")
        
        print("\n" + "="*60)
        
        if not success:
            print("💡 Consider using: /design " + feature)
            print("   for comprehensive iterative architecture")
    
    print(f"📁 All attempts saved in: {work_dir}")

if __name__ == "__main__":
    asyncio.run(main())