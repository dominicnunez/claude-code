#!/usr/bin/env python3
"""
Feature workflow for multi-agent orchestration system.
Implements the /feat command workflow with structural preservation and parallel evaluation.
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
from evaluators.feat_evaluator import FeatEvaluator


class FeatWorkflow:
    """Implements the /feat command workflow."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize feature workflow."""
        self.command_parser = CommandParser()
        self.language_detector = LanguageDetector(config_path)
        self.agent_registry = AgentRegistry()
        self.feat_evaluator = FeatEvaluator()
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
                    "feat_parallel_agent_count": 5,
                    "execution_timeout_seconds": 300,
                    "minimum_agents_for_orchestration": 3
                },
                "user_approval": {
                    "user_feat_approval": False
                },
                "fallback_strategies": {
                    "enable_main_claude_fallback": True,
                    "prompt_user_on_low_confidence": True
                }
            }
            
    async def execute_feat_command(self, command_line: str) -> Dict[str, Any]:
        """
        Execute a /feat command.
        
        Args:
            command_line: Complete command string
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Parse command
            parsed_command = self.command_parser.parse_command(command_line)
            self.command_parser.validate_command(parsed_command)
            
            if parsed_command.command_type != 'feat':
                raise ValueError(f"Expected feat command, got {parsed_command.command_type}")
                
            # Get section identifier
            section_id = parsed_command.section_number or parsed_command.section_name
            if not section_id:
                raise ValueError("No section identifier provided")
                
            # Load app.md for context and structure
            app_md_content = self.persistence.load_app_md()
            if not app_md_content:
                print("Warning: No app.md found. Feature will be generated without structural constraints.")
                expected_structure = []
            else:
                # Extract expected structure from app.md
                expected_structure = self.feat_evaluator.extract_expected_structure(
                    app_md_content, section_id
                )
                print(f"Expected subsections: {expected_structure}")
                
            # Detect language from app.md or project context
            language = self._detect_language_from_context(app_md_content)
            
            # Get architect agents (same as design for consistency)
            if language:
                architect_agents = self.agent_registry.get_best_agents('architecture', language)
            else:
                architect_agents = self.agent_registry.get_best_agents('architecture')
                
            if not architect_agents:
                if self.config["fallback_strategies"]["enable_main_claude_fallback"]:
                    return await self._fallback_to_main_claude(parsed_command, language, app_md_content)
                else:
                    raise RuntimeError("No architect agents available")
                    
            # Limit agent count
            max_agents = self.config["orchestration"]["feat_parallel_agent_count"]
            architect_agents = architect_agents[:max_agents]
            
            min_agents = self.config["orchestration"]["minimum_agents_for_orchestration"]
            if len(architect_agents) < min_agents:
                print(f"Warning: Only {len(architect_agents)} agents available (minimum: {min_agents})")
                
            # Execute parallel feature specification generation
            print(f"Generating feature specification for section {section_id} with {len(architect_agents)} agents...")
            orchestration_result = await self._orchestrate_feature(
                section_id,
                architect_agents,
                language,
                app_md_content
            )
            
            if not orchestration_result.success:
                raise RuntimeError("Feature orchestration failed")
                
            # Evaluate and select best feature specification
            selected_feat, evaluation_results = await self._evaluate_and_select_feature(
                orchestration_result.all_results,
                expected_structure,
                language
            )
            
            # User approval if enabled
            if self.config["user_approval"]["user_feat_approval"]:
                approved_feat = await self._get_user_approval(selected_feat, evaluation_results)
                if approved_feat != selected_feat:
                    selected_feat = approved_feat
                    
            # Validate structural integrity
            if expected_structure:
                structural_validation = self.feat_evaluator.validate_structure(
                    selected_feat['output'],
                    expected_structure
                )
                if not structural_validation.is_valid:
                    print(f"Warning: Selected feature spec has structural issues:")
                    print(f"  Missing sections: {structural_validation.missing_sections}")
                    print(f"  Extra sections: {structural_validation.extra_sections}")
                    
            # Save selected feature specification
            feat_path = self.persistence.save_feature(
                section_id,
                selected_feat['output'],
                {
                    'command': command_line,
                    'section_id': section_id,
                    'language': language,
                    'agent_name': selected_feat['agent_name'],
                    'execution_time': orchestration_result.execution_time,
                    'evaluation_score': evaluation_results[0][1].overall_score if evaluation_results else 0.0,
                    'structural_integrity': structural_validation.structure_score if expected_structure else 1.0,
                    'expected_structure': expected_structure
                }
            )
            
            # Archive non-selected candidates
            non_selected = [result for result in orchestration_result.all_results 
                          if result.agent_name != selected_feat['agent_name']]
            if non_selected:
                candidate_dicts = [asdict(result) for result in non_selected]
                for candidate in candidate_dicts:
                    candidate['section_id'] = section_id
                self.persistence.archive_candidates('feat', candidate_dicts)
                
            return {
                'success': True,
                'feat_path': str(feat_path),
                'section_id': section_id,
                'agent_used': selected_feat['agent_name'],
                'language': language,
                'execution_time': orchestration_result.execution_time,
                'evaluation_score': evaluation_results[0][1].overall_score if evaluation_results else 0.0,
                'structural_score': structural_validation.structure_score if expected_structure else 1.0,
                'agents_used': len(architect_agents),
                'message': f"Feature specification for section {section_id} successfully generated and saved to {feat_path}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"Feature workflow failed: {e}"
            }
            
    def _detect_language_from_context(self, app_md_content: Optional[str]) -> Optional[str]:
        """Detect language from app.md content or project context."""
        # First try to detect from project context
        detection_result = self.language_detector.analyze_project()
        if detection_result.detected_language:
            return detection_result.detected_language
            
        # Try to extract language from app.md content
        if app_md_content:
            content_lower = app_md_content.lower()
            
            # Look for explicit language mentions
            for language in self.language_detector.get_supported_languages():
                if language in content_lower:
                    return language
                    
        return None
        
    async def _orchestrate_feature(self, section_id: str, agents: List, 
                                  language: Optional[str], 
                                  app_md_content: Optional[str]) -> OrchestrationResult:
        """Orchestrate parallel feature specification generation."""
        async with OrchestrationEngine() as engine:
            agent_names = [agent.name for agent in agents]
            return await engine.orchestrate_feature(
                section_id, 
                agent_names, 
                language, 
                app_md_content
            )
            
    async def _evaluate_and_select_feature(self, agent_results: List, 
                                         expected_structure: List[str],
                                         language: Optional[str]) -> tuple:
        """Evaluate feature candidates and select the best one."""
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
            raise RuntimeError("No successful feature specification candidates generated")
            
        # Evaluate candidates with structural constraints
        evaluation_results = self.feat_evaluator.rank_features(
            candidates, 
            expected_structure, 
            language
        )
        
        # Select best candidate (prioritizes structural integrity)
        best_index, best_score = evaluation_results[0]
        selected_feat = candidates[best_index]
        
        print(f"Selected feature specification from {selected_feat['agent_name']} "
              f"(score: {best_score.overall_score:.3f}, "
              f"structural: {best_score.structural_integrity:.3f})")
              
        # Show structural validation results
        if expected_structure:
            validation = best_score.structural_validation
            if validation.is_valid:
                print(f"✓ Structural integrity maintained")
            else:
                print(f"⚠ Structural issues detected:")
                if validation.missing_sections:
                    print(f"  Missing: {', '.join(validation.missing_sections)}")
                if validation.extra_sections:
                    print(f"  Extra: {', '.join(validation.extra_sections)}")
              
        return selected_feat, evaluation_results
        
    async def _get_user_approval(self, selected_feat: Dict, 
                               evaluation_results: List) -> Dict:
        """Get user approval for selected feature specification."""
        print("\n" + "="*60)
        print("FEATURE SPECIFICATION REVIEW")
        print("="*60)
        
        best_index, best_score = evaluation_results[0]
        print(f"Selected Agent: {selected_feat['agent_name']}")
        print(f"Overall Score: {best_score.overall_score:.3f}")
        print(f"Structural Integrity: {best_score.structural_integrity:.3f}")
        print(f"Feedback: {best_score.feedback}")
        
        # Show structural validation
        validation = best_score.structural_validation
        if validation.expected_sections:
            print(f"\nStructural Validation:")
            print(f"  Expected sections: {len(validation.expected_sections)}")
            print(f"  Found sections: {len(validation.found_sections)}")
            if validation.missing_sections:
                print(f"  Missing: {', '.join(validation.missing_sections)}")
            if validation.extra_sections:
                print(f"  Extra: {', '.join(validation.extra_sections)}")
        
        print(f"\nStrengths:")
        for strength in best_score.strengths[:5]:  # Show top 5
            print(f"  + {strength}")
            
        if best_score.weaknesses:
            print(f"\nWeaknesses:")
            for weakness in best_score.weaknesses[:3]:  # Show top 3
                print(f"  - {weakness}")
                
        print(f"\nAlternatives available: {len(evaluation_results) - 1}")
        
        while True:
            choice = input("\nApprove this feature specification? (y/n/s=see alternatives): ").lower().strip()
            
            if choice in ['y', 'yes']:
                return selected_feat
            elif choice in ['n', 'no']:
                return await self._select_alternative(evaluation_results)
            elif choice in ['s', 'see', 'alternatives']:
                return await self._show_alternatives(evaluation_results)
            else:
                print("Please enter y/n/s")
                
    async def _select_alternative(self, evaluation_results: List) -> Dict:
        """Let user select from alternative feature specifications."""
        print("\nAvailable alternatives:")
        for i, (idx, score) in enumerate(evaluation_results[1:6], 1):  # Show top 5 alternatives
            print(f"{i}. Score: {score.overall_score:.3f}, "
                  f"Structural: {score.structural_integrity:.3f}")
            
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
            print(f"\n{i+1}. Overall: {score.overall_score:.3f}, "
                  f"Structural: {score.structural_integrity:.3f}")
            print(f"   Implementation Detail: {score.implementation_detail:.3f}")
            print(f"   Language Specificity: {score.language_specificity:.3f}")
            print(f"   Feedback: {score.feedback}")
            
        while True:
            try:
                choice = input("Select feature specification (1-5): ")
                choice_int = int(choice) - 1
                
                if 0 <= choice_int < min(5, len(evaluation_results)):
                    selected_idx, _ = evaluation_results[choice_int]
                    # Return the actual candidate (simplified)
                    return evaluation_results[choice_int]
                else:
                    print("Invalid choice")
            except ValueError:
                print("Please enter a number")
                
    async def _fallback_to_main_claude(self, parsed_command: ParsedCommand, 
                                     language: Optional[str],
                                     app_md_content: Optional[str]) -> Dict[str, Any]:
        """Fallback to main Claude when no agents available."""
        print("No specialized agents available, using main Claude...")
        
        section_id = parsed_command.section_number or parsed_command.section_name
        
        # Create a basic feature specification
        feat_content = f"""
