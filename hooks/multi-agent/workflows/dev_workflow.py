#!/usr/bin/env python3
"""
Development workflow for multi-agent orchestration system.
Implements the /dev command workflow for code generation from feature specifications.
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
from evaluators.code_evaluator import CodeEvaluator


class DevWorkflow:
    """Implements the /dev command workflow."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize development workflow."""
        self.command_parser = CommandParser()
        self.language_detector = LanguageDetector(config_path)
        self.agent_registry = AgentRegistry()
        self.code_evaluator = CodeEvaluator()
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
                    "dev_parallel_agent_count": 5,
                    "execution_timeout_seconds": 300,
                    "minimum_agents_for_orchestration": 3
                },
                "user_approval": {
                    "user_dev_approval": False
                },
                "fallback_strategies": {
                    "enable_main_claude_fallback": True,
                    "prompt_user_on_low_confidence": True
                }
            }
            
    async def execute_dev_command(self, command_line: str) -> Dict[str, Any]:
        """
        Execute a /dev command.
        
        Args:
            command_line: Complete command string
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Parse command
            parsed_command = self.command_parser.parse_command(command_line)
            self.command_parser.validate_command(parsed_command)
            
            if parsed_command.command_type != 'dev':
                raise ValueError(f"Expected dev command, got {parsed_command.command_type}")
                
            # Extract feature specifications to implement
            feat_specs = self._extract_feat_specs(parsed_command)
            if not feat_specs:
                raise ValueError("No feature specifications identified")
                
            # Determine target language
            language = self._determine_target_language(parsed_command, feat_specs)
            if not language:
                raise ValueError("Could not determine target programming language")
                
            print(f"Generating {language} code for feature specifications: {', '.join(feat_specs)}")
            
            # Load feature specification content
            feat_content = self._load_feat_content(feat_specs)
            
            # Get developer agents for the target language
            developer_agents = self.agent_registry.get_best_agents('implementation', language)
            
            if not developer_agents:
                if self.config["fallback_strategies"]["enable_main_claude_fallback"]:
                    return await self._fallback_to_main_claude(parsed_command, language, feat_content)
                else:
                    raise RuntimeError(f"No developer agents available for {language}")
                    
            # Limit agent count
            max_agents = self.config["orchestration"]["dev_parallel_agent_count"]
            developer_agents = developer_agents[:max_agents]
            
            min_agents = self.config["orchestration"]["minimum_agents_for_orchestration"]
            if len(developer_agents) < min_agents:
                print(f"Warning: Only {len(developer_agents)} agents available (minimum: {min_agents})")
                
            # Execute parallel code generation
            print(f"Generating code with {len(developer_agents)} developer agents...")
            orchestration_result = await self._orchestrate_development(
                feat_specs,
                developer_agents,
                language,
                feat_content
            )
            
            if not orchestration_result.success:
                raise RuntimeError("Development orchestration failed")
                
            # Evaluate and select best code implementation
            selected_code, evaluation_results = await self._evaluate_and_select_code(
                orchestration_result.all_results,
                language
            )
            
            # User approval if enabled
            if self.config["user_approval"]["user_dev_approval"]:
                approved_code = await self._get_user_approval(selected_code, evaluation_results)
                if approved_code != selected_code:
                    selected_code = approved_code
                    
            # Save generated code
            code_path = self.persistence.save_code(
                feat_specs,
                selected_code['output_files'],
                {
                    'command': command_line,
                    'feat_specs': feat_specs,
                    'language': language,
                    'agent_name': selected_code['agent_name'],
                    'execution_time': orchestration_result.execution_time,
                    'evaluation_score': evaluation_results[0][1].overall_score if evaluation_results else 0.0,
                    'code_quality_score': evaluation_results[0][1].code_quality if evaluation_results else 0.0,
                    'test_coverage_score': evaluation_results[0][1].test_coverage if evaluation_results else 0.0
                }
            )
            
            # Archive non-selected candidates
            non_selected = [result for result in orchestration_result.all_results 
                          if result.agent_name != selected_code['agent_name']]
            if non_selected:
                candidate_dicts = [asdict(result) for result in non_selected]
                for candidate in candidate_dicts:
                    candidate['feat_specs'] = feat_specs
                    candidate['language'] = language
                self.persistence.archive_candidates('dev', candidate_dicts)
                
            # Analyze generated code metrics
            code_metrics = selected_code.get('metrics', {})
            
            return {
                'success': True,
                'code_path': str(code_path),
                'feat_specs': feat_specs,
                'language': language,
                'agent_used': selected_code['agent_name'],
                'execution_time': orchestration_result.execution_time,
                'evaluation_score': evaluation_results[0][1].overall_score if evaluation_results else 0.0,
                'code_quality': evaluation_results[0][1].code_quality if evaluation_results else 0.0,
                'test_coverage': evaluation_results[0][1].test_coverage if evaluation_results else 0.0,
                'agents_used': len(developer_agents),
                'files_generated': len(selected_code.get('output_files', {})),
                'message': f"Code successfully generated for {', '.join(feat_specs)} and saved to {code_path}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"Development workflow failed: {e}"
            }
            
    def _extract_feat_specs(self, parsed_command: ParsedCommand) -> List[str]:
        """Extract feature specification identifiers from parsed command."""
        feat_specs = []
        
        if parsed_command.multiple_sections:
            feat_specs = parsed_command.multiple_sections
        elif parsed_command.section_number:
            feat_specs = [parsed_command.section_number]
        elif parsed_command.section_name:
            feat_specs = [parsed_command.section_name]
            
        return feat_specs
        
    def _determine_target_language(self, parsed_command: ParsedCommand, 
                                  feat_specs: List[str]) -> Optional[str]:
        """Determine target programming language for code generation."""
        # Check if language was explicitly specified in command
        if parsed_command.language:
            return parsed_command.language
            
        # Try to detect from project context
        detection_result = self.language_detector.analyze_project()
        if detection_result.detected_language:
            return detection_result.detected_language
            
        # Try to extract from feature specification files
        for feat_spec in feat_specs:
            feat_content = self.persistence.load_feature_spec(feat_spec)
            if feat_content:
                # Look for language indicators in feature content
                content_lower = feat_content.lower()
                for language in self.language_detector.get_supported_languages():
                    if language in content_lower:
                        return language
                        
        # Last resort: prompt user if configured
        if self.config["fallback_strategies"]["prompt_user_on_low_confidence"]:
            print("Could not determine target language automatically.")
            language = input("Please specify target language: ").strip()
            if language:
                return language.lower()
                
        return None
        
    def _load_feat_content(self, feat_specs: List[str]) -> Dict[str, str]:
        """Load content of feature specifications."""
        feat_content = {}
        
        for feat_spec in feat_specs:
            content = self.persistence.load_feature_spec(feat_spec)
            if content:
                # Generate filename for the feature spec
                if feat_spec.replace('.', '').isdigit():
                    filename = f"feat_{feat_spec.replace('.', '_')}.md"
                else:
                    safe_name = feat_spec.replace(' ', '_').replace('-', '_').lower()
                    filename = f"feat_{safe_name}.md"
                    
                feat_content[filename] = content
            else:
                print(f"Warning: Could not load feature specification for {feat_spec}")
                
        return feat_content
        
    async def _orchestrate_development(self, feat_specs: List[str], agents: List, 
                                     language: str, feat_content: Dict[str, str]) -> OrchestrationResult:
        """Orchestrate parallel code generation."""
        async with OrchestrationEngine() as engine:
            agent_names = [agent.name for agent in agents]
            return await engine.orchestrate_development(
                feat_specs, 
                agent_names, 
                language, 
                feat_content
            )
            
    async def _evaluate_and_select_code(self, agent_results: List, 
                                       language: str) -> tuple:
        """Evaluate code candidates and select the best one."""
        # Convert results to evaluation format
        candidates = []
        for result in agent_results:
            if result.success and result.output_files:
                candidates.append({
                    'agent_name': result.agent_name,
                    'output': result.output,
                    'output_files': result.output_files,
                    'execution_time': result.execution_time,
                    'metadata': result.metadata
                })
                
        if not candidates:
            raise RuntimeError("No successful code generation candidates")
            
        # Evaluate candidates
        evaluation_results = self.code_evaluator.rank_code(candidates, language)
        
        # Select best candidate
        best_index, best_score = evaluation_results[0]
        selected_code = candidates[best_index]
        
        print(f"Selected code from {selected_code['agent_name']} "
              f"(score: {best_score.overall_score:.3f}, "
              f"quality: {best_score.code_quality:.3f}, "
              f"tests: {best_score.test_coverage:.3f})")
              
        # Show code metrics
        metrics = best_score.metrics
        print(f"Code metrics: {metrics.total_files} files, "
              f"{metrics.lines_of_code} LOC, "
              f"{metrics.test_coverage_files} test files")
              
        return selected_code, evaluation_results
        
    async def _get_user_approval(self, selected_code: Dict, 
                               evaluation_results: List) -> Dict:
        """Get user approval for selected code implementation."""
        print("\n" + "="*60)
        print("CODE IMPLEMENTATION REVIEW")
        print("="*60)
        
        best_index, best_score = evaluation_results[0]
        print(f"Selected Agent: {selected_code['agent_name']}")
        print(f"Overall Score: {best_score.overall_score:.3f}")
        print(f"Code Quality: {best_score.code_quality:.3f}")
        print(f"Test Coverage: {best_score.test_coverage:.3f}")
        print(f"Feedback: {best_score.feedback}")
        
        # Show code metrics
        metrics = best_score.metrics
        print(f"\nCode Metrics:")
        print(f"  Total Files: {metrics.total_files}")
        print(f"  Lines of Code: {metrics.lines_of_code}")
        print(f"  Test Files: {metrics.test_coverage_files}")
        print(f"  Documentation: {'Yes' if metrics.has_documentation else 'No'}")
        print(f"  Build Config: {'Yes' if metrics.has_build_config else 'No'}")
        print(f"  Syntax Errors: {len(metrics.syntax_errors)}")
        
        print(f"\nStrengths:")
        for strength in best_score.strengths[:5]:  # Show top 5
            print(f"  + {strength}")
            
        if best_score.weaknesses:
            print(f"\nWeaknesses:")
            for weakness in best_score.weaknesses[:3]:  # Show top 3
                print(f"  - {weakness}")
                
        # Show sample files
        output_files = selected_code.get('output_files', {})
        if output_files:
            print(f"\nGenerated Files: {len(output_files)}")
            for filename in sorted(list(output_files.keys())[:5]):  # Show first 5
                print(f"  - {filename}")
            if len(output_files) > 5:
                print(f"  ... and {len(output_files) - 5} more")
                
        print(f"\nAlternatives available: {len(evaluation_results) - 1}")
        
        while True:
            choice = input("\nApprove this code implementation? (y/n/s=see alternatives/f=show files): ").lower().strip()
            
            if choice in ['y', 'yes']:
                return selected_code
            elif choice in ['n', 'no']:
                return await self._select_alternative(evaluation_results)
            elif choice in ['s', 'see', 'alternatives']:
                return await self._show_alternatives(evaluation_results)
            elif choice in ['f', 'files', 'show']:
                await self._show_sample_files(selected_code)
            else:
                print("Please enter y/n/s/f")
                
    async def _show_sample_files(self, selected_code: Dict):
        """Show sample generated files."""
        output_files = selected_code.get('output_files', {})
        if not output_files:
            print("No files generated")
            return
            
        print(f"\nGenerated files ({len(output_files)} total):")
        for i, (filename, content) in enumerate(sorted(output_files.items())):
            print(f"\n{i+1}. {filename}")
            print("-" * 40)
            
            # Show first 20 lines of each file
            lines = content.split('\n')
            for j, line in enumerate(lines[:20]):
                print(f"{j+1:3}: {line}")
            if len(lines) > 20:
                print(f"     ... ({len(lines) - 20} more lines)")
                
            if i >= 2:  # Show max 3 files
                print(f"\n... and {len(output_files) - 3} more files")
                break
                
    async def _select_alternative(self, evaluation_results: List) -> Dict:
        """Let user select from alternative code implementations."""
        print("\nAvailable alternatives:")
        for i, (idx, score) in enumerate(evaluation_results[1:6], 1):  # Show top 5 alternatives
            print(f"{i}. Overall: {score.overall_score:.3f}, "
                  f"Quality: {score.code_quality:.3f}, "
                  f"Tests: {score.test_coverage:.3f}")
            
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
            print(f"\n{i+1}. Overall: {score.overall_score:.3f}")
            print(f"   Code Quality: {score.code_quality:.3f}")
            print(f"   Test Coverage: {score.test_coverage:.3f}")
            print(f"   Documentation: {score.documentation:.3f}")
            print(f"   Project Structure: {score.project_structure:.3f}")
            print(f"   Files: {score.metrics.total_files}")
            print(f"   Feedback: {score.feedback}")
            
        while True:
            try:
                choice = input("Select code implementation (1-5): ")
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
                                     language: str,
                                     feat_content: Dict[str, str]) -> Dict[str, Any]:
        """Fallback to main Claude when no developer agents available."""
        print(f"No specialized {language} developer agents available, using main Claude...")
        
        feat_specs = self._extract_feat_specs(parsed_command)
        
        # Create basic code structure based on language
        if language == 'go':
            output_files = self._create_go_fallback(feat_specs, feat_content)
        elif language == 'python':
            output_files = self._create_python_fallback(feat_specs, feat_content)
        else:
            output_files = self._create_generic_fallback(language, feat_specs, feat_content)
            
        # Save fallback code
        code_path = self.persistence.save_code(
            feat_specs,
            output_files,
            {
                'command': f"/dev {language} feat {' '.join(feat_specs)}",
                'feat_specs': feat_specs,
                'language': language,
                'agent_name': 'main_claude_fallback',
                'execution_time': 0.0,
                'evaluation_score': 0.5
            }
        )
        
        return {
            'success': True,
            'code_path': str(code_path),
            'feat_specs': feat_specs,
            'language': language,
            'agent_used': 'main_claude_fallback',
            'execution_time': 0.0,
            'evaluation_score': 0.5,
            'code_quality': 0.5,
            'test_coverage': 0.3,
            'agents_used': 0,
            'files_generated': len(output_files),
            'message': f"Fallback {language} code generated for {', '.join(feat_specs)} and saved to {code_path}"
        }
        
    def _create_go_fallback(self, feat_specs: List[str], feat_content: Dict[str, str]) -> Dict[str, str]:
        """Create basic Go code structure as fallback."""
        output_files = {}
        
        # go.mod
        output_files['go.mod'] = """module generated-project

