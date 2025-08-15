#!/usr/bin/env python3
"""
Command parser for multi-agent orchestration system.
Parses user input and determines execution strategy for /design, /feat, and /dev commands.
"""

import re
import argparse
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParsedCommand:
    """Represents a parsed command with its arguments."""
    command_type: str  # 'design', 'feat', 'dev'
    language: Optional[str] = None
    description: Optional[str] = None
    section_number: Optional[str] = None
    section_name: Optional[str] = None
    multiple_sections: Optional[List[str]] = None
    target_spec: Optional[str] = None  # For /dev command (e.g., 'feat')


class CommandParser:
    """Parses and validates multi-agent orchestration commands."""
    
    def __init__(self):
        self.supported_languages = [
            'go', 'python', 'rust', 'javascript', 'typescript', 
            'java', 'csharp', 'cpp', 'c'
        ]
        
    def parse_design_command(self, args: List[str]) -> ParsedCommand:
        """
        Parse /design command.
        
        Examples:
        - /design go pomodoro timer
        - /design pomodoro timer
        - /design microservice-architecture
        """
        if not args:
            raise ValueError("Design command requires a description")
            
        # Check if first argument is a language
        language = None
        description_start = 0
        
        if args[0].lower() in self.supported_languages:
            language = args[0].lower()
            description_start = 1
            
        if description_start >= len(args):
            raise ValueError("Design command requires a description after language")
            
        description = ' '.join(args[description_start:])
        
        return ParsedCommand(
            command_type='design',
            language=language,
            description=description
        )
        
    def parse_feat_command(self, args: List[str]) -> ParsedCommand:
        """
        Parse /feat command.
        
        Examples:
        - /feat 1
        - /feat timer-core
        - /feat 2.3
        """
        if not args:
            raise ValueError("Feat command requires a section identifier")
            
        section_identifier = args[0]
        
        # Check if it's a number (e.g., "1", "2.3")
        if re.match(r'^\d+(\.\d+)?$', section_identifier):
            return ParsedCommand(
                command_type='feat',
                section_number=section_identifier
            )
        else:
            # It's a section name
            return ParsedCommand(
                command_type='feat',
                section_name=section_identifier
            )
            
    def parse_dev_command(self, args: List[str]) -> ParsedCommand:
        """
        Parse /dev command.
        
        Examples:
        - /dev feat 1
        - /dev go feat timer-core
        - /dev feat 1,3,5
        """
        if not args:
            raise ValueError("Dev command requires arguments")
            
        language = None
        args_start = 0
        
        # Check if first argument is a language
        if args[0].lower() in self.supported_languages:
            language = args[0].lower()
            args_start = 1
            
        if args_start >= len(args):
            raise ValueError("Dev command requires target specification")
            
        remaining_args = args[args_start:]
        
        # Expect 'feat' keyword
        if remaining_args[0] != 'feat':
            raise ValueError("Dev command currently only supports 'feat' target")
            
        if len(remaining_args) < 2:
            raise ValueError("Dev command requires section identifier after 'feat'")
            
        section_spec = remaining_args[1]
        
        # Check for multiple sections (comma-separated)
        if ',' in section_spec:
            multiple_sections = [s.strip() for s in section_spec.split(',')]
            return ParsedCommand(
                command_type='dev',
                language=language,
                target_spec='feat',
                multiple_sections=multiple_sections
            )
        else:
            # Single section
            if re.match(r'^\d+(\.\d+)?$', section_spec):
                return ParsedCommand(
                    command_type='dev',
                    language=language,
                    target_spec='feat',
                    section_number=section_spec
                )
            else:
                return ParsedCommand(
                    command_type='dev',
                    language=language,
                    target_spec='feat',
                    section_name=section_spec
                )
                
    def parse_command(self, command_line: str) -> ParsedCommand:
        """
        Parse a complete command line.
        
        Args:
            command_line: Full command string (e.g., "/design go pomodoro timer")
            
        Returns:
            ParsedCommand object with parsed arguments
        """
        # Remove leading slash if present
        if command_line.startswith('/'):
            command_line = command_line[1:]
            
        parts = command_line.split()
        if not parts:
            raise ValueError("Empty command")
            
        command_type = parts[0].lower()
        args = parts[1:]
        
        if command_type == 'design':
            return self.parse_design_command(args)
        elif command_type == 'feat':
            return self.parse_feat_command(args)
        elif command_type == 'dev':
            return self.parse_dev_command(args)
        else:
            raise ValueError(f"Unknown command type: {command_type}")
            
    def validate_command(self, parsed_command: ParsedCommand) -> bool:
        """
        Validate a parsed command for consistency and completeness.
        
        Args:
            parsed_command: ParsedCommand to validate
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        if parsed_command.command_type == 'design':
            if not parsed_command.description:
                raise ValueError("Design command requires a description")
                
        elif parsed_command.command_type == 'feat':
            if not parsed_command.section_number and not parsed_command.section_name:
                raise ValueError("Feat command requires section identifier")
                
        elif parsed_command.command_type == 'dev':
            if not parsed_command.target_spec:
                raise ValueError("Dev command requires target specification")
            if parsed_command.target_spec == 'feat':
                if (not parsed_command.section_number and 
                    not parsed_command.section_name and 
                    not parsed_command.multiple_sections):
                    raise ValueError("Dev feat command requires section identifier")
                    
        return True
        
    def get_help_text(self, command_type: Optional[str] = None) -> str:
        """Get help text for commands."""
        if command_type == 'design':
            return """
/design command usage:
  /design [language] <description>
  
Examples:
  /design go pomodoro timer          # Language-specific (uses gad)
  /design pomodoro timer             # Auto-detect language
  /design microservice-architecture  # Multi-service design
"""
        elif command_type == 'feat':
            return """
/feat command usage:
  /feat <section_identifier>
  
Examples:
  /feat 1            # Implement section 1 from app.md
  /feat timer-core   # Implement named section
  /feat 2.3          # Implement specific subsection
"""
        elif command_type == 'dev':
            return """
/dev command usage:
  /dev [language] feat <section_identifier>
  
Examples:
  /dev feat 1                # Generate code for feat_1_*.md
  /dev go feat timer-core    # Language-specific generation
  /dev feat 1,3,5           # Multiple specifications
"""
        else:
            return """
Multi-agent orchestration commands:

/design [language] <description>
  Generate high-level system architecture

/feat <section_identifier>
  Transform architecture sections into detailed implementation specifications

/dev [language] feat <section_identifier>
  Generate working source code from feature specifications

Use /help <command> for specific command details.
"""


def main():
    """Test the command parser with example inputs."""
    parser = CommandParser()
    
    test_commands = [
        "/design go pomodoro timer",
        "/design pomodoro timer",
        "/feat 1",
        "/feat timer-core",
        "/feat 2.3",
        "/dev feat 1",
        "/dev go feat timer-core",
        "/dev feat 1,3,5"
    ]
    
    for cmd in test_commands:
        try:
            parsed = parser.parse_command(cmd)
            parser.validate_command(parsed)
            print(f"✓ {cmd} -> {parsed}")
        except ValueError as e:
            print(f"✗ {cmd} -> ERROR: {e}")


if __name__ == "__main__":
    main()