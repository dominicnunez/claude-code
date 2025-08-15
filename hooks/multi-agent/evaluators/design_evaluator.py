#!/usr/bin/env python3
"""
Design evaluator for multi-agent orchestration system.
Assesses and ranks architectural design candidates using weighted criteria.
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import logging


@dataclass
class EvaluationCriteria:
    """Evaluation criteria with weights."""
    language_idioms: float = 0.25      # Adherence to language conventions
    architecture: float = 0.25         # Technical correctness and scalability
    implementability: float = 0.20     # Practical implementation feasibility
    completeness: float = 0.15         # Thoroughness of coverage
    innovation: float = 0.10           # Creative and elegant solutions
    documentation: float = 0.05        # Clarity and comprehensiveness


@dataclass
class DesignScore:
    """Score for a design candidate."""
    overall_score: float
    language_idioms: float
    architecture: float
    implementability: float
    completeness: float
    innovation: float
    documentation: float
    feedback: str
    strengths: List[str]
    weaknesses: List[str]


class DesignEvaluator:
    """Evaluates architectural design quality using weighted criteria."""
    
    def __init__(self, criteria: Optional[EvaluationCriteria] = None):
        """Initialize design evaluator."""
        self.criteria = criteria or EvaluationCriteria()
        self.logger = self._setup_logging()
        
        # Language-specific architectural patterns
        self.language_patterns = {
            'go': {
                'patterns': ['interface', 'struct', 'goroutine', 'channel', 'package'],
                'anti_patterns': ['inheritance', 'class', 'exception'],
                'best_practices': ['composition', 'small interfaces', 'error handling', 'concurrency']
            },
            'python': {
                'patterns': ['class', 'decorator', 'context manager', 'generator', 'async/await'],
                'anti_patterns': ['global variables', 'deep inheritance'],
                'best_practices': ['PEP 8', 'type hints', 'virtual environments', 'docstrings']
            },
            'rust': {
                'patterns': ['ownership', 'borrowing', 'trait', 'enum', 'match'],
                'anti_patterns': ['unsafe blocks without justification', 'clone() overuse'],
                'best_practices': ['zero-cost abstractions', 'memory safety', 'error handling']
            },
            'javascript': {
                'patterns': ['promise', 'async/await', 'closure', 'prototype', 'module'],
                'anti_patterns': ['global pollution', 'callback hell', 'var usage'],
                'best_practices': ['ES6+', 'immutability', 'functional programming', 'testing']
            }
        }
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for design evaluator."""
        logger = logging.getLogger('design_evaluator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    def evaluate_language_idioms(self, design_content: str, 
                                language: Optional[str] = None) -> Tuple[float, List[str], List[str]]:
        """
        Evaluate adherence to language conventions and idioms.
        
        Args:
            design_content: Design document content
            language: Target programming language
            
        Returns:
            Tuple of (score, strengths, weaknesses)
        """
        strengths = []
        weaknesses = []
        score = 0.5  # Base score
        
        if not language or language.lower() not in self.language_patterns:
            # Generic evaluation for unknown languages
            if any(term in design_content.lower() for term in 
                   ['best practice', 'convention', 'standard', 'idiomatic']):
                strengths.append("Mentions best practices and conventions")
                score += 0.2
            else:
                weaknesses.append("No mention of language-specific best practices")
                score -= 0.1
                
            return max(0.0, min(1.0, score)), strengths, weaknesses
            
        # Language-specific evaluation
        lang_patterns = self.language_patterns[language.lower()]
        content_lower = design_content.lower()
        
        # Check for language patterns
        pattern_matches = sum(1 for pattern in lang_patterns['patterns'] 
                            if pattern in content_lower)
        if pattern_matches >= len(lang_patterns['patterns']) * 0.7:
            strengths.append(f"Strong use of {language} idioms and patterns")
            score += 0.3
        elif pattern_matches > 0:
            strengths.append(f"Some use of {language} patterns")
            score += 0.1
        else:
            weaknesses.append(f"Limited use of {language}-specific patterns")
            score -= 0.2
            
        # Check for anti-patterns
        anti_pattern_matches = sum(1 for anti in lang_patterns['anti_patterns'] 
                                 if anti in content_lower)
        if anti_pattern_matches > 0:
            weaknesses.append(f"Contains {language} anti-patterns")
            score -= 0.2
        else:
            strengths.append(f"Avoids common {language} anti-patterns")
            score += 0.1
            
        # Check for best practices
        practice_matches = sum(1 for practice in lang_patterns['best_practices'] 
                             if practice in content_lower)
        if practice_matches >= len(lang_patterns['best_practices']) * 0.5:
            strengths.append(f"Incorporates {language} best practices")
            score += 0.2
        elif practice_matches > 0:
            strengths.append(f"Some {language} best practices mentioned")
            score += 0.1
        else:
            weaknesses.append(f"Limited discussion of {language} best practices")
            score -= 0.1
            
        return max(0.0, min(1.0, score)), strengths, weaknesses
        
    def evaluate_architecture(self, design_content: str) -> Tuple[float, List[str], List[str]]:
        """
        Evaluate technical correctness and scalability.
        
        Args:
            design_content: Design document content
            
        Returns:
            Tuple of (score, strengths, weaknesses)
        """
        strengths = []
        weaknesses = []
        score = 0.5  # Base score
        content_lower = design_content.lower()
        
        # Check for architectural components
        components = ['component', 'module', 'service', 'layer', 'interface']
        component_mentions = sum(1 for comp in components if comp in content_lower)
        if component_mentions >= 3:
            strengths.append("Well-defined architectural components")
            score += 0.2
        elif component_mentions > 0:
            strengths.append("Some architectural structure")
            score += 0.1
        else:
            weaknesses.append("Unclear architectural structure")
            score -= 0.2
            
        # Check for scalability considerations
        scalability_terms = ['scalability', 'scale', 'performance', 'load', 'concurrent']
        if any(term in content_lower for term in scalability_terms):
            strengths.append("Addresses scalability concerns")
            score += 0.2
        else:
            weaknesses.append("Limited scalability discussion")
            score -= 0.1
            
        # Check for data flow and communication
        if any(term in content_lower for term in ['data flow', 'communication', 'api', 'interface']):
            strengths.append("Defines data flow and communication")
            score += 0.15
        else:
            weaknesses.append("Unclear data flow and communication")
            score -= 0.15
            
        # Check for error handling and resilience
        if any(term in content_lower for term in ['error', 'exception', 'failure', 'resilience']):
            strengths.append("Considers error handling and resilience")
            score += 0.15
        else:
            weaknesses.append("Limited error handling discussion")
            score -= 0.1
            
        # Check for separation of concerns
        if any(term in content_lower for term in ['separation', 'concern', 'responsibility', 'single']):
            strengths.append("Good separation of concerns")
            score += 0.1
        
        return max(0.0, min(1.0, score)), strengths, weaknesses
        
    def evaluate_implementability(self, design_content: str) -> Tuple[float, List[str], List[str]]:
        """
        Evaluate practical implementation feasibility.
        
        Args:
            design_content: Design document content
            
        Returns:
            Tuple of (score, strengths, weaknesses)
        """
        strengths = []
        weaknesses = []
        score = 0.5  # Base score
        content_lower = design_content.lower()
        
        # Check for concrete implementation details
        impl_terms = ['implement', 'code', 'function', 'method', 'algorithm']
        impl_mentions = sum(1 for term in impl_terms if term in content_lower)
        if impl_mentions >= 3:
            strengths.append("Provides concrete implementation guidance")
            score += 0.3
        elif impl_mentions > 0:
            strengths.append("Some implementation details")
            score += 0.1
        else:
            weaknesses.append("Lacks implementation details")
            score -= 0.2
            
        # Check for technology stack specification
        tech_terms = ['framework', 'library', 'database', 'technology', 'stack']
        if any(term in content_lower for term in tech_terms):
            strengths.append("Specifies technology choices")
            score += 0.2
        else:
            weaknesses.append("Unclear technology stack")
            score -= 0.1
            
        # Check for complexity assessment
        complexity_terms = ['simple', 'complex', 'easy', 'difficult', 'effort']
        if any(term in content_lower for term in complexity_terms):
            strengths.append("Considers implementation complexity")
            score += 0.1
            
        # Check for step-by-step approach
        if any(term in content_lower for term in ['step', 'phase', 'stage', 'milestone']):
            strengths.append("Provides implementation roadmap")
            score += 0.2
        else:
            weaknesses.append("No clear implementation roadmap")
            score -= 0.1
            
        # Check for dependencies and requirements
        if any(term in content_lower for term in ['dependency', 'requirement', 'prerequisite']):
            strengths.append("Identifies dependencies and requirements")
            score += 0.1
            
        return max(0.0, min(1.0, score)), strengths, weaknesses
        
    def evaluate_completeness(self, design_content: str) -> Tuple[float, List[str], List[str]]:
        """
        Evaluate thoroughness of architectural coverage.
        
        Args:
            design_content: Design document content
            
        Returns:
            Tuple of (score, strengths, weaknesses)
        """
        strengths = []
        weaknesses = []
        score = 0.0
        content_lower = design_content.lower()
        
        # Required sections checklist
        required_sections = {
            'overview': ['overview', 'introduction', 'summary'],
            'architecture': ['architecture', 'design', 'structure'],
            'components': ['component', 'module', 'service'],
            'data': ['data', 'model', 'schema', 'database'],
            'interfaces': ['interface', 'api', 'contract'],
            'deployment': ['deployment', 'infrastructure', 'environment']
        }
        
        sections_found = 0
        for section_name, keywords in required_sections.items():
            if any(keyword in content_lower for keyword in keywords):
                sections_found += 1
                
        completion_ratio = sections_found / len(required_sections)
        score = completion_ratio
        
        if completion_ratio >= 0.8:
            strengths.append("Comprehensive coverage of all major areas")
        elif completion_ratio >= 0.6:
            strengths.append("Good coverage of most areas")
        elif completion_ratio >= 0.4:
            strengths.append("Basic coverage of key areas")
            weaknesses.append("Missing some important architectural aspects")
        else:
            weaknesses.append("Incomplete architectural coverage")
            
        # Check document length (proxy for detail level)
        word_count = len(design_content.split())
        if word_count >= 1000:
            strengths.append("Detailed and thorough documentation")
            score += 0.1
        elif word_count >= 500:
            strengths.append("Adequate level of detail")
        else:
            weaknesses.append("Lacks sufficient detail")
            score -= 0.1
            
        return max(0.0, min(1.0, score)), strengths, weaknesses
        
    def evaluate_innovation(self, design_content: str) -> Tuple[float, List[str], List[str]]:
        """
        Evaluate creative and elegant solutions.
        
        Args:
            design_content: Design document content
            
        Returns:
            Tuple of (score, strengths, weaknesses)
        """
        strengths = []
        weaknesses = []
        score = 0.5  # Base score
        content_lower = design_content.lower()
        
        # Check for innovative approaches
        innovation_terms = ['innovative', 'novel', 'creative', 'elegant', 'unique']
        if any(term in content_lower for term in innovation_terms):
            strengths.append("Demonstrates innovative thinking")
            score += 0.2
            
        # Check for modern patterns and practices
        modern_terms = ['modern', 'contemporary', 'latest', 'current', 'state-of-the-art']
        if any(term in content_lower for term in modern_terms):
            strengths.append("Uses modern approaches")
            score += 0.1
            
        # Check for optimization and efficiency
        efficiency_terms = ['optimize', 'efficient', 'performance', 'fast', 'lightweight']
        if any(term in content_lower for term in efficiency_terms):
            strengths.append("Focuses on optimization and efficiency")
            score += 0.2
            
        # Check for extensibility and flexibility
        flexibility_terms = ['extensible', 'flexible', 'modular', 'configurable', 'pluggable']
        if any(term in content_lower for term in flexibility_terms):
            strengths.append("Designed for extensibility")
            score += 0.2
            
        # Penalty for overly complex or convoluted approaches
        complexity_terms = ['complicated', 'convoluted', 'over-engineered', 'complex']
        if any(term in content_lower for term in complexity_terms):
            weaknesses.append("May be overly complex")
            score -= 0.1
            
        return max(0.0, min(1.0, score)), strengths, weaknesses
        
    def evaluate_documentation(self, design_content: str) -> Tuple[float, List[str], List[str]]:
        """
        Evaluate clarity and comprehensiveness of documentation.
        
        Args:
            design_content: Design document content
            
        Returns:
            Tuple of (score, strengths, weaknesses)
        """
        strengths = []
        weaknesses = []
        score = 0.5  # Base score
        
        # Check for clear structure (headers, sections)
        header_count = len(re.findall(r'^#+\s+', design_content, re.MULTILINE))
        if header_count >= 5:
            strengths.append("Well-structured with clear sections")
            score += 0.2
        elif header_count >= 3:
            strengths.append("Good document structure")
            score += 0.1
        else:
            weaknesses.append("Poor document structure")
            score -= 0.2
            
        # Check for diagrams or visual elements
        if any(term in design_content.lower() for term in ['diagram', 'figure', 'chart', 'visual']):
            strengths.append("Includes visual documentation")
            score += 0.2
            
        # Check for examples and use cases
        if any(term in design_content.lower() for term in ['example', 'use case', 'scenario']):
            strengths.append("Provides examples and use cases")
            score += 0.2
            
        # Check for clear language and readability
        sentences = design_content.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        if 10 <= avg_sentence_length <= 25:
            strengths.append("Clear and readable writing style")
            score += 0.1
        elif avg_sentence_length > 30:
            weaknesses.append("Sentences may be too long and complex")
            score -= 0.1
            
        # Check for consistent terminology
        if design_content.count('TODO') > 0 or design_content.count('TBD') > 0:
            weaknesses.append("Contains incomplete sections")
            score -= 0.2
            
        return max(0.0, min(1.0, score)), strengths, weaknesses
        
    def evaluate_design(self, design_content: str, 
                       language: Optional[str] = None,
                       metadata: Optional[Dict] = None) -> DesignScore:
        """
        Evaluate a complete design using all criteria.
        
        Args:
            design_content: Design document content
            language: Target programming language
            metadata: Additional evaluation metadata
            
        Returns:
            DesignScore with detailed evaluation
        """
        # Evaluate each criteria
        lang_score, lang_strengths, lang_weaknesses = self.evaluate_language_idioms(
            design_content, language)
        arch_score, arch_strengths, arch_weaknesses = self.evaluate_architecture(
            design_content)
        impl_score, impl_strengths, impl_weaknesses = self.evaluate_implementability(
            design_content)
        comp_score, comp_strengths, comp_weaknesses = self.evaluate_completeness(
            design_content)
        innov_score, innov_strengths, innov_weaknesses = self.evaluate_innovation(
            design_content)
        doc_score, doc_strengths, doc_weaknesses = self.evaluate_documentation(
            design_content)
        
        # Calculate weighted overall score
        overall_score = (
            lang_score * self.criteria.language_idioms +
            arch_score * self.criteria.architecture +
            impl_score * self.criteria.implementability +
            comp_score * self.criteria.completeness +
            innov_score * self.criteria.innovation +
            doc_score * self.criteria.documentation
        )
        
        # Combine feedback
        all_strengths = (lang_strengths + arch_strengths + impl_strengths + 
                        comp_strengths + innov_strengths + doc_strengths)
        all_weaknesses = (lang_weaknesses + arch_weaknesses + impl_weaknesses + 
                         comp_weaknesses + innov_weaknesses + doc_weaknesses)
        
        # Generate summary feedback
        if overall_score >= 0.8:
            feedback = "Excellent design with strong architectural foundation"
        elif overall_score >= 0.6:
            feedback = "Good design with solid implementation potential"
        elif overall_score >= 0.4:
            feedback = "Adequate design but needs improvements"
        else:
            feedback = "Design requires significant improvements"
            
        return DesignScore(
            overall_score=overall_score,
            language_idioms=lang_score,
            architecture=arch_score,
            implementability=impl_score,
            completeness=comp_score,
            innovation=innov_score,
            documentation=doc_score,
            feedback=feedback,
            strengths=all_strengths,
            weaknesses=all_weaknesses
        )
        
    def rank_designs(self, design_candidates: List[Dict[str, Any]], 
                    language: Optional[str] = None) -> List[Tuple[int, DesignScore]]:
        """
        Rank multiple design candidates.
        
        Args:
            design_candidates: List of design candidate dictionaries
            language: Target programming language
            
        Returns:
            List of (candidate_index, DesignScore) tuples, sorted by score
        """
        scored_designs = []
        
        for i, candidate in enumerate(design_candidates):
            content = candidate.get('output', candidate.get('content', ''))
            if content:
                score = self.evaluate_design(content, language, candidate)
                scored_designs.append((i, score))
                
        # Sort by overall score (descending)
        scored_designs.sort(key=lambda x: x[1].overall_score, reverse=True)
        
        self.logger.info(
            f"Ranked {len(scored_designs)} designs. "
            f"Best score: {scored_designs[0][1].overall_score:.3f}"
        )
        
        return scored_designs