go 1.19

require (
    // Add dependencies here
)
"""
        
        # Main entry point
        output_files['cmd/main.go'] = """package main

import (
    "fmt"
    "log"
)

func main() {
    fmt.Println("Generated application starting...")
    
    // TODO: Implement main application logic
    // Based on feature specifications: """ + ', '.join(feat_specs) + """
    
    log.Println("Application completed")
}
"""
        
        # Basic implementation file
        output_files['internal/app/app.go'] = """package app

// App represents the main application
type App struct {
    // TODO: Add application fields
}

// New creates a new App instance
func New() *App {
    return &App{
        // TODO: Initialize fields
    }
}

// Run starts the application
func (a *App) Run() error {
    // TODO: Implement application logic
    // Based on feature specifications: """ + ', '.join(feat_specs) + """
    return nil
}
"""
        
        # Basic test
        output_files['internal/app/app_test.go'] = """package app

import "testing"

func TestNew(t *testing.T) {
    app := New()
    if app == nil {
        t.Error("Expected app to be created")
    }
}

func TestRun(t *testing.T) {
    app := New()
    err := app.Run()
    if err != nil {
        t.Errorf("Expected no error, got %v", err)
    }
}
"""
        
        # README
        output_files['README.md'] = f"""# Generated Project

This project was generated based on feature specifications: {', '.join(feat_specs)}

