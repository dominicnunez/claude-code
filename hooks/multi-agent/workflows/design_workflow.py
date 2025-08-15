#!/usr/bin/env python3
"""
Design workflow for multi-agent orchestration system.
Implements the /design command workflow with parallel agent execution and evaluation.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

# Import core modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.command_parser import CommandParser, ParsedCommand
from core.language_detection import LanguageDetector
from core.agent_registry import AgentRegistry
from core.orchestration_engine import OrchestrationEngine, AgentTask, OrchestrationResult
from core.persistence import PersistenceManager
from evaluators.design_evaluator import DesignEvaluator


class DesignWorkflow:
    """Implements the /design command workflow."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize design workflow."""
        self.command_parser = CommandParser()
        self.language_detector = LanguageDetector(config_path)
        self.agent_registry = AgentRegistry()
        self.design_evaluator = DesignEvaluator()
        self.persistence = PersistenceManager()
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Scan agents on initialization
        self.agent_registry.scan_agents()
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load workflow configuration."""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "orchestration_config.json"
            
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "orchestration": {
                    "design_parallel_agent_count": 5,
                    "execution_timeout_seconds": 300,
                    "minimum_agents_for_orchestration": 3
                },
                "user_approval": {
                    "user_design_approval": True
                },
                "fallback_strategies": {
                    "enable_main_claude_fallback": True,
                    "prompt_user_on_low_confidence": True
                }
            }
            
    async def execute_design_command(self, command_line: str) -> Dict[str, Any]:
        """
        Execute a /design command.
        
        Args:
            command_line: Complete command string
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Parse command
            parsed_command = self.command_parser.parse_command(command_line)
            self.command_parser.validate_command(parsed_command)
            
            if parsed_command.command_type != 'design':
                raise ValueError(f"Expected design command, got {parsed_command.command_type}")
                
            # Detect language if not specified
            language = parsed_command.language
            if not language:
                detection_result = self.language_detector.analyze_project()
                if detection_result.detected_language:
                    language = detection_result.detected_language
                    print(f"Auto-detected language: {language}")
                elif self.config["fallback_strategies"]["prompt_user_on_low_confidence"]:
                    print(f"Language detection: {detection_result.recommendation}")
                    language = input("Please specify language (or press Enter for generic): ").strip()
                    if not language:
                        language = None
                        
            # Get architect agents
            if language:
                architect_agents = self.agent_registry.get_best_agents('architecture', language)
            else:
                architect_agents = self.agent_registry.get_best_agents('architecture')
                
            if not architect_agents:
                if self.config["fallback_strategies"]["enable_main_claude_fallback"]:
                    return await self._fallback_to_main_claude(parsed_command, language)
                else:
                    raise RuntimeError("No architect agents available")
                    
            # Limit agent count
            max_agents = self.config["orchestration"]["design_parallel_agent_count"]
            architect_agents = architect_agents[:max_agents]
            
            min_agents = self.config["orchestration"]["minimum_agents_for_orchestration"]
            if len(architect_agents) < min_agents:
                print(f"Warning: Only {len(architect_agents)} agents available (minimum: {min_agents})")
                
            # Execute parallel design generation
            print(f"Executing design with {len(architect_agents)} agents...")
            orchestration_result = await self._orchestrate_design(
                parsed_command.description, 
                architect_agents, 
                language
            )
            
            if not orchestration_result.success:
                raise RuntimeError("Design orchestration failed")
                
            # Evaluate and select best design
            selected_design, evaluation_results = await self._evaluate_and_select_design(
                orchestration_result.all_results,
                language
            )
            
            # User approval if enabled
            if self.config["user_approval"]["user_design_approval"]:
                approved_design = await self._get_user_approval(selected_design, evaluation_results)
                if approved_design != selected_design:
                    selected_design = approved_design
                    
            # Save selected design
            design_path = self.persistence.save_design(
                selected_design['output'],
                {
                    'command': command_line,
                    'language': language,
                    'agent_name': selected_design['agent_name'],
                    'execution_time': orchestration_result.execution_time,
                    'evaluation_score': evaluation_results[0][1].overall_score if evaluation_results else 0.0
                }
            )
            
            # Archive non-selected candidates
            non_selected = [result for result in orchestration_result.all_results 
                          if result.agent_name != selected_design['agent_name']]
            if non_selected:
                candidate_dicts = [asdict(result) for result in non_selected]
                self.persistence.archive_candidates('design', candidate_dicts)
                
            return {
                'success': True,
                'design_path': str(design_path),
                'agent_used': selected_design['agent_name'],
                'language': language,
                'execution_time': orchestration_result.execution_time,
                'evaluation_score': evaluation_results[0][1].overall_score if evaluation_results else 0.0,
                'agents_used': len(architect_agents),
                'message': f"Design successfully generated and saved to {design_path}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"Design workflow failed: {e}"
            }
            
    async def _orchestrate_design(self, description: str, agents: List, 
                                 language: Optional[str]) -> OrchestrationResult:
        """Orchestrate parallel design generation."""
        async with OrchestrationEngine() as engine:
            agent_names = [agent.name for agent in agents]
            return await engine.orchestrate_design(description, agent_names, language)
            
    async def _evaluate_and_select_design(self, agent_results: List, 
                                        language: Optional[str]) -> tuple:
        """Evaluate design candidates and select the best one."""
        # Convert results to evaluation format
        candidates = []
        for result in agent_results:
            if result.success:
                candidates.append({
                    'agent_name': result.agent_name,
                    'output': result.output,
                    'execution_time': result.execution_time,
                    'metadata': result.metadata
                })
                
        if not candidates:
            raise RuntimeError("No successful design candidates generated")
            
        # Evaluate candidates
        evaluation_results = self.design_evaluator.rank_designs(candidates, language)
        
        # Select best candidate
        best_index, best_score = evaluation_results[0]
        selected_design = candidates[best_index]
        
        print(f"Selected design from {selected_design['agent_name']} "
              f"(score: {best_score.overall_score:.3f})")
              
        return selected_design, evaluation_results
        
    async def _get_user_approval(self, selected_design: Dict, 
                               evaluation_results: List) -> Dict:
        """Get user approval for selected design."""
        print("\n" + "="*60)
        print("DESIGN SELECTION REVIEW")
        print("="*60)
        
        best_index, best_score = evaluation_results[0]
        print(f"Selected Agent: {selected_design['agent_name']}")
        print(f"Overall Score: {best_score.overall_score:.3f}")
        print(f"Feedback: {best_score.feedback}")
        
        print(f"\nStrengths:")
        for strength in best_score.strengths:
            print(f"  + {strength}")
            
        if best_score.weaknesses:
            print(f"\nWeaknesses:")
            for weakness in best_score.weaknesses:
                print(f"  - {weakness}")
                
        print(f"\nAlternatives available: {len(evaluation_results) - 1}")
        
        while True:
            choice = input("\nApprove this design? (y/n/s=see alternatives/r=regenerate): ").lower().strip()
            
            if choice in ['y', 'yes']:
                return selected_design
            elif choice in ['n', 'no']:
                return await self._select_alternative(evaluation_results)
            elif choice in ['s', 'see', 'alternatives']:
                return await self._show_alternatives(evaluation_results)
            elif choice in ['r', 'regenerate']:
                raise RuntimeError("User requested regeneration (not implemented)")
            else:
                print("Please enter y/n/s/r")
                
    async def _select_alternative(self, evaluation_results: List) -> Dict:
        """Let user select from alternative designs."""
        print("\nAvailable alternatives:")
        for i, (idx, score) in enumerate(evaluation_results[1:6], 1):  # Show top 5 alternatives
            agent_name = score.feedback  # This is simplified
            print(f"{i}. Agent: {agent_name}, Score: {score.overall_score:.3f}")
            
        while True:
            try:
                choice = input("Select alternative (1-5) or 0 to return to best: ")
                choice_int = int(choice)
                
                if choice_int == 0:
                    return evaluation_results[0]
                elif 1 <= choice_int <= min(5, len(evaluation_results) - 1):
                    return evaluation_results[choice_int]
                else:
                    print("Invalid choice")
            except ValueError:
                print("Please enter a number")
                
    async def _show_alternatives(self, evaluation_results: List) -> Dict:
        """Show detailed alternatives and let user choose."""
        print("\nDetailed alternatives:")
        for i, (idx, score) in enumerate(evaluation_results[:5]):
            print(f"\n{i+1}. Score: {score.overall_score:.3f}")
            print(f"   Feedback: {score.feedback}")
            print(f"   Strengths: {', '.join(score.strengths[:3])}")
            
        while True:
            try:
                choice = input("Select design (1-5): ")
                choice_int = int(choice) - 1
                
                if 0 <= choice_int < min(5, len(evaluation_results)):
                    selected_idx, _ = evaluation_results[choice_int]
                    # Need to get the actual candidate data
                    # This is simplified - in real implementation would track candidates
                    return evaluation_results[choice_int]
                else:
                    print("Invalid choice")
            except ValueError:
                print("Please enter a number")
                
    async def _fallback_to_main_claude(self, parsed_command: ParsedCommand, 
                                     language: Optional[str]) -> Dict[str, Any]:
        """Fallback to main Claude when no agents available."""
        print("No specialized agents available, using main Claude...")
        
        # Create a simple design using basic orchestration
        # This is a simplified fallback implementation
        design_content = f"""
# {parsed_command.description.title()} Design

## System Overview
This is a high-level architectural design for: {parsed_command.description}

## Core Components
- Component 1: [To be defined]
- Component 2: [To be defined]
- Component 3: [To be defined]

## Technology Stack
{f"Language: {language}" if language else "Language: To be determined"}

## Implementation Notes
This design was generated using fallback mode.
Please refine with specialized architect agents when available.
"""
        
        # Save fallback design
        design_path = self.persistence.save_design(
            design_content,
            {
                'command': f"/design {parsed_command.description}",
                'language': language,
                'agent_name': 'main_claude_fallback',
                'execution_time': 0.0,
                'evaluation_score': 0.5
            }
        )
        
        return {
            'success': True,
            'design_path': str(design_path),
            'agent_used': 'main_claude_fallback',
            'language': language,
            'execution_time': 0.0,
            'evaluation_score': 0.5,
            'agents_used': 0,
            'message': f"Fallback design generated and saved to {design_path}"
        }


async def main():
    """Test design workflow."""
    workflow = DesignWorkflow()
    
    # Test design command
    result = await workflow.execute_design_command("/design go pomodoro timer")
    
    print("Design Workflow Result:")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Design saved to: {result['design_path']}")
        print(f"Agent used: {result['agent_used']}")
        print(f"Language: {result['language']}")
        print(f"Execution time: {result['execution_time']:.2f}s")
        print(f"Score: {result['evaluation_score']:.3f}")
    else:
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())