def main():
    """Test design evaluator functionality."""
    evaluator = DesignEvaluator()
    
    # Test design content
    test_design = """
    # Go Pomodoro Timer Architecture
    
    ## Overview
    A simple and efficient pomodoro timer application built in Go, focusing on clean architecture and extensibility.
    
    ## Core Components
    
    ### Timer Engine
    - Uses goroutines for concurrent timer management
    - Channel-based communication for timer events
    - Interface-based design for extensibility
    
    ### Configuration Manager
    - Struct-based configuration with JSON marshaling
    - Environment variable support
    - Validation and default values
    
    ## Implementation Approach
    - Small, focused interfaces following Go conventions
    - Composition over inheritance
    - Proper error handling with explicit error returns
    - Comprehensive unit tests
    
    ## Technology Stack
    - Go 1.19+
    - Standard library for core functionality
    - Third-party libraries for CLI and notifications
    """
    
    score = evaluator.evaluate_design(test_design, language='go')
    
    print(f"Overall Score: {score.overall_score:.3f}")
    print(f"Feedback: {score.feedback}")
    print(f"\nStrengths:")
    for strength in score.strengths:
        print(f"  + {strength}")
    print(f"\nWeaknesses:")
    for weakness in score.weaknesses:
        print(f"  - {weakness}")
    print(f"\nDetailed Scores:")
    print(f"  Language Idioms: {score.language_idioms:.3f}")
    print(f"  Architecture: {score.architecture:.3f}")
    print(f"  Implementability: {score.implementability:.3f}")
    print(f"  Completeness: {score.completeness:.3f}")
    print(f"  Innovation: {score.innovation:.3f}")
    print(f"  Documentation: {score.documentation:.3f}")


if __name__ == "__main__":
    main()