#!/usr/bin/env python3
"""
Main orchestration script for multi-agent system.
Provides command-line interface for /design, /feat, and /dev commands.
"""

import sys
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add the multi-agent directory to Python path
MULTI_AGENT_DIR = Path(__file__).parent
sys.path.insert(0, str(MULTI_AGENT_DIR))

# Import workflow classes
from workflows.design_workflow import DesignWorkflow
from workflows.feat_workflow import FeatWorkflow
from workflows.dev_workflow import DevWorkflow
from utils.validation import Validator
from utils.file_manager import get_file_manager, cleanup_global_file_manager


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger('orchestrate')


async def execute_design_command(command_line: str) -> int:
    """Execute /design command."""
    try:
        workflow = DesignWorkflow()
        result = await workflow.execute_design_command(command_line)
        
        if result['success']:
            print(f"✓ {result['message']}")
            print(f"  Design saved to: {result['design_path']}")
            print(f"  Agent used: {result['agent_used']}")
            print(f"  Language: {result.get('language', 'auto-detected')}")
            print(f"  Execution time: {result['execution_time']:.2f}s")
            print(f"  Quality score: {result['evaluation_score']:.3f}")
            return 0
        else:
            print(f"✗ {result['message']}")
            if 'error' in result:
                print(f"  Error: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"✗ Design command failed: {e}")
        return 1


async def execute_feat_command(command_line: str) -> int:
    """Execute /feat command."""
    try:
        workflow = FeatWorkflow()
        result = await workflow.execute_feat_command(command_line)
        
        if result['success']:
            print(f"✓ {result['message']}")
            print(f"  Feature spec saved to: {result['feat_path']}")
            print(f"  Section ID: {result['section_id']}")
            print(f"  Agent used: {result['agent_used']}")
            print(f"  Language: {result.get('language', 'auto-detected')}")
            print(f"  Execution time: {result['execution_time']:.2f}s")
            print(f"  Quality score: {result['evaluation_score']:.3f}")
            print(f"  Structural score: {result['structural_score']:.3f}")
            return 0
        else:
            print(f"✗ {result['message']}")
            if 'error' in result:
                print(f"  Error: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"✗ Feature command failed: {e}")
        return 1


async def execute_dev_command(command_line: str) -> int:
    """Execute /dev command."""
    try:
        workflow = DevWorkflow()
        result = await workflow.execute_dev_command(command_line)
        
        if result['success']:
            print(f"✓ {result['message']}")
            print(f"  Code saved to: {result['code_path']}")
            print(f"  Feature specs: {', '.join(result['feat_specs'])}")
            print(f"  Language: {result['language']}")
            print(f"  Agent used: {result['agent_used']}")
            print(f"  Execution time: {result['execution_time']:.2f}s")
            print(f"  Quality score: {result['evaluation_score']:.3f}")
            print(f"  Code quality: {result['code_quality']:.3f}")
            print(f"  Files generated: {result['files_generated']}")
            return 0
        else:
            print(f"✗ {result['message']}")
            if 'error' in result:
                print(f"  Error: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"✗ Development command failed: {e}")
        return 1


def validate_command_line(command_line: str) -> bool:
    """Validate command line syntax."""
    validator = Validator()
    result = validator.validate_command_syntax(command_line)
    
    if not result.is_valid:
        print(f"✗ Invalid command: {result.message}")
        return False
        
    return True


def print_help():
    """Print help information."""
    print("""
Multi-Agent Orchestration System

USAGE:
    orchestrate.py [OPTIONS] COMMAND

COMMANDS:
    design [language] <description>     Generate system architecture
    feat <section_id>                   Generate feature implementation spec  
    dev [language] feat <section_id>    Generate working code

EXAMPLES:
    orchestrate.py design go pomodoro timer
    orchestrate.py feat 1
    orchestrate.py dev go feat timer-core

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose          Enable verbose logging
    --log-level LEVEL      Set logging level (DEBUG, INFO, WARNING, ERROR)

WORKFLOW:
    1. /design   - Create high-level architecture (app.md)
    2. /feat N   - Generate detailed implementation specs (feat_N.md)  
    3. /dev feat N - Generate working code from specifications

For detailed command documentation, see:
    - /home/aural/.claude/commands/design.md
    - /home/aural/.claude/commands/feat.md
    - /home/aural/.claude/commands/dev.md
""")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Orchestration System",
        add_help=False  # We'll handle help ourselves
    )
    
    parser.add_argument('command', nargs='*', help='Command to execute')
    parser.add_argument('-h', '--help', action='store_true', help='Show help')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--log-level', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Set logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else args.log_level
    logger = setup_logging(log_level)
    
    # Show help
    if args.help or not args.command:
        print_help()
        return 0
        
    # Reconstruct command line
    command_line = ' '.join(args.command)
    
    # Add leading slash if not present
    if not command_line.startswith('/'):
        command_line = '/' + command_line
        
    logger.info(f"Executing command: {command_line}")
    
    # Validate command
    if not validate_command_line(command_line):
        return 1
        
    try:
        # Determine command type
        command_parts = command_line[1:].split()  # Remove leading slash
        command_type = command_parts[0].lower()
        
        # Execute appropriate workflow
        if command_type == 'design':
            return await execute_design_command(command_line)
        elif command_type == 'feat':
            return await execute_feat_command(command_line)
        elif command_type == 'dev':
            return await execute_dev_command(command_line)
        else:
            print(f"✗ Unknown command type: {command_type}")
            print("  Valid commands: design, feat, dev")
            return 1
            
    except KeyboardInterrupt:
        print("\n✗ Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        print(f"✗ Orchestration failed: {e}")
        return 1
    finally:
        # Cleanup
        cleanup_global_file_manager()


if __name__ == "__main__":
    # Run the async main function
    sys.exit(asyncio.run(main()))