# Feature Implementation Specification: {section_id}

## Overview
Implementation specification for section {section_id}.

## Implementation Approach
{f"Language: {language}" if language else "Language: To be determined"}

### Core Implementation
- Define main components and their responsibilities
- Implement core algorithms and data structures
- Handle error conditions and edge cases

### Integration Points
- Define interfaces with other components
- Specify data exchange formats
- Handle external dependencies

### Testing Strategy
- Unit tests for core functionality
- Integration tests for component interaction
- Performance tests where applicable

## Technical Details
This specification was generated using fallback mode.
Please refine with specialized architect agents when available.

{f"## Context from app.md:" if app_md_content else ""}
{app_md_content[:500] + "..." if app_md_content and len(app_md_content) > 500 else app_md_content or ""}
"""
        
        # Save fallback feature specification
        feat_path = self.persistence.save_feature(
            section_id,
            feat_content,
            {
                'command': f"/feat {section_id}",
                'section_id': section_id,
                'language': language,
                'agent_name': 'main_claude_fallback',
                'execution_time': 0.0,
                'evaluation_score': 0.5,
                'structural_score': 1.0  # No structural constraints in fallback
            }
        )
        
        return {
            'success': True,
            'feat_path': str(feat_path),
            'section_id': section_id,
            'agent_used': 'main_claude_fallback',
            'language': language,
            'execution_time': 0.0,
            'evaluation_score': 0.5,
            'structural_score': 1.0,
            'agents_used': 0,
            'message': f"Fallback feature specification for section {section_id} generated and saved to {feat_path}"
        }


async def main():
    """Test feature workflow."""
    workflow = FeatWorkflow()
    
    # Test feature command
    result = await workflow.execute_feat_command("/feat 1")
    
    print("Feature Workflow Result:")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Feature spec saved to: {result['feat_path']}")
        print(f"Section ID: {result['section_id']}")
        print(f"Agent used: {result['agent_used']}")
        print(f"Language: {result['language']}")
        print(f"Execution time: {result['execution_time']:.2f}s")
        print(f"Score: {result['evaluation_score']:.3f}")
        print(f"Structural score: {result['structural_score']:.3f}")
    else:
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())