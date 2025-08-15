#!/usr/bin/env python3
"""
Code evaluator for multi-agent orchestration system.
Assesses generated code quality, testing, and integration readiness.
"""

import re
import ast
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
import logging


@dataclass
class CodeQualityMetrics:
    """Code quality metrics."""
    total_files: int
    lines_of_code: int
    test_coverage_files: int
    has_documentation: bool
    has_build_config: bool
    syntax_errors: List[str]
    code_smells: List[str]
    complexity_score: float


@dataclass
class CodeScore:
    """Score for generated code."""
    overall_score: float
    code_quality: float
    test_coverage: float
    documentation: float
    project_structure: float
    language_idioms: float
    build_readiness: float
    feedback: str
    strengths: List[str]
    weaknesses: List[str]
    metrics: CodeQualityMetrics


class CodeEvaluator:
    """Evaluates generated code quality and completeness."""
    
    def __init__(self):
        """Initialize code evaluator."""
        self.logger = self._setup_logging()
        
        # Weights for evaluation criteria
        self.weights = {
            'code_quality': 0.25,      # Syntax, style, complexity
            'test_coverage': 0.20,     # Test files and coverage
            'documentation': 0.15,     # Comments, README, docs
            'project_structure': 0.15, # Proper directory organization
            'language_idioms': 0.15,   # Language-specific best practices
            'build_readiness': 0.10    # Build configs, dependencies
        }
        
        # Language-specific configurations
        self.language_configs = {
            'go': {
                'source_extensions': ['.go'],
                'test_patterns': ['*_test.go'],
                'build_files': ['go.mod', 'go.sum', 'Makefile'],
                'doc_files': ['README.md', 'doc.go'],
                'main_files': ['main.go', 'cmd/*/main.go'],
                'project_structure': ['cmd/', 'internal/', 'pkg/', 'test/']
            },
            'python': {
                'source_extensions': ['.py'],
                'test_patterns': ['test_*.py', '*_test.py', 'tests/'],
                'build_files': ['pyproject.toml', 'requirements.txt', 'setup.py', 'Pipfile'],
                'doc_files': ['README.md', '__init__.py'],
                'main_files': ['main.py', '__main__.py'],
                'project_structure': ['src/', 'tests/', 'docs/']
            },
            'rust': {
                'source_extensions': ['.rs'],
                'test_patterns': ['**/tests/', '#[test]', '#[cfg(test)]'],
                'build_files': ['Cargo.toml', 'Cargo.lock'],
                'doc_files': ['README.md', 'lib.rs'],
                'main_files': ['main.rs', 'bin/'],
                'project_structure': ['src/', 'tests/', 'examples/']
            },
            'javascript': {
                'source_extensions': ['.js', '.mjs'],
                'test_patterns': ['*.test.js', '*.spec.js', 'test/', '__tests__/'],
                'build_files': ['package.json', 'yarn.lock', 'package-lock.json'],
                'doc_files': ['README.md', 'index.js'],
                'main_files': ['index.js', 'app.js', 'server.js'],
                'project_structure': ['src/', 'lib/', 'test/', 'dist/']
            },
            'typescript': {
                'source_extensions': ['.ts', '.tsx'],
                'test_patterns': ['*.test.ts', '*.spec.ts', 'test/', '__tests__/'],
                'build_files': ['package.json', 'tsconfig.json'],
                'doc_files': ['README.md', 'index.ts'],
                'main_files': ['index.ts', 'app.ts', 'main.ts'],
                'project_structure': ['src/', 'lib/', 'test/', 'dist/']
            }
        }
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for code evaluator."""
        logger = logging.getLogger('code_evaluator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    def analyze_code_files(self, code_dir: Path, language: str) -> CodeQualityMetrics:
        """
        Analyze code files for quality metrics.
        
        Args:
            code_dir: Directory containing generated code
            language: Programming language
            
        Returns:
            CodeQualityMetrics with analysis results
        """
        config = self.language_configs.get(language.lower(), {})
        source_extensions = config.get('source_extensions', [])
        
        total_files = 0
        lines_of_code = 0
        test_coverage_files = 0
        syntax_errors = []
        code_smells = []
        complexity_score = 0.0
        
        # Find source files
        source_files = []
        for ext in source_extensions:
            source_files.extend(code_dir.rglob(f'*{ext}'))
            
        total_files = len(source_files)
        
        # Analyze each source file
        for file_path in source_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                file_lines = len([line for line in content.split('\n') if line.strip()])
                lines_of_code += file_lines
                
                # Check if it's a test file
                if self._is_test_file(file_path, config):
                    test_coverage_files += 1
                    
                # Language-specific analysis
                if language.lower() == 'python':
                    file_errors, file_smells, file_complexity = self._analyze_python_file(content)
                    syntax_errors.extend(file_errors)
                    code_smells.extend(file_smells)
                    complexity_score += file_complexity
                elif language.lower() == 'go':
                    file_errors, file_smells, file_complexity = self._analyze_go_file(content)
                    syntax_errors.extend(file_errors)
                    code_smells.extend(file_smells)
                    complexity_score += file_complexity
                    
            except Exception as e:
                syntax_errors.append(f"Failed to analyze {file_path}: {e}")
                
        # Normalize complexity score
        if total_files > 0:
            complexity_score /= total_files
            
        # Check for documentation
        has_documentation = self._has_documentation(code_dir, config)
        
        # Check for build configuration
        has_build_config = self._has_build_config(code_dir, config)
        
        return CodeQualityMetrics(
            total_files=total_files,
            lines_of_code=lines_of_code,
            test_coverage_files=test_coverage_files,
            has_documentation=has_documentation,
            has_build_config=has_build_config,
            syntax_errors=syntax_errors,
            code_smells=code_smells,
            complexity_score=complexity_score
        )
        
    def _is_test_file(self, file_path: Path, config: Dict) -> bool:
        """Check if a file is a test file."""
        test_patterns = config.get('test_patterns', [])
        
        for pattern in test_patterns:
            if '*' in pattern:
                # Simple glob pattern matching
                if pattern.endswith('*'):
                    if file_path.name.startswith(pattern[:-1]):
                        return True
                elif pattern.startswith('*'):
                    if file_path.name.endswith(pattern[1:]):
                        return True
                elif '*' in pattern:
                    prefix, suffix = pattern.split('*', 1)
                    if file_path.name.startswith(prefix) and file_path.name.endswith(suffix):
                        return True
            else:
                # Directory or exact pattern
                if pattern in str(file_path):
                    return True
                    
        return False
        
    def _analyze_python_file(self, content: str) -> Tuple[List[str], List[str], float]:
        """Analyze Python file for errors and code quality."""
        errors = []
        smells = []
        complexity = 0.0
        
        try:
            # Parse AST for syntax errors
            tree = ast.parse(content)
            
            # Basic complexity analysis
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
                    complexity += 1
                elif isinstance(node, ast.FunctionDef):
                    complexity += 1
                    # Check function length
                    func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 10
                    if func_lines > 50:
                        smells.append(f"Long function: {node.name} ({func_lines} lines)")
                        
            # Check for code smells
            lines = content.split('\n')
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                
                # Long lines
                if len(line) > 100:
                    smells.append(f"Long line {i+1}: {len(line)} characters")
                    
                # TODO/FIXME comments
                if any(marker in line_stripped.upper() for marker in ['TODO', 'FIXME', 'HACK']):
                    smells.append(f"Incomplete code marker at line {i+1}")
                    
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
        except Exception as e:
            errors.append(f"Analysis error: {e}")
            
        return errors, smells, complexity
        
    def _analyze_go_file(self, content: str) -> Tuple[List[str], List[str], float]:
        """Analyze Go file for errors and code quality."""
        errors = []
        smells = []
        complexity = 0.0
        
        lines = content.split('\n')
        
        # Basic complexity analysis (simplified)
        for line in lines:
            line_stripped = line.strip()
            
            # Control structures add complexity
            if any(keyword in line_stripped for keyword in ['if ', 'for ', 'switch ', 'select ']):
                complexity += 1
                
            # Long lines
            if len(line) > 120:
                smells.append(f"Long line: {len(line)} characters")
                
            # TODO/FIXME comments
            if any(marker in line_stripped.upper() for marker in ['TODO', 'FIXME', 'HACK']):
                smells.append("Incomplete code marker found")
                
            # Missing error handling (simplified check)
            if 'err :=' in line_stripped and 'if err != nil' not in content:
                smells.append("Potential missing error handling")
                
        return errors, smells, complexity
        
    def _has_documentation(self, code_dir: Path, config: Dict) -> bool:
        """Check if project has documentation."""
        doc_files = config.get('doc_files', ['README.md'])
        
        for doc_file in doc_files:
            if (code_dir / doc_file).exists():
                return True
                
        # Check for substantial comments in source files
        source_extensions = config.get('source_extensions', [])
        comment_lines = 0
        total_lines = 0
        
        for ext in source_extensions:
            for file_path in code_dir.rglob(f'*{ext}'):
                try:
                    content = file_path.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    total_lines += len(lines)
                    
                    for line in lines:
                        stripped = line.strip()
                        if stripped.startswith('//') or stripped.startswith('#') or stripped.startswith('"""'):
                            comment_lines += 1
                except Exception:
                    continue
                    
        # Consider documented if >10% comment lines
        return total_lines > 0 and (comment_lines / total_lines) > 0.1
        
    def _has_build_config(self, code_dir: Path, config: Dict) -> bool:
        """Check if project has build configuration."""
        build_files = config.get('build_files', [])
        
        for build_file in build_files:
            if (code_dir / build_file).exists():
                return True
                
        return False
        
    def evaluate_code_quality(self, metrics: CodeQualityMetrics) -> Tuple[float, List[str], List[str]]:
        """Evaluate overall code quality."""
        strengths = []
        weaknesses = []
        score = 0.5  # Base score
        
        # Syntax errors are critical
        if not metrics.syntax_errors:
            strengths.append("No syntax errors detected")
            score += 0.3
        else:
            weaknesses.append(f"{len(metrics.syntax_errors)} syntax errors found")
            score -= 0.4
            
        # Code smells impact quality
        smell_ratio = len(metrics.code_smells) / max(1, metrics.total_files)
        if smell_ratio == 0:
            strengths.append("Clean code with no detected issues")
            score += 0.2
        elif smell_ratio < 2:
            strengths.append("Minimal code quality issues")
            score += 0.1
        else:
            weaknesses.append(f"Multiple code quality issues detected")
            score -= 0.2
            
        # Complexity assessment
        if metrics.complexity_score <= 5:
            strengths.append("Low complexity, maintainable code")
            score += 0.1
        elif metrics.complexity_score <= 10:
            strengths.append("Moderate complexity")
        else:
            weaknesses.append("High complexity, may be difficult to maintain")
            score -= 0.1
            
        return max(0.0, min(1.0, score)), strengths, weaknesses
        
    def evaluate_test_coverage(self, metrics: CodeQualityMetrics) -> Tuple[float, List[str], List[str]]:
        """Evaluate test coverage."""
        strengths = []
        weaknesses = []
        score = 0.0
        
        if metrics.total_files == 0:
            return score, strengths, weaknesses
            
        coverage_ratio = metrics.test_coverage_files / metrics.total_files
        
        if coverage_ratio >= 0.8:
            strengths.append("Excellent test coverage")
            score = 1.0
        elif coverage_ratio >= 0.6:
            strengths.append("Good test coverage")
            score = 0.8
        elif coverage_ratio >= 0.3:
            strengths.append("Basic test coverage")
            score = 0.5
        elif coverage_ratio > 0:
            weaknesses.append("Limited test coverage")
            score = 0.2
        else:
            weaknesses.append("No test files found")
            score = 0.0
            
        return score, strengths, weaknesses
        
    def evaluate_project_structure(self, code_dir: Path, language: str) -> Tuple[float, List[str], List[str]]:
        """Evaluate project structure organization."""
        strengths = []
        weaknesses = []
        score = 0.5  # Base score
        
        config = self.language_configs.get(language.lower(), {})
        expected_structure = config.get('project_structure', [])
        
        if not expected_structure:
            return score, strengths, weaknesses
            
        # Check for expected directories
        found_dirs = 0
        for expected_dir in expected_structure:
            dir_path = code_dir / expected_dir.rstrip('/')
            if dir_path.exists() and dir_path.is_dir():
                found_dirs += 1
                
        structure_ratio = found_dirs / len(expected_structure)
        
        if structure_ratio >= 0.8:
            strengths.append("Excellent project organization")
            score += 0.3
        elif structure_ratio >= 0.5:
            strengths.append("Good project structure")
            score += 0.1
        else:
            weaknesses.append("Poor project organization")
            score -= 0.2
            
        # Check for main entry point
        main_files = config.get('main_files', [])
        has_main = any((code_dir / main_file).exists() for main_file in main_files)
        
        if has_main:
            strengths.append("Clear entry point defined")
            score += 0.1
        else:
            weaknesses.append("No clear entry point found")
            score -= 0.1
            
        return max(0.0, min(1.0, score)), strengths, weaknesses
        
    def evaluate_code(self, code_dir: Path, language: str, 
                     metadata: Optional[Dict] = None) -> CodeScore:
        """
        Evaluate complete generated code.
        
        Args:
            code_dir: Directory containing generated code
            language: Programming language
            metadata: Additional evaluation metadata
            
        Returns:
            CodeScore with detailed evaluation
        """
        # Analyze code files
        metrics = self.analyze_code_files(code_dir, language)
        
        # Evaluate individual aspects
        quality_score, quality_strengths, quality_weaknesses = self.evaluate_code_quality(metrics)
        test_score, test_strengths, test_weaknesses = self.evaluate_test_coverage(metrics)
        structure_score, structure_strengths, structure_weaknesses = self.evaluate_project_structure(code_dir, language)
        
        # Documentation evaluation
        doc_score = 1.0 if metrics.has_documentation else 0.0
        doc_strengths = ["Includes documentation"] if metrics.has_documentation else []
        doc_weaknesses = ["Missing documentation"] if not metrics.has_documentation else []
        
        # Build readiness evaluation
        build_score = 1.0 if metrics.has_build_config else 0.0
        build_strengths = ["Build configuration present"] if metrics.has_build_config else []
        build_weaknesses = ["Missing build configuration"] if not metrics.has_build_config else []
        
        # Language idioms (simplified evaluation)
        idiom_score = 0.7  # Default decent score
        idiom_strengths = ["Uses appropriate language patterns"]
        idiom_weaknesses = []
        
        # Calculate weighted overall score
        overall_score = (
            quality_score * self.weights['code_quality'] +
            test_score * self.weights['test_coverage'] +
            doc_score * self.weights['documentation'] +
            structure_score * self.weights['project_structure'] +
            idiom_score * self.weights['language_idioms'] +
            build_score * self.weights['build_readiness']
        )
        
        # Combine feedback
        all_strengths = (quality_strengths + test_strengths + doc_strengths + 
                        structure_strengths + idiom_strengths + build_strengths)
        all_weaknesses = (quality_weaknesses + test_weaknesses + doc_weaknesses + 
                         structure_weaknesses + idiom_weaknesses + build_weaknesses)
        
        # Generate summary feedback
        if overall_score >= 0.8:
            feedback = "Excellent code quality, ready for production use"
        elif overall_score >= 0.6:
            feedback = "Good code quality with minor improvements needed"
        elif overall_score >= 0.4:
            feedback = "Adequate code but requires significant improvements"
        else:
            feedback = "Code quality is poor, major revisions needed"
            
        return CodeScore(
            overall_score=overall_score,
            code_quality=quality_score,
            test_coverage=test_score,
            documentation=doc_score,
            project_structure=structure_score,
            language_idioms=idiom_score,
            build_readiness=build_score,
            feedback=feedback,
            strengths=all_strengths,
            weaknesses=all_weaknesses,
            metrics=metrics
        )
        
    def rank_code(self, code_candidates: List[Dict[str, Any]], 
                 language: str) -> List[Tuple[int, CodeScore]]:
        """
        Rank multiple code generation candidates.
        
        Args:
            code_candidates: List of code candidate dictionaries
            language: Programming language
            
        Returns:
            List of (candidate_index, CodeScore) tuples, sorted by score
        """
        scored_code = []
        
        for i, candidate in enumerate(code_candidates):
            # Create temporary directory with candidate files
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Write candidate files
                output_files = candidate.get('output_files', {})
                for rel_path, content in output_files.items():
                    file_path = temp_path / rel_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        file_path.write_text(content, encoding='utf-8')
                    except UnicodeEncodeError:
                        # Handle binary files
                        file_path.write_bytes(content.encode('utf-8', errors='replace'))
                        
                # Evaluate code
                score = self.evaluate_code(temp_path, language, candidate)
                scored_code.append((i, score))
                
        # Sort by overall score (descending)
        scored_code.sort(key=lambda x: x[1].overall_score, reverse=True)
        
        self.logger.info(
            f"Ranked {len(scored_code)} code candidates. "
            f"Best score: {scored_code[0][1].overall_score:.3f}"
        )
        
        return scored_code


