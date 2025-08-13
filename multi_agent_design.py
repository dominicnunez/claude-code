#!/usr/bin/env python3
"""
Multi-Agent Architecture Design Orchestrator
Runs 3 GAD agents in parallel, then reviews to select best design
"""

import asyncio
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from claude_sdk import ClaudeSDKClient

async def run_design_agent(client, agent_num: int, task: str, work_dir: Path) -> bool:
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
    design_file = work_dir / f"design_agent{agent_num}.md"
    
    prompt = f"""You are GAD agent #{agent_num}. Focus on {focus}.

Task: {task}

Create your architectural design in a file called {design_file}

Requirements:
{chr(10).join(f"{i+1}. {req}" for i, req in enumerate(requirements))}

Output your design to {design_file}"""

    print(f"🤖 Starting Agent #{agent_num} (Focus: {focus})...")
    
    try:
        # Use the GAD agent
        await client.query(prompt, agent="gad")
        
        async for message in client.receive_response():
            if message.status == "success":
                print(f"✅ Agent #{agent_num} completed successfully")
                return True
            elif message.status == "error":
                print(f"❌ Agent #{agent_num} failed: {message.content}")
                return False
                
    except Exception as e:
        print(f"❌ Agent #{agent_num} error: {e}")
        return False
    
    return True

async def run_review_agent(client, task: str, work_dir: Path) -> bool:
    """Run review agent to analyze and select best design"""
    
    # Read all design files
    designs = {}
    for i in range(1, 4):
        design_file = work_dir / f"design_agent{i}.md"
        if design_file.exists():
            designs[i] = design_file.read_text()
        else:
            designs[i] = "Design not available - agent failed"
    
    final_design_file = work_dir / "final_design.md"
    
    review_prompt = f"""You are a senior architecture review specialist. You need to evaluate architectural designs from multiple GAD agents and select the best approach.

Original Task: {task}

Please review the following architectural designs:

AGENT 1 DESIGN (Simplicity Focus):
---
{designs[1]}
---

AGENT 2 DESIGN (Scalability Focus):
---
{designs[2]}
---

AGENT 3 DESIGN (Flexibility Focus):
---
{designs[3]}
---

Your task:
1. Analyze each design's strengths and weaknesses
2. Compare the approaches against the original requirements
3. Select the best design OR synthesize a superior approach combining the best elements
4. Create a final architectural design in {final_design_file}

Output structure for {final_design_file}:

# Final Architecture Design: [Task Name]

## Executive Summary
[Brief summary of the selected/synthesized approach]

## Design Evaluation

### Agent 1 Analysis (Simplicity)
**Strengths:**
- [List key strengths]

**Weaknesses:**
- [List key weaknesses]

**Score:** X/10

### Agent 2 Analysis (Scalability)
**Strengths:**
- [List key strengths]

**Weaknesses:**
- [List key weaknesses]

**Score:** X/10

### Agent 3 Analysis (Flexibility)
**Strengths:**
- [List key strengths]

**Weaknesses:**
- [List key weaknesses]

**Score:** X/10

## Selected Approach
[Either "Agent X Design Selected" or "Synthesized Design"]

## Final Architecture

[Complete architectural design - either the selected agent's design with improvements, or a synthesized approach combining the best elements]

## Justification
[Detailed explanation of why this approach was selected]

## Implementation Roadmap
[High-level phases for implementing this architecture]"""

    print("🔍 Running review agent to evaluate and select best design...")
    
    try:
        await client.query(review_prompt, agent="gad")
        
        async for message in client.receive_response():
            if message.status == "success":
                print("✅ Review completed successfully")
                return True
            elif message.status == "error":
                print(f"❌ Review failed: {message.content}")
                return False
                
    except Exception as e:
        print(f"❌ Review error: {e}")
        return False
    
    return True

async def main():
    """Main orchestration function"""
    
    if len(sys.argv) < 2:
        print("Usage: python multi_agent_design.py '<architecture_task>'")
        print("\nExample:")
        print("  python multi_agent_design.py 'Design a microservice architecture for an e-commerce platform'")
        sys.exit(1)
    
    task = sys.argv[1]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = Path(tempfile.gettempdir()) / f"multi_agent_{timestamp}"
    work_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 Starting multi-agent architecture design process...")
    print(f"📋 Task: {task}")
    print(f"📁 Working directory: {work_dir}")
    print("")
    
    # Run 3 agents in parallel
    print("🔄 Running 3 GAD agents in parallel...")
    print("")
    
    # Create clients for parallel execution
    async with ClaudeSDKClient() as client1, \
               ClaudeSDKClient() as client2, \
               ClaudeSDKClient() as client3:
        
        # Run all three agents concurrently
        results = await asyncio.gather(
            run_design_agent(client1, 1, task, work_dir),
            run_design_agent(client2, 2, task, work_dir),
            run_design_agent(client3, 3, task, work_dir),
            return_exceptions=True
        )
    
    # Count successful agents
    successful = sum(1 for r in results if r is True)
    
    print("")
    
    if successful < 2:
        print(f"❌ Error: Only {successful} agents succeeded. Need at least 2 for comparison.")
        print(f"Check the output files in {work_dir} for details.")
        sys.exit(1)
    
    print(f"✨ {successful} agents completed successfully")
    print("")
    
    # Run review agent
    async with ClaudeSDKClient() as review_client:
        review_success = await run_review_agent(review_client, task, work_dir)
    
    if not review_success:
        print("❌ Review process failed")
        sys.exit(1)
    
    # Display final results
    final_design_file = work_dir / "final_design.md"
    
    print("")
    print("═" * 64)
    print("                    FINAL ARCHITECTURE DESIGN                   ")
    print("═" * 64)
    print("")
    
    if final_design_file.exists():
        print(final_design_file.read_text())
    else:
        print("❌ Error: Final design file not created")
        sys.exit(1)
    
    print("")
    print("═" * 64)
    print("")
    print(f"📁 All designs saved in: {work_dir}")
    print(f"   - Individual designs: design_agent1.md, design_agent2.md, design_agent3.md")
    print(f"   - Final design: final_design.md")
    print("")
    print("✨ Multi-agent architecture design process complete!")

if __name__ == "__main__":
    asyncio.run(main())