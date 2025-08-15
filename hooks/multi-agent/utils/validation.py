#!/usr/bin/env python3
"""
Validation utility for multi-agent orchestration system.
Provides input and output validation functions for commands, content, and results.
"""

import re
import json
import ast
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging


class ValidationLevel(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    level: ValidationLevel
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class ValidationSummary:
    """Summary of multiple validation results."""
    is_valid: bool
    results: List[ValidationResult]
    error_count: int
    warning_count: int
    info_count: int


class Validator:
    """Main validation class for multi-agent orchestration."""
    
    def __init__(self):
        """Initialize validator."""
        self.logger = self._setup_logging()
        
        # Supported programming languages
        self.supported_languages = {
            'go', 'python', 'rust', 'javascript', 'typescript', 
            'java', 'csharp', 'cpp', 'c', 'ruby', 'php', 'swift'
        }
        
        # File extension mappings
        self.language_extensions = {
            'go': ['.go'],
            'python': ['.py'],
            'rust': ['.rs'],
            'javascript': ['.js', '.mjs'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'csharp': ['.cs'],
            'cpp': ['.cpp', '.cxx', '.cc'],
            'c': ['.c', '.h'],
            'ruby': ['.rb'],
            'php': ['.php'],
            'swift': ['.swift']
        }
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for validator."""
        logger = logging.getLogger('validator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    def validate_command_syntax(self, command_line: str) -> ValidationResult:
        """
        Validate command syntax.
        
        Args:
            command_line: Command string to validate
            
        Returns:
            ValidationResult
        """
        if not command_line or not command_line.strip():
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Command cannot be empty",
                field="command_line"
            )
            
        # Remove leading slash
        if command_line.startswith('/'):
            command_line = command_line[1:]
            
        parts = command_line.split()
        if not parts:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Command cannot be empty",
                field="command_line"
            )
            
        command_type = parts[0].lower()
        valid_commands = {'design', 'feat', 'dev'}
        
        if command_type not in valid_commands:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Invalid command type: {command_type}. Valid commands: {', '.join(valid_commands)}",
                field="command_type"
            )
            
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message="Command syntax is valid",
            field="command_line"
        )
        
    def validate_language(self, language: str) -> ValidationResult:
        """
        Validate programming language.
        
        Args:
            language: Programming language to validate
            
        Returns:
            ValidationResult
        """
        if not language:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Language cannot be empty",
                field="language"
            )
            
        language_lower = language.lower().strip()
        
        if language_lower not in self.supported_languages:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Unsupported language: {language}. Supported: {', '.join(sorted(self.supported_languages))}",
                field="language",
                details={"suggested_languages": list(self.supported_languages)}
            )
            
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message=f"Language '{language_lower}' is supported",
            field="language"
        )
        
    def validate_section_identifier(self, section_id: str) -> ValidationResult:
        """
        Validate section identifier for /feat commands.
        
        Args:
            section_id: Section identifier to validate
            
        Returns:
            ValidationResult
        """
        if not section_id:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Section identifier cannot be empty",
                field="section_id"
            )
            
        # Check for numeric section (e.g., "1", "2.3", "1.2.3")
        if re.match(r'^\d+(\.\d+)*$', section_id):
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message=f"Valid numeric section identifier: {section_id}",
                field="section_id"
            )
            
        # Check for named section (alphanumeric with hyphens/underscores)
        if re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', section_id):
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message=f"Valid named section identifier: {section_id}",
                field="section_id"
            )
            
        return ValidationResult(
            is_valid=False,
            level=ValidationLevel.ERROR,
            message=f"Invalid section identifier: {section_id}. Use numeric (1, 2.3) or named (timer-core) format",
            field="section_id"
        )
        
    def validate_agent_name(self, agent_name: str) -> ValidationResult:
        """
        Validate agent name.
        
        Args:
            agent_name: Agent name to validate
            
        Returns:
            ValidationResult
        """
        if not agent_name:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Agent name cannot be empty",
                field="agent_name"
            )
            
        # Check for valid agent name format
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', agent_name):
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Invalid agent name format: {agent_name}. Use alphanumeric characters, hyphens, and underscores only",
                field="agent_name"
            )
            
        # Check length
        if len(agent_name) > 50:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Agent name too long: {len(agent_name)} characters. Maximum 50 characters",
                field="agent_name"
            )
            
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message=f"Valid agent name: {agent_name}",
            field="agent_name"
        )
        
    def validate_markdown_content(self, content: str) -> ValidationResult:
        """
        Validate markdown content structure.
        
        Args:
            content: Markdown content to validate
            
        Returns:
            ValidationResult
        """
        if not content or not content.strip():
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Content cannot be empty",
                field="content"
            )
            
        lines = content.split('\n')
        issues = []
        
        # Check for headers
        header_count = sum(1 for line in lines if line.strip().startswith('#'))
        if header_count == 0:
            issues.append("No headers found - consider adding section headers")
            
        # Check for very short content
        word_count = len(content.split())
        if word_count < 50:
            issues.append(f"Content is very short ({word_count} words) - consider adding more detail")
            
        # Check for incomplete sections
        if any(marker in content.upper() for marker in ['TODO', 'TBD', 'FIXME']):
            issues.append("Content contains incomplete sections (TODO/TBD/FIXME)")
            
        # Check for proper markdown structure
        code_blocks = content.count('```')
        if code_blocks % 2 != 0:
            issues.append("Unmatched code block markers (```)")
            
        if issues:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message=f"Content has {len(issues)} issues",
                field="content",
                details={"issues": issues}
            )
            
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message="Content structure is valid",
            field="content"
        )
        
    def validate_code_content(self, content: str, language: str) -> ValidationResult:
        """
        Validate code content for basic syntax.
        
        Args:
            content: Code content to validate
            language: Programming language
            
        Returns:
            ValidationResult
        """
        if not content or not content.strip():
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Code content cannot be empty",
                field="content"
            )
            
        if language.lower() == 'python':
            return self._validate_python_syntax(content)
        elif language.lower() == 'go':
            return self._validate_go_syntax(content)
        elif language.lower() == 'javascript':
            return self._validate_javascript_syntax(content)
        else:
            # Generic validation for other languages
            return self._validate_generic_code(content, language)
            
    def _validate_python_syntax(self, content: str) -> ValidationResult:
        """Validate Python syntax."""
        try:
            ast.parse(content)
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message="Python syntax is valid",
                field="python_syntax"
            )
        except SyntaxError as e:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Python syntax error: {e}",
                field="python_syntax",
                details={"line": e.lineno, "offset": e.offset}
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Python validation error: {e}",
                field="python_syntax"
            )
            
    def _validate_go_syntax(self, content: str) -> ValidationResult:
        """Basic Go syntax validation."""
        issues = []
        
        # Check for package declaration
        if not re.search(r'^package\s+\w+', content, re.MULTILINE):
            issues.append("Missing package declaration")
            
        # Check for unmatched braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            issues.append(f"Unmatched braces: {open_braces} open, {close_braces} close")
            
        # Check for unmatched parentheses
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens != close_parens:
            issues.append(f"Unmatched parentheses: {open_parens} open, {close_parens} close")
            
        if issues:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Go syntax issues: {'; '.join(issues)}",
                field="go_syntax",
                details={"issues": issues}
            )
            
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message="Go syntax appears valid",
            field="go_syntax"
        )
        
    def _validate_javascript_syntax(self, content: str) -> ValidationResult:
        """Basic JavaScript syntax validation."""
        issues = []
        
        # Check for unmatched braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            issues.append(f"Unmatched braces: {open_braces} open, {close_braces} close")
            
        # Check for unmatched parentheses
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens != close_parens:
            issues.append(f"Unmatched parentheses: {open_parens} open, {close_parens} close")
            
        # Check for unmatched brackets
        open_brackets = content.count('[')
        close_brackets = content.count(']')
        if open_brackets != close_brackets:
            issues.append(f"Unmatched brackets: {open_brackets} open, {close_brackets} close")
            
        if issues:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message=f"JavaScript syntax issues: {'; '.join(issues)}",
                field="javascript_syntax",
                details={"issues": issues}
            )
            
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message="JavaScript syntax appears valid",
            field="javascript_syntax"
        )
        
    def _validate_generic_code(self, content: str, language: str) -> ValidationResult:
        """Generic code validation."""
        issues = []
        
        # Check for very short code
        if len(content.strip()) < 10:
            issues.append("Code content is very short")
            
        # Check for incomplete markers
        if any(marker in content.upper() for marker in ['TODO', 'FIXME', 'HACK']):
            issues.append("Code contains incomplete markers")
            
        if issues:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message=f"{language} code issues: {'; '.join(issues)}",
                field="code_content",
                details={"issues": issues}
            )
            
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message=f"{language} code appears valid",
            field="code_content"
        )
        
    def validate_file_structure(self, files: Dict[str, str], language: str) -> ValidationResult:
        """
        Validate generated file structure.
        
        Args:
            files: Dictionary of filename -> content
            language: Programming language
            
        Returns:
            ValidationResult
        """
        if not files:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="No files generated",
                field="file_structure"
            )
            
        issues = []
        
        # Get expected extensions for language
        expected_extensions = self.language_extensions.get(language.lower(), [])
        
        # Check for source files
        source_files = [f for f in files.keys() 
                       if any(f.endswith(ext) for ext in expected_extensions)]
        
        if not source_files:
            issues.append(f"No {language} source files found")
            
        # Check for test files
        test_files = [f for f in files.keys() 
                     if 'test' in f.lower() or '_test.' in f or '.test.' in f]
        
        if not test_files:
            issues.append("No test files found")
            
        # Check for documentation
        doc_files = [f for f in files.keys() 
                    if f.lower() in ['readme.md', 'readme.txt', 'readme.rst']]
        
        if not doc_files:
            issues.append("No README documentation found")
            
        # Language-specific structure validation
        if language.lower() == 'go':
            has_go_mod = any(f == 'go.mod' for f in files.keys())
            if not has_go_mod:
                issues.append("No go.mod file found")
                
        elif language.lower() == 'python':
            has_pyproject = any(f.endswith('pyproject.toml') for f in files.keys())
            has_setup = any(f.endswith('setup.py') for f in files.keys())
            has_requirements = any(f.endswith('requirements.txt') for f in files.keys())
            
            if not (has_pyproject or has_setup or has_requirements):
                issues.append("No Python package configuration found")
                
        if issues:
            level = ValidationLevel.WARNING if len(issues) <= 2 else ValidationLevel.ERROR
            return ValidationResult(
                is_valid=level != ValidationLevel.ERROR,
                level=level,
                message=f"File structure issues: {'; '.join(issues)}",
                field="file_structure",
                details={"issues": issues, "file_count": len(files)}
            )
            
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message=f"File structure is valid ({len(files)} files)",
            field="file_structure",
            details={"file_count": len(files), "source_files": len(source_files)}
        )
        
    def validate_json_content(self, content: str) -> ValidationResult:
        """
        Validate JSON content.
        
        Args:
            content: JSON content to validate
            
        Returns:
            ValidationResult
        """
        try:
            json.loads(content)
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message="JSON content is valid",
                field="json_content"
            )
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Invalid JSON: {e}",
                field="json_content",
                details={"line": e.lineno, "column": e.colno}
            )
            
    def validate_multiple(self, validations: List[Tuple[str, Any, str]]) -> ValidationSummary:
        """
        Run multiple validations and return summary.
        
        Args:
            validations: List of (validation_type, value, context) tuples
            
        Returns:
            ValidationSummary
        """
        results = []
        
        for validation_type, value, context in validations:
            if validation_type == 'command':
                result = self.validate_command_syntax(value)
            elif validation_type == 'language':
                result = self.validate_language(value)
            elif validation_type == 'section_id':
                result = self.validate_section_identifier(value)
            elif validation_type == 'agent_name':
                result = self.validate_agent_name(value)
            elif validation_type == 'markdown':
                result = self.validate_markdown_content(value)
            elif validation_type == 'code':
                result = self.validate_code_content(value, context)
            elif validation_type == 'file_structure':
                result = self.validate_file_structure(value, context)
            elif validation_type == 'json':
                result = self.validate_json_content(value)
            else:
                result = ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message=f"Unknown validation type: {validation_type}",
                    field="validation_type"
                )
                
            results.append(result)
            
        # Count by level
        error_count = sum(1 for r in results if r.level == ValidationLevel.ERROR)
        warning_count = sum(1 for r in results if r.level == ValidationLevel.WARNING)
        info_count = sum(1 for r in results if r.level == ValidationLevel.INFO)
        
        # Overall validity
        is_valid = error_count == 0
        
        return ValidationSummary(
            is_valid=is_valid,
            results=results,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count
        )


def main():
    """Test validation functionality."""
    validator = Validator()
    
    print("Testing validator...")
    
    # Test command validation
    commands = [
        "/design go pomodoro timer",
        "/feat 1",
        "/dev go feat timer-core",
        "/invalid command",
        ""
    ]
    
    for cmd in commands:
        result = validator.validate_command_syntax(cmd)
        print(f"Command '{cmd}': {'✓' if result.is_valid else '✗'} {result.message}")
        
    # Test language validation
    languages = ["go", "python", "invalid_lang", ""]
    for lang in languages:
        result = validator.validate_language(lang)
        print(f"Language '{lang}': {'✓' if result.is_valid else '✗'} {result.message}")
        
    # Test multiple validations
    validations = [
        ('command', '/design go timer', ''),
        ('language', 'go', ''),
        ('section_id', '1.2.3', ''),
        ('agent_name', 'gad', ''),
        ('markdown', '# Test\n\nThis is a test.', ''),
    ]
    
    summary = validator.validate_multiple(validations)
    print(f"\nMultiple validation summary:")
    print(f"  Valid: {summary.is_valid}")
    print(f"  Errors: {summary.error_count}")
    print(f"  Warnings: {summary.warning_count}")
    print(f"  Info: {summary.info_count}")
    
    for result in summary.results:
        print(f"  {result.field}: {'✓' if result.is_valid else '✗'} {result.message}")


if __name__ == "__main__":
    main()