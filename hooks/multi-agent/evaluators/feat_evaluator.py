#!/usr/bin/env python3
"""
Feature implementation evaluator for multi-agent orchestration system.
Assesses feature specifications with focus on structural preservation and implementation detail.
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from pathlib import Path
import logging


@dataclass
class StructuralValidation:
    """Results of structural validation."""
    is_valid: bool
    expected_sections: List[str]
    found_sections: List[str]
    missing_sections: List[str]
    extra_sections: List[str]
    structure_score: float


@dataclass
class FeatScore:
    """Score for a feature specification candidate."""
    overall_score: float
    structural_integrity: float
    implementation_detail: float
    language_specificity: float
    technical_accuracy: float
    clarity: float
    feedback: str
    strengths: List[str]
    weaknesses: List[str]
    structural_validation: StructuralValidation


class FeatEvaluator:
    """Evaluates feature implementation specifications with structure preservation focus."""
    
    def __init__(self):
        """Initialize feature evaluator."""
        self.logger = self._setup_logging()
        
        # Weights for evaluation criteria
        self.weights = {
            'structural_integrity': 0.30,   # Exact subsection structure preservation
            'implementation_detail': 0.25,  # Depth and specificity of implementation guidance
            'language_specificity': 0.20,   # Language-specific patterns and approaches
            'technical_accuracy': 0.15,     # Technical correctness and feasibility
            'clarity': 0.10                 # Clarity and readability
        }
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for feature evaluator."""
        logger = logging.getLogger('feat_evaluator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    def extract_section_structure(self, content: str) -> List[str]:
        """
        Extract section structure from markdown content.
        
        Args:
            content: Markdown content
            
        Returns:
            List of section headers in order
        """
        sections = []
        
        # Find all headers (# ## ### etc.)
        header_pattern = r'^(#+)\s+(.+)$'
        for match in re.finditer(header_pattern, content, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            
            # Normalize section identifier
            # Remove numbers if present (e.g., "2.1 Section Title" -> "section title")
            normalized = re.sub(r'^[\d.]+\s*', '', title).lower().strip()
            sections.append(normalized)
            
        return sections
        
    def extract_expected_structure(self, app_md_content: str, section_id: str) -> List[str]:
        """
        Extract expected subsection structure from app.md for a specific section.
        
        Args:
            app_md_content: Content of app.md
            section_id: Section identifier (e.g., "1", "2.3", "timer-core")
            
        Returns:
            List of expected subsection headers
        """
        expected_sections = []
        
        if not app_md_content:
            return expected_sections
            
        lines = app_md_content.split('\n')
        in_target_section = False
        target_level = None
        
        for line in lines:
            line = line.strip()
            
            # Check for header
            header_match = re.match(r'^(#+)\s+(.+)$', line)
            if not header_match:
                continue
                
            level = len(header_match.group(1))
            title = header_match.group(2).strip()
            
            # Check if this is our target section
            if self._is_target_section(title, section_id):
                in_target_section = True
                target_level = level
                continue
                
            if in_target_section:
                if level <= target_level:
                    # We've reached the next section at same or higher level
                    break
                elif level == target_level + 1:
                    # This is a direct subsection
                    normalized = re.sub(r'^[\d.]+\s*', '', title).lower().strip()
                    expected_sections.append(normalized)
                    
        return expected_sections
        
    def _is_target_section(self, title: str, section_id: str) -> bool:
        """Check if a title matches the target section."""
        title_lower = title.lower()
        section_lower = section_id.lower()
        
        # Check for exact numeric match (e.g., "1", "2.3")
        if re.match(r'^\d+(\.\d+)?$', section_id):
            pattern = r'^' + re.escape(section_id) + r'[.\s]'
            if re.search(pattern, title):
                return True
                
        # Check for name match
        if section_lower in title_lower or title_lower in section_lower:
            return True
            
        return False
        
    def validate_structure(self, feat_content: str, expected_sections: List[str]) -> StructuralValidation:
        """
        Validate that feature specification preserves expected structure.
        
        Args:
            feat_content: Feature specification content
            expected_sections: Expected subsection structure
            
        Returns:
            StructuralValidation result
        """
        found_sections = self.extract_section_structure(feat_content)
        
        # Convert to sets for comparison
        expected_set = set(expected_sections)
        found_set = set(found_sections)
        
        missing_sections = list(expected_set - found_set)
        extra_sections = list(found_set - expected_set)
        
        # Calculate structure score
        if not expected_sections:
            # No expected structure, so any structure is acceptable
            structure_score = 1.0
            is_valid = True
        else:
            # Score based on how well structure is preserved
            if missing_sections or extra_sections:
                # Penalize missing sections more than extra sections
                missing_penalty = len(missing_sections) * 0.3
                extra_penalty = len(extra_sections) * 0.1
                total_penalty = missing_penalty + extra_penalty
                structure_score = max(0.0, 1.0 - total_penalty / len(expected_sections))
                is_valid = len(missing_sections) == 0  # Valid if no missing sections
            else:
                structure_score = 1.0
                is_valid = True
                
        return StructuralValidation(
            is_valid=is_valid,
            expected_sections=expected_sections,
            found_sections=found_sections,
            missing_sections=missing_sections,
            extra_sections=extra_sections,
            structure_score=structure_score
        )
        
    def evaluate_implementation_detail(self, feat_content: str) -> Tuple[float, List[str], List[str]]:
        """
        Evaluate depth and specificity of implementation guidance.
        
        Args:
            feat_content: Feature specification content
            
        Returns:
            Tuple of (score, strengths, weaknesses)
        """
        strengths = []
        weaknesses = []
        score = 0.0
        content_lower = feat_content.lower()
        
        # Check for specific implementation details
        detail_indicators = [
            'function', 'method', 'class', 'struct', 'interface',
            'algorithm', 'data structure', 'parameter', 'return',
            'input', 'output', 'validation', 'error handling'
        ]
        
        detail_count = sum(1 for indicator in detail_indicators if indicator in content_lower)
        detail_score = min(1.0, detail_count / len(detail_indicators))
        score += detail_score * 0.4
        
        if detail_score >= 0.7:
            strengths.append("Rich implementation details and specificity")
        elif detail_score >= 0.4:
            strengths.append("Good level of implementation detail")
        else:
            weaknesses.append("Lacks specific implementation details")
            
        # Check for code examples or pseudocode
        if any(marker in feat_content for marker in ['```', '```python', '```go', '```rust']):
            strengths.append("Includes code examples")
            score += 0.2
        elif any(marker in content_lower for marker in ['pseudocode', 'example', 'sample']):
            strengths.append("Provides implementation examples")
            score += 0.1
        else:
            weaknesses.append("No code examples or pseudocode")
            
        # Check for data flow and process descriptions
        flow_terms = ['flow', 'process', 'step', 'sequence', 'workflow']
        if any(term in content_lower for term in flow_terms):
            strengths.append("Describes implementation flow and processes")
            score += 0.2
        else:
            weaknesses.append("Limited description of implementation flow")
            
        # Check for edge cases and error conditions
        if any(term in content_lower for term in ['edge case', 'error', 'exception', 'failure']):
            strengths.append("Addresses edge cases and error handling")
            score += 0.1
        else:
            weaknesses.append("Missing edge case and error handling discussion")
            
        # Check for performance considerations
        if any(term in content_lower for term in ['performance', 'optimization', 'efficiency']):
            strengths.append("Includes performance considerations")
            score += 0.1
            
        return max(0.0, min(1.0, score)), strengths, weaknesses
        
    def evaluate_language_specificity(self, feat_content: str, language: Optional[str] = None) -> Tuple[float, List[str], List[str]]:
        """
        Evaluate language-specific patterns and approaches.
        
        Args:
            feat_content: Feature specification content
            language: Target programming language
            
        Returns:
            Tuple of (score, strengths, weaknesses)
        """
        strengths = []
        weaknesses = []
        score = 0.5  # Base score
        content_lower = feat_content.lower()
        
        if not language:
            # Generic evaluation without specific language
            if any(term in content_lower for term in ['language-specific', 'idiom', 'convention']):
                strengths.append("Mentions language-specific considerations")
                score += 0.2
            return score, strengths, weaknesses
            
        # Language-specific evaluation
        language_patterns = {
            'go': {
                'positive': ['interface', 'struct', 'goroutine', 'channel', 'defer', 'panic', 'recover'],
                'negative': ['class', 'inheritance', 'exception'],
                'practices': ['composition', 'error handling', 'concurrency']
            },
            'python': {
                'positive': ['class', 'decorator', 'generator', 'context manager', 'list comprehension'],
                'negative': ['goto', 'multiple inheritance abuse'],
                'practices': ['pythonic', 'pep 8', 'duck typing', 'zen of python']
            },
            'rust': {
                'positive': ['ownership', 'borrowing', 'trait', 'enum', 'match', 'result', 'option'],
                'negative': ['garbage collection', 'null pointer'],
                'practices': ['memory safety', 'zero-cost abstraction', 'fearless concurrency']
            }
        }
        
        if language.lower() in language_patterns:
            patterns = language_patterns[language.lower()]
            
            # Check for positive language patterns
            positive_matches = sum(1 for pattern in patterns['positive'] if pattern in content_lower)
            if positive_matches >= len(patterns['positive']) * 0.5:
                strengths.append(f"Strong use of {language}-specific patterns")
                score += 0.3
            elif positive_matches > 0:
                strengths.append(f"Some {language}-specific patterns used")
                score += 0.1
            else:
                weaknesses.append(f"Limited use of {language}-specific patterns")
                score -= 0.2
                
            # Check for negative patterns (anti-patterns)
            negative_matches = sum(1 for pattern in patterns['negative'] if pattern in content_lower)
            if negative_matches > 0:
                weaknesses.append(f"Contains {language} anti-patterns")
                score -= 0.2
                
            # Check for best practices
            practice_matches = sum(1 for practice in patterns['practices'] if practice in content_lower)
            if practice_matches > 0:
                strengths.append(f"Incorporates {language} best practices")
                score += 0.2
        else:
            # Unknown language
            if language in content_lower:
                strengths.append(f"Mentions {language} in context")
                score += 0.1
                
        return max(0.0, min(1.0, score)), strengths, weaknesses
        
    def evaluate_technical_accuracy(self, feat_content: str) -> Tuple[float, List[str], List[str]]:
        """
        Evaluate technical correctness and feasibility.
        
        Args:
            feat_content: Feature specification content
            
        Returns:
            Tuple of (score, strengths, weaknesses)
        """
        strengths = []
        weaknesses = []
        score = 0.5  # Base score
        content_lower = feat_content.lower()
        
        # Check for technical depth
        tech_terms = [
            'algorithm', 'data structure', 'complexity', 'performance',
            'memory', 'cpu', 'network', 'database', 'api', 'protocol'
        ]
        tech_mentions = sum(1 for term in tech_terms if term in content_lower)
        if tech_mentions >= 5:
            strengths.append("Strong technical depth")
            score += 0.3
        elif tech_mentions >= 3:
            strengths.append("Good technical coverage")
            score += 0.1
        else:
            weaknesses.append("Limited technical depth")
            score -= 0.1
            
        # Check for architecture patterns
        arch_patterns = ['mvc', 'mvp', 'singleton', 'factory', 'observer', 'strategy']
        if any(pattern in content_lower for pattern in arch_patterns):
            strengths.append("Uses established architecture patterns")
            score += 0.2
            
        # Check for security considerations
        security_terms = ['security', 'authentication', 'authorization', 'encryption', 'validation']
        if any(term in content_lower for term in security_terms):
            strengths.append("Addresses security considerations")
            score += 0.1
        else:
            weaknesses.append("Limited security discussion")
            
        # Check for scalability and maintainability
        if any(term in content_lower for term in ['scalable', 'maintainable', 'extensible']):
            strengths.append("Considers scalability and maintainability")
            score += 0.1
            
        # Check for testing approach
        if any(term in content_lower for term in ['test', 'testing', 'unit test', 'integration']):
            strengths.append("Includes testing approach")
            score += 0.2
        else:
            weaknesses.append("No testing methodology specified")
            score -= 0.1
            
        return max(0.0, min(1.0, score)), strengths, weaknesses
        
    def evaluate_clarity(self, feat_content: str) -> Tuple[float, List[str], List[str]]:
        """
        Evaluate clarity and readability.
        
        Args:
            feat_content: Feature specification content
            
        Returns:
            Tuple of (score, strengths, weaknesses)
        """
        strengths = []
        weaknesses = []
        score = 0.5  # Base score
        
        # Check document structure
        header_count = len(re.findall(r'^#+\s+', feat_content, re.MULTILINE))
        if header_count >= 3:
            strengths.append("Well-structured document")
            score += 0.2
        elif header_count >= 1:
            strengths.append("Basic document structure")
            score += 0.1
        else:
            weaknesses.append("Poor document structure")
            score -= 0.2
            
        # Check for lists and bullet points
        list_pattern = r'^[\s]*[-*+]\s+|^\s*\d+\.\s+'
        list_count = len(re.findall(list_pattern, feat_content, re.MULTILINE))
        if list_count >= 5:
            strengths.append("Good use of lists for organization")
            score += 0.1
            
        # Check for clear language indicators
        clear_indicators = ['specifically', 'namely', 'for example', 'in other words', 'that is']
        if any(indicator in feat_content.lower() for indicator in clear_indicators):
            strengths.append("Uses clear explanatory language")
            score += 0.1
            
        # Check sentence length (readability proxy)
        sentences = [s.strip() for s in feat_content.split('.') if s.strip()]
        if sentences:
            avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if 10 <= avg_length <= 25:
                strengths.append("Good sentence length for readability")
                score += 0.1
            elif avg_length > 30:
                weaknesses.append("Sentences may be too long")
                score -= 0.1
                
        # Check for completeness indicators
        if any(incomplete in feat_content.upper() for incomplete in ['TODO', 'TBD', 'FIXME']):
            weaknesses.append("Contains incomplete sections")
            score -= 0.2
            
        return max(0.0, min(1.0, score)), strengths, weaknesses
        
    def evaluate_feature(self, feat_content: str, 
                        expected_structure: Optional[List[str]] = None,
                        language: Optional[str] = None,
                        metadata: Optional[Dict] = None) -> FeatScore:
        """
        Evaluate a complete feature specification.
        
        Args:
            feat_content: Feature specification content
            expected_structure: Expected subsection structure from app.md
            language: Target programming language
            metadata: Additional evaluation metadata
            
        Returns:
            FeatScore with detailed evaluation
        """
        # Structural validation (critical requirement)
        structural_validation = self.validate_structure(feat_content, expected_structure or [])
        
        # Other evaluations
        impl_score, impl_strengths, impl_weaknesses = self.evaluate_implementation_detail(feat_content)
        lang_score, lang_strengths, lang_weaknesses = self.evaluate_language_specificity(feat_content, language)
        tech_score, tech_strengths, tech_weaknesses = self.evaluate_technical_accuracy(feat_content)
        clarity_score, clarity_strengths, clarity_weaknesses = self.evaluate_clarity(feat_content)
        
        # Calculate weighted overall score
        overall_score = (
            structural_validation.structure_score * self.weights['structural_integrity'] +
            impl_score * self.weights['implementation_detail'] +
            lang_score * self.weights['language_specificity'] +
            tech_score * self.weights['technical_accuracy'] +
            clarity_score * self.weights['clarity']
        )
        
        # Combine feedback
        all_strengths = (impl_strengths + lang_strengths + tech_strengths + clarity_strengths)
        all_weaknesses = (impl_weaknesses + lang_weaknesses + tech_weaknesses + clarity_weaknesses)
        
        # Add structural feedback
        if structural_validation.is_valid:
            all_strengths.insert(0, "Preserves required section structure")
        else:
            all_weaknesses.insert(0, f"Missing required sections: {', '.join(structural_validation.missing_sections)}")
            
        # Generate summary feedback
        if overall_score >= 0.8:
            feedback = "Excellent feature specification with comprehensive implementation guidance"
        elif overall_score >= 0.6:
            feedback = "Good feature specification ready for implementation"
        elif overall_score >= 0.4:
            feedback = "Adequate specification but needs more detail"
        else:
            feedback = "Specification requires significant improvements"
            
        return FeatScore(
            overall_score=overall_score,
            structural_integrity=structural_validation.structure_score,
            implementation_detail=impl_score,
            language_specificity=lang_score,
            technical_accuracy=tech_score,
            clarity=clarity_score,
            feedback=feedback,
            strengths=all_strengths,
            weaknesses=all_weaknesses,
            structural_validation=structural_validation
        )
        
    def rank_features(self, feature_candidates: List[Dict[str, Any]], 
                     expected_structure: Optional[List[str]] = None,
                     language: Optional[str] = None) -> List[Tuple[int, FeatScore]]:
        """
        Rank multiple feature specification candidates.
        
        Args:
            feature_candidates: List of feature candidate dictionaries
            expected_structure: Expected subsection structure
            language: Target programming language
            
        Returns:
            List of (candidate_index, FeatScore) tuples, sorted by score
        """
        scored_features = []
        
        for i, candidate in enumerate(feature_candidates):
            content = candidate.get('output', candidate.get('content', ''))
            if content:
                score = self.evaluate_feature(content, expected_structure, language, candidate)
                scored_features.append((i, score))
                
        # Sort by overall score, but prioritize structural integrity
        def sort_key(item):
            _, score = item
            # Heavily penalize structural violations
            structure_penalty = 0 if score.structural_validation.is_valid else -1.0
            return score.overall_score + structure_penalty
            
        scored_features.sort(key=sort_key, reverse=True)
        
        self.logger.info(
            f"Ranked {len(scored_features)} feature specifications. "
            f"Best score: {scored_features[0][1].overall_score:.3f}"
        )
        
        return scored_features


def main():
    """Test feature evaluator functionality."""
    evaluator = FeatEvaluator()
    
    # Test feature specification
    test_feat = """
    # Timer Core Implementation
    
    ## Timer State Management
    Implement a robust timer state machine with the following states:
    - Idle: Timer not running
    - Active: Timer counting down
    - Paused: Timer temporarily stopped
    - Completed: Timer finished
    
    ### Go Implementation
    ```go
    type TimerState int
    
    const (
        StateIdle TimerState = iota
        StateActive
        StatePaused
        StateCompleted
    )
    ```
    
    ## Event Handling System
    Create an event-driven architecture for timer events:
    - Start events
    - Pause/Resume events
    - Completion events
    - Configuration change events
    
    ## Error Handling
    Implement comprehensive error handling for:
    - Invalid timer durations
    - State transition errors
    - System resource limitations
    
    ## Testing Strategy
    - Unit tests for state transitions
    - Integration tests for event handling
    - Performance tests for timer accuracy
    """
    
    expected_structure = [
        "timer state management",
        "event handling system", 
        "error handling"
    ]
    
    score = evaluator.evaluate_feature(test_feat, expected_structure, language='go')
    
    print(f"Overall Score: {score.overall_score:.3f}")
    print(f"Feedback: {score.feedback}")
    print(f"\nStructural Validation:")
    print(f"  Valid: {score.structural_validation.is_valid}")
    print(f"  Structure Score: {score.structural_validation.structure_score:.3f}")
    print(f"  Missing: {score.structural_validation.missing_sections}")
    print(f"  Extra: {score.structural_validation.extra_sections}")
    print(f"\nStrengths:")
    for strength in score.strengths:
        print(f"  + {strength}")
    print(f"\nWeaknesses:")
    for weakness in score.weaknesses:
        print(f"  - {weakness}")
    print(f"\nDetailed Scores:")
    print(f"  Structural Integrity: {score.structural_integrity:.3f}")
    print(f"  Implementation Detail: {score.implementation_detail:.3f}")
    print(f"  Language Specificity: {score.language_specificity:.3f}")
    print(f"  Technical Accuracy: {score.technical_accuracy:.3f}")
    print(f"  Clarity: {score.clarity:.3f}")


if __name__ == "__main__":
    main()