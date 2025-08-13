#!/usr/bin/env python3
"""
Iterative Multi-Agent Architecture Design System
Loops through design-review cycles until comprehensive documentation is achieved
"""

import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from claude_sdk import ClaudeSDKClient

class DesignIterator:
    def __init__(self, features: List[str], task: str, work_dir: Path):
        self.features = features
        self.task = task
        self.work_dir = work_dir
        self.iteration = 0
        self.max_iterations = 5
        self.design_history = []
        self.coverage_scores = []
        
    async def run_design_agent(self, client, agent_num: int, iteration: int, feedback: str = "") -> bool:
        """Run a single GAD agent with specific focus and iteration feedback"""
        
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
        design_file = self.work_dir / f"iteration_{iteration}" / f"design_agent{agent_num}.md"
        design_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Build feature checklist
        feature_list = "\n".join(f"- [ ] {feature}" for feature in self.features)
        
        # Add iteration context if not first iteration
        iteration_context = ""
        if iteration > 1 and feedback:
            iteration_context = f"""
## Iteration {iteration} Context
Previous iteration feedback:
{feedback}

You must address the gaps identified and ensure all features are fully designed.
"""
        
        prompt = f"""You are GAD agent #{agent_num} (Iteration {iteration}). Focus on {focus}.

Task: {self.task}

## Required Features (ALL must be addressed):
{feature_list}

{iteration_context}

Create your architectural design in {design_file}

Requirements:
{chr(10).join(f"{i+1}. {req}" for i, req in enumerate(requirements))}

## Design Output Requirements:
1. Address EVERY feature in the list above
2. For each feature, provide:
   - Component design
   - Interface definitions
   - Data flow
   - Integration points
3. Mark each feature with coverage level:
   - [x] Fully designed
   - [~] Partially designed
   - [ ] Not addressed

Output your comprehensive design to {design_file}"""

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

    async def run_review_agent(self, client, iteration: int) -> Tuple[bool, float, str]:
        """
        Run review agent to analyze designs and determine if comprehensive
        Returns: (is_complete, coverage_score, feedback)
        """
        
        iter_dir = self.work_dir / f"iteration_{iteration}"
        
        # Read all design files
        designs = {}
        for i in range(1, 4):
            design_file = iter_dir / f"design_agent{i}.md"
            if design_file.exists():
                designs[i] = design_file.read_text()
            else:
                designs[i] = "Design not available - agent failed"
        
        review_file = iter_dir / "review.md"
        
        # Build feature checklist for review
        feature_checklist = "\n".join(f"{i+1}. {feature}" for i, feature in enumerate(self.features))
        
        review_prompt = f"""You are a senior architecture review specialist reviewing iteration {iteration} of the design process.

Original Task: {self.task}

## Required Features to Cover:
{feature_checklist}

## Designs to Review:

### AGENT 1 DESIGN (Simplicity Focus):
{designs[1]}

### AGENT 2 DESIGN (Scalability Focus):
{designs[2]}

### AGENT 3 DESIGN (Flexibility Focus):
{designs[3]}

## Your Review Tasks:

1. **Feature Coverage Analysis**
   For EACH required feature, assess:
   - Is it fully addressed across the designs?
   - Are there clear component designs?
   - Are interfaces well-defined?
   - Is the data flow documented?
   
2. **Completeness Score**
   Calculate a coverage percentage (0-100%) based on:
   - How many features are fully designed
   - Depth of architectural detail
   - Clarity of implementation path
   
3. **Synthesis Decision**
   Either:
   - SELECT the most comprehensive design
   - SYNTHESIZE a complete design combining best elements
   - IDENTIFY gaps that need another iteration

4. **Create Output Document** in {review_file}:

# Architecture Review - Iteration {iteration}

## Coverage Analysis
[Feature-by-feature coverage assessment]

## Completeness Score: XX%

## Design Evaluation
[Evaluation of each agent's design]

## Decision: [COMPLETE/NEEDS_REFINEMENT]

## Synthesized Architecture (if COMPLETE)
[Final comprehensive architecture combining best elements]

## Gaps Requiring Refinement (if NEEDS_REFINEMENT)
[Specific gaps that need to be addressed in next iteration]

## Feedback for Next Iteration (if NEEDS_REFINEMENT)
[Specific guidance for agents in next iteration]

IMPORTANT: Only mark as COMPLETE if coverage is >= 90% and all critical features are fully designed."""

        print(f"🔍 Running review for iteration {iteration}...")
        
        try:
            await client.query(review_prompt, agent="gad")
            
            async for message in client.receive_response():
                if message.status == "success":
                    # Parse the review to extract completeness
                    if review_file.exists():
                        review_content = review_file.read_text()
                        
                        # Extract completeness score
                        import re
                        score_match = re.search(r'Completeness Score:\s*(\d+)%', review_content)
                        score = float(score_match.group(1)) if score_match else 0.0
                        
                        # Check if complete
                        is_complete = "Decision: COMPLETE" in review_content
                        
                        # Extract feedback
                        feedback_match = re.search(r'## Feedback for Next Iteration.*?\n(.*?)(?=\n#|\Z)', 
                                                 review_content, re.DOTALL)
                        feedback = feedback_match.group(1).strip() if feedback_match else ""
                        
                        return is_complete, score, feedback
                    
                    return False, 0.0, "Review file not created"
                    
        except Exception as e:
            print(f"  ❌ Review error: {e}")
            return False, 0.0, str(e)
        
        return False, 0.0, "Review failed"

    async def iterate_until_complete(self) -> Path:
        """Main iteration loop that continues until comprehensive design is achieved"""
        
        feedback = ""
        
        for iteration in range(1, self.max_iterations + 1):
            print(f"\n{'='*60}")
            print(f"🔄 ITERATION {iteration}/{self.max_iterations}")
            print(f"{'='*60}\n")
            
            # Run 3 agents in parallel
            print("📐 Running 3 GAD agents in parallel...")
            
            async with ClaudeSDKClient() as client1, \
                       ClaudeSDKClient() as client2, \
                       ClaudeSDKClient() as client3:
                
                results = await asyncio.gather(
                    self.run_design_agent(client1, 1, iteration, feedback),
                    self.run_design_agent(client2, 2, iteration, feedback),
                    self.run_design_agent(client3, 3, iteration, feedback),
                    return_exceptions=True
                )
            
            successful = sum(1 for r in results if r is True)
            
            if successful < 2:
                print(f"  ⚠️ Only {successful}/3 agents succeeded")
                if iteration == self.max_iterations:
                    print("  ❌ Max iterations reached with insufficient agents")
                    break
                continue
            
            print(f"  ✅ {successful}/3 agents completed")
            
            # Run review agent
            async with ClaudeSDKClient() as review_client:
                is_complete, score, feedback = await self.run_review_agent(review_client, iteration)
            
            self.coverage_scores.append(score)
            print(f"  📊 Coverage Score: {score}%")
            
            if is_complete:
                print(f"  ✨ DESIGN COMPLETE! Achieved comprehensive coverage.")
                return self.work_dir / f"iteration_{iteration}" / "review.md"
            
            if iteration < self.max_iterations:
                print(f"  🔄 Design needs refinement. Moving to iteration {iteration + 1}...")
                print(f"  💡 Feedback: {feedback[:200]}..." if len(feedback) > 200 else f"  💡 Feedback: {feedback}")
            else:
                print(f"  ⚠️ Max iterations reached. Coverage: {score}%")
                return self.work_dir / f"iteration_{iteration}" / "review.md"
        
        # Return best iteration if we didn't achieve complete
        if self.coverage_scores:
            best_iteration = self.coverage_scores.index(max(self.coverage_scores)) + 1
            return self.work_dir / f"iteration_{best_iteration}" / "review.md"
        
        return None

    async def build_final_documentation(self, final_review_path: Path) -> Path:
        """Build comprehensive documentation from the final iteration"""
        
        # Output to plan.md in current directory (comprehensive system architecture)
        plan_path = Path.cwd() / "plan.md"
        # Also keep a copy in work directory
        final_doc_path = self.work_dir / "FINAL_ARCHITECTURE.md"
        iteration = int(final_review_path.parent.name.split('_')[1])
        
        # Read all relevant files
        review_content = final_review_path.read_text() if final_review_path.exists() else ""
        
        designs = {}
        for i in range(1, 4):
            design_file = final_review_path.parent / f"design_agent{i}.md"
            if design_file.exists():
                designs[i] = design_file.read_text()
        
        doc_prompt = f"""Create comprehensive final architecture documentation combining all work from iteration {iteration}.

## Review Content:
{review_content}

## All Agent Designs:
{chr(10).join(f"### Agent {i}:\n{content}" for i, content in designs.items())}

Create a complete, production-ready architecture document in plan.md with:

# {self.task} - Complete Architecture

## Executive Summary
[Brief overview of the architecture]

## Table of Contents
[Auto-generated TOC]

## 1. System Overview
### 1.1 Purpose and Scope
### 1.2 Key Features
{chr(10).join(f"- {feature}" for feature in self.features)}
### 1.3 Architecture Principles

## 2. High-Level Architecture
### 2.1 System Diagram
### 2.2 Component Overview
### 2.3 Technology Stack

## 3. Detailed Component Design
[For each major component, include:]
### 3.X Component Name
#### Purpose
#### Responsibilities
#### Interfaces
#### Dependencies
#### Data Model
#### Key Algorithms/Patterns

## 4. Data Architecture
### 4.1 Data Models
### 4.2 Data Flow
### 4.3 Storage Strategy
### 4.4 Caching Strategy

## 5. API Design
### 5.1 External APIs
### 5.2 Internal APIs
### 5.3 Event/Message Contracts

## 6. Security Architecture
### 6.1 Authentication & Authorization
### 6.2 Data Security
### 6.3 Network Security

## 7. Scalability & Performance
### 7.1 Scaling Strategy
### 7.2 Performance Optimizations
### 7.3 Load Distribution

## 8. Operational Considerations
### 8.1 Deployment Architecture
### 8.2 Monitoring & Observability
### 8.3 Disaster Recovery

## 9. Implementation Roadmap
### 9.1 Phase 1: Foundation
### 9.2 Phase 2: Core Features
### 9.3 Phase 3: Advanced Features
### 9.4 Phase 4: Optimization

## 10. Appendices
### A. Decision Log
### B. Glossary
### C. References

Make this a comprehensive, production-ready document that a development team could use to build the system."""

        print("\n📚 Building final comprehensive documentation...")
        
        async with ClaudeSDKClient() as client:
            await client.query(doc_prompt, agent="gad")
            
            async for message in client.receive_response():
                if message.status == "success":
                    print("  ✅ Final documentation created")
                    # The GAD agent should have created plan.md
                    if plan_path.exists():
                        # Also save a copy in work directory
                        final_doc_path.write_text(plan_path.read_text())
                        print(f"  📄 Created: plan.md (comprehensive system architecture)")
                        return plan_path
                    return final_doc_path
        
        return plan_path if plan_path.exists() else final_doc_path