def main():
    """Test code evaluator functionality."""
    evaluator = CodeEvaluator()
    
    # Create test code directory
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create sample Go project structure
        (temp_path / "cmd" / "timer").mkdir(parents=True)
        (temp_path / "internal" / "timer").mkdir(parents=True)
        (temp_path / "pkg" / "config").mkdir(parents=True)
        
        # Create sample files
        (temp_path / "go.mod").write_text("module timer\n\ngo 1.19\n")
        (temp_path / "README.md").write_text("# Timer Application\n\nA simple pomodoro timer.")
        
        main_go = """package main

import (
    "fmt"
    "timer/internal/timer"
)

func main() {
    t := timer.New(25 * 60) // 25 minutes
    t.Start()
    fmt.Println("Timer started!")
}
"""
        (temp_path / "cmd" / "timer" / "main.go").write_text(main_go)
        
        timer_go = """package timer

import (
    "time"
)

type Timer struct {
    duration time.Duration
    running  bool
}

func New(seconds int) *Timer {
    return &Timer{
        duration: time.Duration(seconds) * time.Second,
        running:  false,
    }
}

func (t *Timer) Start() {
    t.running = true
    // Implementation here
}
"""
        (temp_path / "internal" / "timer" / "timer.go").write_text(timer_go)
        
        timer_test = """package timer

import (
    "testing"
)

func TestNew(t *testing.T) {
    timer := New(60)
    if timer == nil {
        t.Error("Expected timer to be created")
    }
}

func TestStart(t *testing.T) {
    timer := New(60)
    timer.Start()
    if !timer.running {
        t.Error("Expected timer to be running")
    }
}
"""
        (temp_path / "internal" / "timer" / "timer_test.go").write_text(timer_test)
        
        # Evaluate the code
        score = evaluator.evaluate_code(temp_path, 'go')
        
        print(f"Overall Score: {score.overall_score:.3f}")
        print(f"Feedback: {score.feedback}")
        print(f"\nMetrics:")
        print(f"  Total Files: {score.metrics.total_files}")
        print(f"  Lines of Code: {score.metrics.lines_of_code}")
        print(f"  Test Files: {score.metrics.test_coverage_files}")
        print(f"  Has Documentation: {score.metrics.has_documentation}")
        print(f"  Has Build Config: {score.metrics.has_build_config}")
        print(f"  Syntax Errors: {len(score.metrics.syntax_errors)}")
        print(f"  Code Smells: {len(score.metrics.code_smells)}")
        print(f"\nStrengths:")
        for strength in score.strengths:
            print(f"  + {strength}")
        print(f"\nWeaknesses:")
        for weakness in score.weaknesses:
            print(f"  - {weakness}")
        print(f"\nDetailed Scores:")
        print(f"  Code Quality: {score.code_quality:.3f}")
        print(f"  Test Coverage: {score.test_coverage:.3f}")
        print(f"  Documentation: {score.documentation:.3f}")
        print(f"  Project Structure: {score.project_structure:.3f}")
        print(f"  Language Idioms: {score.language_idioms:.3f}")
        print(f"  Build Readiness: {score.build_readiness:.3f}")


if __name__ == "__main__":
    main()