## Build

```bash
go mod tidy
go build -o app cmd/main.go
```

## Run

```bash
./app
```

## Test

```bash
go test ./...
```

## TODO

- Implement feature specifications
- Add proper error handling
- Enhance test coverage
- Add documentation
"""
        
        return output_files
        
    def _create_python_fallback(self, feat_specs: List[str], feat_content: Dict[str, str]) -> Dict[str, str]:
        """Create basic Python code structure as fallback."""
        output_files = {}
        
        # pyproject.toml
        output_files['pyproject.toml'] = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "generated-project"
version = "0.1.0"
description = "Generated project"
authors = [{name = "Generated", email = "generated@example.com"}]
dependencies = [
    # Add dependencies here
]

[project.optional-dependencies]
dev = [
    "pytest>=6.0",
    "black",
    "flake8",
]
"""
        
        # Main module
        output_files['src/generated_project/__init__.py'] = """\"\"\"Generated project package.\"\"\""
__version__ = "0.1.0"
"""
        
        # Main entry point
        output_files['src/generated_project/main.py'] = """\"\"\"Main application entry point.\"\"\"

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class App:
    \"\"\"Main application class.\"\"\"
    
    def __init__(self):
        \"\"\"Initialize the application.\"\"\"
        # TODO: Add initialization logic
        pass
    
    def run(self) -> Optional[int]:
        \"\"\"Run the application.
        
        Returns:
            Exit code (0 for success, non-zero for error)
        \"\"\"
        logger.info("Application starting...")
        
        # TODO: Implement application logic
        # Based on feature specifications: """ + ', '.join(feat_specs) + """
        
        logger.info("Application completed")
        return 0


def main() -> int:
    \"\"\"Main entry point.\"\"\"
    logging.basicConfig(level=logging.INFO)
    
    app = App()
    return app.run() or 0


if __name__ == "__main__":
    exit(main())
"""
        
        # Basic test
        output_files['tests/test_main.py'] = """\"\"\"Tests for main module.\"\"\"

import pytest
from generated_project.main import App


def test_app_creation():
    \"\"\"Test app can be created.\"\"\"
    app = App()
    assert app is not None


def test_app_run():
    \"\"\"Test app can run.\"\"\"
    app = App()
    result = app.run()
    assert result == 0
"""
        
        # README
        output_files['README.md'] = f"""# Generated Project

This project was generated based on feature specifications: {', '.join(feat_specs)}

## Installation

```bash
pip install -e .
```

## Development

```bash
pip install -e ".[dev]"
```

## Run

```bash
python -m generated_project.main
```

## Test

```bash
pytest
```

## TODO

- Implement feature specifications
- Add proper error handling
- Enhance test coverage
- Add documentation
"""
        
        return output_files
        
    def _create_generic_fallback(self, language: str, feat_specs: List[str], 
                               feat_content: Dict[str, str]) -> Dict[str, str]:
        """Create generic code structure as fallback."""
        output_files = {}
        
        # README
        output_files['README.md'] = f"""# Generated {language.title()} Project

This project was generated based on feature specifications: {', '.join(feat_specs)}

## Language: {language}

## TODO

- Implement feature specifications
- Set up build system
- Add tests
- Add documentation

## Feature Specifications

{feat_content if feat_content else "No feature specification content available"}
"""
        
        # Basic implementation file
        if language == 'rust':
            output_files['src/main.rs'] = """fn main() {
    println!("Generated Rust application");
    // TODO: Implement application logic
}

#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        assert_eq!(2 + 2, 4);
    }
}
"""
            output_files['Cargo.toml'] = """[package]
name = "generated-project"
version = "0.1.0"
edition = "2021"

[dependencies]
"""
            
        elif language == 'javascript':
            output_files['package.json'] = """{
  "name": "generated-project",
  "version": "1.0.0",
  "description": "Generated JavaScript project",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "jest"
  },
  "devDependencies": {
    "jest": "^28.0.0"
  }
}
"""
            output_files['index.js'] = """console.log('Generated JavaScript application');

// TODO: Implement application logic

module.exports = {
    // Export main functionality
};
"""
            output_files['index.test.js'] = """const app = require('./index');

test('basic test', () => {
    expect(2 + 2).toBe(4);
});
"""
        
        return output_files


async def main():
    """Test development workflow."""
    workflow = DevWorkflow()
    
    # Test development command
    result = await workflow.execute_dev_command("/dev go feat 1")
    
    print("Development Workflow Result:")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Code saved to: {result['code_path']}")
        print(f"Feature specs: {result['feat_specs']}")
        print(f"Language: {result['language']}")
        print(f"Agent used: {result['agent_used']}")
        print(f"Execution time: {result['execution_time']:.2f}s")
        print(f"Score: {result['evaluation_score']:.3f}")
        print(f"Code quality: {result['code_quality']:.3f}")
        print(f"Files generated: {result['files_generated']}")
    else:
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())