async def main():
    """Main orchestration function"""
    
    if len(sys.argv) < 2:
        print("Usage: python iterative_design_system.py '<app_description>' [features.json]")
        print("\nExample 1 (inline features):")
        print("  python iterative_design_system.py 'E-commerce platform with real-time inventory'")
        print("\nExample 2 (features file):")
        print("  python iterative_design_system.py 'E-commerce platform' features.json")
        print("\nFeatures file format:")
        print('  ["User authentication and authorization",')
        print('   "Product catalog with search",')
        print('   "Shopping cart with session persistence",')
        print('   "Payment processing with multiple gateways",')
        print('   "Real-time inventory tracking"]')
        sys.exit(1)
    
    task = sys.argv[1]
    
    # Load features from file or parse from task
    features = []
    if len(sys.argv) > 2:
        features_file = sys.argv[2]
        if Path(features_file).exists():
            with open(features_file, 'r') as f:
                features = json.load(f)
        else:
            print(f"❌ Features file not found: {features_file}")
            sys.exit(1)
    else:
        # Extract features from task description using an agent
        print("🔍 Analyzing requirements to extract features...")
        
        feature_prompt = f"""Extract a comprehensive list of features from this app description:
        
{task}

Output a JSON array of specific features that need to be architecturally designed.
Each feature should be concrete and implementable.

Example output:
["User authentication system", "REST API endpoints", "Database schema design"]

Output ONLY the JSON array, no other text."""
        
        async with ClaudeSDKClient() as client:
            await client.query(feature_prompt)
            
            async for message in client.receive_response():
                if message.status == "success" and message.content:
                    try:
                        import re
                        # Extract JSON array from response
                        json_match = re.search(r'\[.*\]', message.content, re.DOTALL)
                        if json_match:
                            features = json.loads(json_match.group())
                    except:
                        print("  ⚠️ Could not parse features, using task as single feature")
                        features = [task]
    
    if not features:
        print("❌ No features identified")
        sys.exit(1)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = Path(tempfile.gettempdir()) / f"iterative_design_{timestamp}"
    work_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("🚀 ITERATIVE MULTI-AGENT ARCHITECTURE DESIGN SYSTEM")
    print("="*60)
    print(f"📋 Task: {task}")
    print(f"📊 Features to Design: {len(features)}")
    for i, feature in enumerate(features, 1):
        print(f"   {i}. {feature}")
    print(f"📁 Working directory: {work_dir}")
    print("="*60)
    
    # Create iterator and run
    iterator = DesignIterator(features, task, work_dir)
    final_review = await iterator.iterate_until_complete()
    
    if final_review:
        # Build comprehensive documentation
        final_doc = await iterator.build_final_documentation(final_review)
        
        # Display results
        print("\n" + "="*60)
        print("              FINAL ARCHITECTURE DOCUMENTATION              ")
        print("="*60 + "\n")
        
        if final_doc and final_doc.exists():
            content = final_doc.read_text()
            # Display first 100 lines or full if shorter
            lines = content.split('\n')
            if len(lines) > 100:
                print('\n'.join(lines[:100]))
                print(f"\n... [{len(lines) - 100} more lines] ...\n")
            else:
                print(content)
        
        print("\n" + "="*60)
        print(f"📁 All iterations saved in: {work_dir}")
        if final_doc.name == "plan.md":
            print(f"📄 System architecture: plan.md (comprehensive design)")
        else:
            print(f"📄 Final documentation: {final_doc}")
        print(f"📊 Coverage progression: {' → '.join(f'{s:.0f}%' for s in iterator.coverage_scores)}")
        print("✨ Iterative design process complete!")
    else:
        print("\n❌ Design process failed to produce final documentation")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())