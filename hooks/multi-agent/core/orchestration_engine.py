#!/usr/bin/env python3
"""
Orchestration engine for multi-agent coordination and execution.
Manages parallel agent execution, process isolation, and result coordination.
"""

import asyncio
import tempfile
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import signal
import time


@dataclass
class AgentTask:
    """Represents a task to be executed by an agent."""
    agent_name: str
    prompt: str
    task_id: str
    timeout: int = 300  # 5 minutes default
    input_files: Optional[Dict[str, str]] = None  # filename -> content
    expected_outputs: Optional[List[str]] = None


@dataclass
class AgentResult:
    """Result from an agent execution."""
    agent_name: str
    task_id: str
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    output_files: Optional[Dict[str, str]] = None  # filename -> content
    metadata: Optional[Dict] = None


@dataclass
class OrchestrationResult:
    """Result from a complete orchestration session."""
    task_type: str  # 'design', 'feat', 'dev'
    success: bool
    selected_result: Optional[AgentResult] = None
    all_results: Optional[List[AgentResult]] = None
    execution_time: float = 0.0
    metadata: Optional[Dict] = None


class OrchestrationEngine:
    """Manages parallel agent execution and coordination."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize orchestration engine."""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.temp_dir = None
        self.active_processes: Dict[str, asyncio.subprocess.Process] = {}
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load orchestration configuration."""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "orchestration_config.json"
            
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default configuration
            return {
                "orchestration": {
                    "design_parallel_agent_count": 5,
                    "feat_parallel_agent_count": 5,
                    "dev_parallel_agent_count": 5,
                    "execution_timeout_seconds": 300,
                    "minimum_agents_for_orchestration": 3
                },
                "language_detection": {
                    "confidence_threshold": 0.6,
                    "file_scan_depth": 3
                },
                "user_approval": {
                    "user_design_approval": True,
                    "user_feat_approval": False,
                    "user_dev_approval": False
                },
                "fallback_strategies": {
                    "enable_main_claude_fallback": True,
                    "prompt_user_on_low_confidence": True
                }
            }
            
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for orchestration engine."""
        logger = logging.getLogger('orchestration_engine')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.temp_dir = tempfile.mkdtemp(prefix='claude_orchestration_')
        self.logger.info(f"Created temporary directory: {self.temp_dir}")
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
        
    async def cleanup(self):
        """Clean up resources and temporary files."""
        # Terminate any active processes
        for task_id, process in self.active_processes.items():
            if process.returncode is None:
                self.logger.warning(f"Terminating active process for task {task_id}")
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self.logger.warning(f"Force killing process for task {task_id}")
                    process.kill()
                    
        self.active_processes.clear()
        
        # Clean up temporary directory
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
            
    def _create_task_workspace(self, task: AgentTask) -> Path:
        """Create isolated workspace for a task."""
        task_dir = Path(self.temp_dir) / task.task_id
        task_dir.mkdir(exist_ok=True)
        
        # Create input files if provided
        if task.input_files:
            for filename, content in task.input_files.items():
                input_file = task_dir / filename
                input_file.write_text(content, encoding='utf-8')
                
        # Create prompt file
        prompt_file = task_dir / "prompt.txt"
        prompt_file.write_text(task.prompt, encoding='utf-8')
        
        return task_dir
        
    async def _execute_agent_task(self, task: AgentTask) -> AgentResult:
        """
        Execute a single agent task with process isolation.
        
        Args:
            task: AgentTask to execute
            
        Returns:
            AgentResult with execution results
        """
        start_time = time.time()
        task_dir = self._create_task_workspace(task)
        
        try:
            # Prepare claude-code command
            cmd = [
                'claude-code',
                '--agent', task.agent_name
            ]
            
            # Add input file if we have a prompt file
            prompt_file = task_dir / "prompt.txt"
            if prompt_file.exists():
                cmd.extend(['--input', str(prompt_file)])
                
            self.logger.info(f"Executing task {task.task_id} with agent {task.agent_name}")
            self.logger.debug(f"Command: {' '.join(cmd)}")
            
            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=task_dir
            )
            
            self.active_processes[task.task_id] = process
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=task.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(f"Task {task.task_id} timed out after {task.timeout} seconds")
            finally:
                self.active_processes.pop(task.task_id, None)
                
            execution_time = time.time() - start_time
            
            # Collect output files
            output_files = {}
            for file_path in task_dir.rglob('*'):
                if file_path.is_file() and file_path.name != 'prompt.txt':
                    try:
                        rel_path = file_path.relative_to(task_dir)
                        output_files[str(rel_path)] = file_path.read_text(encoding='utf-8')
                    except (UnicodeDecodeError, PermissionError):
                        # Skip binary files or files we can't read
                        pass
                        
            # Determine success
            success = process.returncode == 0
            output = stdout.decode('utf-8', errors='replace') if stdout else ""
            error = stderr.decode('utf-8', errors='replace') if stderr else None
            
            if not success and not error:
                error = f"Process exited with code {process.returncode}"
                
            self.logger.info(
                f"Task {task.task_id} completed in {execution_time:.2f}s: "
                f"{'SUCCESS' if success else 'FAILED'}"
            )
            
            return AgentResult(
                agent_name=task.agent_name,
                task_id=task.task_id,
                success=success,
                output=output,
                error=error,
                execution_time=execution_time,
                output_files=output_files,
                metadata={
                    'return_code': process.returncode,
                    'workspace': str(task_dir)
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Task {task.task_id} failed with exception: {e}")
            
            return AgentResult(
                agent_name=task.agent_name,
                task_id=task.task_id,
                success=False,
                output="",
                error=str(e),
                execution_time=execution_time,
                metadata={'workspace': str(task_dir)}
            )
            
    async def execute_parallel_tasks(self, tasks: List[AgentTask]) -> List[AgentResult]:
        """
        Execute multiple agent tasks in parallel.
        
        Args:
            tasks: List of AgentTask objects to execute
            
        Returns:
            List of AgentResult objects
        """
        if not tasks:
            return []
            
        self.logger.info(f"Starting parallel execution of {len(tasks)} tasks")
        
        # Create tasks for async execution
        async_tasks = [self._execute_agent_task(task) for task in tasks]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*async_tasks, return_exceptions=True)
        
        # Convert exceptions to failed results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Task {tasks[i].task_id} raised exception: {result}")
                final_results.append(AgentResult(
                    agent_name=tasks[i].agent_name,
                    task_id=tasks[i].task_id,
                    success=False,
                    output="",
                    error=str(result),
                    execution_time=0.0
                ))
            else:
                final_results.append(result)
                
        successful_tasks = sum(1 for r in final_results if r.success)
        self.logger.info(
            f"Parallel execution completed: {successful_tasks}/{len(tasks)} successful"
        )
        
        return final_results
        
    async def orchestrate_design(self, prompt: str, agents: List[str], 
                                language: Optional[str] = None) -> OrchestrationResult:
        """
        Orchestrate parallel design generation.
        
        Args:
            prompt: Design prompt
            agents: List of agent names to use
            language: Optional target language
            
        Returns:
            OrchestrationResult with selected design
        """
        start_time = time.time()
        
        # Create tasks for parallel execution
        tasks = []
        for i, agent_name in enumerate(agents):
            task_prompt = f"""Design a {language + ' ' if language else ''}system based on this description:

{prompt}

Provide a comprehensive architectural design document with:
1. System overview and architecture
2. Core components and their responsibilities
3. Data models and interfaces
4. Technology stack and dependencies
5. Implementation considerations

Focus on creating a well-structured, implementable design that follows {language} best practices if specified."""

            tasks.append(AgentTask(
                agent_name=agent_name,
                prompt=task_prompt,
                task_id=f"design_{i}_{int(time.time())}",
                timeout=self.config['orchestration']['execution_timeout_seconds']
            ))
            
        # Execute tasks in parallel
        results = await self.execute_parallel_tasks(tasks)
        
        # For now, select first successful result
        # In production, would use evaluation logic
        selected_result = None
        for result in results:
            if result.success:
                selected_result = result
                break
                
        execution_time = time.time() - start_time
        
        return OrchestrationResult(
            task_type='design',
            success=selected_result is not None,
            selected_result=selected_result,
            all_results=results,
            execution_time=execution_time,
            metadata={
                'language': language,
                'agent_count': len(agents),
                'prompt': prompt
            }
        )
        
    async def orchestrate_feature(self, section_id: str, agents: List[str],
                                 language: Optional[str] = None,
                                 app_md_content: Optional[str] = None) -> OrchestrationResult:
        """
        Orchestrate parallel feature implementation specification.
        
        Args:
            section_id: Section identifier (number or name)
            agents: List of agent names to use
            language: Optional target language
            app_md_content: Content of app.md for context
            
        Returns:
            OrchestrationResult with selected feature specification
        """
        start_time = time.time()
        
        # Create tasks for parallel execution
        tasks = []
        for i, agent_name in enumerate(agents):
            task_prompt = f"""Generate detailed implementation specifications for section {section_id}.

{"Context from app.md:" if app_md_content else ""}
{app_md_content or ""}

Create a comprehensive implementation specification that:
1. Preserves exact subsection structure from the original section
2. Provides detailed implementation guidance
3. Includes specific {language + ' ' if language else ''}code patterns and approaches
4. Specifies data structures, algorithms, and interfaces
5. Addresses error handling and edge cases

Ensure the output maintains structural integrity and follows {language} best practices if specified."""

            input_files = {}
            if app_md_content:
                input_files['app.md'] = app_md_content
                
            tasks.append(AgentTask(
                agent_name=agent_name,
                prompt=task_prompt,
                task_id=f"feat_{section_id}_{i}_{int(time.time())}",
                timeout=self.config['orchestration']['execution_timeout_seconds'],
                input_files=input_files
            ))
            
        # Execute tasks in parallel
        results = await self.execute_parallel_tasks(tasks)
        
        # Select first successful result
        selected_result = None
        for result in results:
            if result.success:
                selected_result = result
                break
                
        execution_time = time.time() - start_time
        
        return OrchestrationResult(
            task_type='feat',
            success=selected_result is not None,
            selected_result=selected_result,
            all_results=results,
            execution_time=execution_time,
            metadata={
                'section_id': section_id,
                'language': language,
                'agent_count': len(agents)
            }
        )
        
    async def orchestrate_development(self, feat_specs: List[str], agents: List[str],
                                    language: str, feat_content: Optional[Dict[str, str]] = None) -> OrchestrationResult:
        """
        Orchestrate parallel code generation from feature specifications.
        
        Args:
            feat_specs: List of feature specification identifiers
            agents: List of agent names to use
            language: Target programming language
            feat_content: Optional feature specification content
            
        Returns:
            OrchestrationResult with selected code implementation
        """
        start_time = time.time()
        
        # Create tasks for parallel execution
        tasks = []
        for i, agent_name in enumerate(agents):
            task_prompt = f"""Generate working {language} code from these feature specifications:

Feature specifications: {', '.join(feat_specs)}

{f"Feature content provided in input files." if feat_content else ""}

Create a complete, working codebase that:
1. Implements all specified features with proper {language} idioms
2. Includes comprehensive test suites
3. Provides proper documentation and comments
4. Uses appropriate project structure for {language}
5. Includes build and deployment configurations

Focus on creating production-ready, well-tested code that follows {language} best practices."""

            input_files = feat_content or {}
                
            tasks.append(AgentTask(
                agent_name=agent_name,
                prompt=task_prompt,
                task_id=f"dev_{i}_{int(time.time())}",
                timeout=self.config['orchestration']['execution_timeout_seconds'],
                input_files=input_files
            ))
            
        # Execute tasks in parallel
        results = await self.execute_parallel_tasks(tasks)
        
        # Select first successful result
        selected_result = None
        for result in results:
            if result.success:
                selected_result = result
                break
                
        execution_time = time.time() - start_time
        
        return OrchestrationResult(
            task_type='dev',
            success=selected_result is not None,
            selected_result=selected_result,
            all_results=results,
            execution_time=execution_time,
            metadata={
                'feat_specs': feat_specs,
                'language': language,
                'agent_count': len(agents)
            }
        )


async def main():
    """Test orchestration engine functionality."""
    async with OrchestrationEngine() as engine:
        # Test simple task execution
        task = AgentTask(
            agent_name="gad",
            prompt="Design a simple timer application",
            task_id="test_task_1"
        )
        
        print("Testing single task execution...")
        result = await engine._execute_agent_task(task)
        print(f"Result: {result.success}, Time: {result.execution_time:.2f}s")
        if result.error:
            print(f"Error: {result.error}")
            

if __name__ == "__main__":
    asyncio.run(main())