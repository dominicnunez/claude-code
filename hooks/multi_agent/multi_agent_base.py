#!/usr/bin/env python3
"""
Multi-Agent Base Class
Reusable framework for 3-worker/1-reviewer agent orchestration pattern
"""

import asyncio
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from claude_sdk import ClaudeSDKClient


class MultiAgentOrchestrator(ABC):
    """
    Base class for orchestrating 3 parallel agents with review and retry.
    Inherit from this class and implement the abstract methods for your specific use case.
    """
    
    def __init__(self, task: str, work_dir: Optional[Path] = None, max_retries: int = 1):
        """
        Initialize the orchestrator.
        
        Args:
            task: Description of the task to perform
            work_dir: Working directory for temporary files (auto-created if None)
            max_retries: Maximum number of retry attempts (default 1)
        """
        self.task = task
        self.max_retries = max_retries
        self.attempt = 0
        
        if work_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.work_dir = Path(tempfile.gettempdir()) / f"multi_agent_{timestamp}"
            self.work_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.work_dir = work_dir
    
    @abstractmethod
    def get_agent_focuses(self) -> Dict[int, Tuple[str, List[str]]]:
        """
        Define the focus areas for each of the 3 agents.
        
        Returns:
            Dict mapping agent number (1-3) to (focus_name, requirements_list)
            
        Example:
            return {
                1: ("SIMPLICITY", ["Keep it simple", "Minimize complexity"]),
                2: ("PERFORMANCE", ["Optimize for speed", "Minimize allocations"]),
                3: ("FLEXIBILITY", ["Design for change", "Use interfaces"])
            }
        """
        pass
    
    @abstractmethod
    def get_agent_prompt(self, agent_num: int, attempt: int, focus: str, 
                         requirements: List[str], feedback: str = "") -> str:
        """
        Generate the prompt for a specific agent.
        
        Args:
            agent_num: Agent number (1-3)
            attempt: Current attempt number
            focus: The agent's focus area name
            requirements: List of requirements for this focus
            feedback: Feedback from previous attempt (empty on first attempt)
            
        Returns:
            Complete prompt string for the agent
        """
        pass
    
    @abstractmethod
    def get_review_prompt(self, attempt: int, agent_outputs: Dict[int, str]) -> str:
        """
        Generate the prompt for the review agent.
        
        Args:
            attempt: Current attempt number
            agent_outputs: Dict mapping agent number to their output
            
        Returns:
            Complete prompt string for the review agent
        """
        pass
    
    @abstractmethod
    def parse_review_decision(self, review_output: str, attempt: int) -> Tuple[str, Any, str]:
        """
        Parse the review agent's output to extract decision and feedback.
        
        Args:
            review_output: The review agent's output
            attempt: Current attempt number
            
        Returns:
            Tuple of (decision, result, feedback)
            - decision: "ACCEPT", "RETRY", "ESCALATE", etc.
            - result: The final result if accepted (varies by implementation)
            - feedback: Feedback for retry (empty if not retrying)
        """
        pass
    
    @abstractmethod
    def get_agent_type(self) -> str:
        """
        Return the agent type to use (e.g., "gad", "god").
        
        Returns:
            Agent type string
        """
        pass
    
    @abstractmethod
    def save_final_output(self, result: Any) -> Path:
        """
        Save the final output to appropriate files.
        
        Args:
            result: The final result from review
            
        Returns:
            Path to the primary output file
        """
        pass
    
    @abstractmethod
    def get_output_description(self) -> str:
        """
        Get a description of what this orchestrator produces.
        
        Returns:
            Description string (e.g., "architecture design", "Go implementation")
        """
        pass
    
    async def run_agent(self, client: ClaudeSDKClient, agent_num: int, 
                       attempt: int, feedback: str = "") -> Optional[str]:
        """
        Run a single agent and return its output.
        
        Args:
            client: Claude SDK client
            agent_num: Agent number (1-3)
            attempt: Current attempt number
            feedback: Feedback from previous attempt
            
        Returns:
            Agent output or None if failed
        """
        focuses = self.get_agent_focuses()
        focus, requirements = focuses[agent_num]
        
        # Get output file path for this agent
        output_file = self.work_dir / f"attempt_{attempt}" / f"agent_{agent_num}_output.txt"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate prompt
        prompt = self.get_agent_prompt(agent_num, attempt, focus, requirements, feedback)
        
        print(f"  🤖 Agent #{agent_num} (Focus: {focus})...")
        
        try:
            await client.query(prompt, agent=self.get_agent_type())
            
            async for message in client.receive_response():
                if message.status == "success":
                    # Save output to file
                    output_file.write_text(message.content or "")
                    return message.content
                elif message.status == "error":
                    print(f"    ❌ Agent #{agent_num} failed: {message.content}")
                    return None
                    
        except Exception as e:
            print(f"    ❌ Agent #{agent_num} error: {e}")
            return None
        
        return None
    
    async def run_review(self, client: ClaudeSDKClient, attempt: int, 
                        agent_outputs: Dict[int, str]) -> Tuple[str, Any, str]:
        """
        Run the review agent.
        
        Args:
            client: Claude SDK client
            attempt: Current attempt number
            agent_outputs: Dict mapping agent number to their output
            
        Returns:
            Tuple of (decision, result, feedback)
        """
        review_file = self.work_dir / f"attempt_{attempt}" / "review.txt"
        review_file.parent.mkdir(parents=True, exist_ok=True)
        
        prompt = self.get_review_prompt(attempt, agent_outputs)
        
        print(f"🔍 Running review for attempt {attempt}...")
        
        try:
            await client.query(prompt, agent=self.get_agent_type())
            
            async for message in client.receive_response():
                if message.status == "success":
                    review_output = message.content or ""
                    review_file.write_text(review_output)
                    return self.parse_review_decision(review_output, attempt)
                    
        except Exception as e:
            print(f"  ❌ Review error: {e}")
            return "ACCEPT", None, ""  # Default to accept on error
        
        return "ACCEPT", None, ""
    
    async def orchestrate(self) -> Tuple[bool, Optional[Path]]:
        """
        Main orchestration loop.
        
        Returns:
            Tuple of (success, output_path)
        """
        feedback = ""
        
        for attempt in range(1, self.max_retries + 2):
            print(f"\n{'='*60}")
            print(f"🔄 ATTEMPT {attempt}/{self.max_retries + 1} - {self.get_output_description().upper()}")
            print(f"{'='*60}\n")
            
            # Run 3 agents in parallel
            print(f"🚀 Running 3 {self.get_agent_type().upper()} agents in parallel...")
            
            async with ClaudeSDKClient() as client1, \
                       ClaudeSDKClient() as client2, \
                       ClaudeSDKClient() as client3:
                
                results = await asyncio.gather(
                    self.run_agent(client1, 1, attempt, feedback),
                    self.run_agent(client2, 2, attempt, feedback),
                    self.run_agent(client3, 3, attempt, feedback),
                    return_exceptions=True
                )
            
            # Process results
            agent_outputs = {}
            successful = 0
            for i, result in enumerate(results, 1):
                if isinstance(result, str) and result:
                    agent_outputs[i] = result
                    successful += 1
                elif isinstance(result, Exception):
                    print(f"  ❌ Agent {i} exception: {result}")
                    agent_outputs[i] = f"Agent {i} failed with error"
                else:
                    agent_outputs[i] = f"Agent {i} produced no output"
            
            if successful == 0:
                print(f"  ❌ All agents failed. Cannot proceed.")
                return False, None
            
            print(f"  ✅ {successful}/3 agents completed successfully")
            
            # Run review agent
            async with ClaudeSDKClient() as review_client:
                decision, result, feedback = await self.run_review(
                    review_client, attempt, agent_outputs
                )
            
            print(f"  📊 Review Decision: {decision}")
            
            if decision == "ACCEPT":
                print(f"  ✨ {self.get_output_description()} ACCEPTED!")
                if result is not None:
                    output_path = self.save_final_output(result)
                    return True, output_path
                else:
                    print(f"  ⚠️ Accepted but no result to save")
                    return False, None
            
            elif decision == "RETRY" and attempt < self.max_retries + 1:
                print(f"  🔄 Retry requested. Incorporating feedback...")
                if feedback:
                    print(f"  💡 Feedback: {feedback[:200]}..." if len(feedback) > 200 else f"  💡 Feedback: {feedback}")
                continue
            
            elif decision == "ESCALATE":
                print(f"  ⚠️ Task too complex for this process")
                print(f"  💡 Consider breaking down the task or using a different approach")
                return False, None
            
            else:
                # Unknown decision or max retries reached
                if attempt >= self.max_retries + 1:
                    print(f"  ⚠️ Max retries reached")
                else:
                    print(f"  ⚠️ Unknown decision: {decision}")
                
                if result is not None:
                    output_path = self.save_final_output(result)
                    return True, output_path
                return False, None
        
        print(f"  ❌ Orchestration failed after all attempts")
        return False, None
    
    def print_summary(self, success: bool, output_path: Optional[Path]):
        """
        Print a summary of the orchestration results.
        
        Args:
            success: Whether the orchestration succeeded
            output_path: Path to the output file (if any)
        """
        print("\n" + "="*60)
        
        if success and output_path:
            print(f"              {self.get_output_description().upper()} COMPLETE              ")
            print("="*60 + "\n")
            print(f"✨ Success! Output saved to: {output_path}")
        else:
            print(f"              {self.get_output_description().upper()} FAILED              ")
            print("="*60 + "\n")
            print(f"❌ Process did not complete successfully")
        
        print(f"📁 Working directory: {self.work_dir}")


# Example usage - inherit and implement for specific use cases:
"""
class FeatureDesigner(MultiAgentOrchestrator):
    def get_agent_focuses(self) -> Dict[int, Tuple[str, List[str]]]:
        return {
            1: ("SIMPLICITY", ["Keep it simple", "Minimize complexity"]),
            2: ("SCALABILITY", ["Design for scale", "Handle growth"]),
            3: ("FLEXIBILITY", ["Enable changes", "Use abstractions"])
        }
    
    def get_agent_type(self) -> str:
        return "gad"
    
    def get_output_description(self) -> str:
        return "architecture design"
    
    # ... implement other abstract methods ...

# Use it:
designer = FeatureDesigner("Design auth system")
success, output = await designer.orchestrate()
designer.print_summary(success, output)
"""