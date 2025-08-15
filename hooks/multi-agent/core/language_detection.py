#!/usr/bin/env python3
"""
Language detection engine for multi-agent orchestration system.
Analyzes project context to identify target language and map to appropriate agents.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter


@dataclass
class LanguageEvidence:
    """Evidence for a particular programming language."""
    language: str
    confidence: float
    evidence_type: str  # 'config', 'source', 'pattern'
    evidence: str  # Description of evidence found


@dataclass
class LanguageDetectionResult:
    """Result of language detection analysis."""
    detected_language: Optional[str]
    confidence: float
    all_evidence: List[LanguageEvidence]
    recommendation: str


class LanguageDetector:
    """Detects programming language from project context."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize with language configuration."""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "language_agents.json"
            
        self.config = self._load_config(config_path)
        self.confidence_threshold = 0.6
        self.file_scan_depth = 3
        
    def _load_config(self, config_path: str) -> Dict:
        """Load language configuration."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default configuration if file doesn't exist
            return {
                "languages": {
                    "go": {
                        "architect": "gad",
                        "developer": "god",
                        "confidence_threshold": 0.8,
                        "file_extensions": [".go"],
                        "config_files": ["go.mod", "go.sum"],
                        "patterns": ["package main", "func main()", "import ("]
                    },
                    "python": {
                        "architect": "pyad",
                        "developer": "pydv",
                        "confidence_threshold": 0.8,
                        "file_extensions": [".py"],
                        "config_files": ["pyproject.toml", "requirements.txt", "setup.py", "Pipfile"],
                        "patterns": ["def ", "import ", "from ", "if __name__ == '__main__':"]
                    },
                    "rust": {
                        "architect": "rustarch",
                        "developer": "rustdev",
                        "confidence_threshold": 0.8,
                        "file_extensions": [".rs"],
                        "config_files": ["Cargo.toml", "Cargo.lock"],
                        "patterns": ["fn main()", "use ", "pub fn", "struct "]
                    },
                    "javascript": {
                        "architect": "jsad",
                        "developer": "jsdev",
                        "confidence_threshold": 0.8,
                        "file_extensions": [".js", ".mjs"],
                        "config_files": ["package.json", "yarn.lock", "package-lock.json"],
                        "patterns": ["function ", "const ", "let ", "var ", "=>"]
                    },
                    "typescript": {
                        "architect": "tsad",
                        "developer": "tsdev",
                        "confidence_threshold": 0.8,
                        "file_extensions": [".ts", ".tsx"],
                        "config_files": ["tsconfig.json", "package.json"],
                        "patterns": ["interface ", "type ", ": string", ": number", "export "]
                    }
                }
            }
            
    def detect_from_config_files(self, project_path: str) -> List[LanguageEvidence]:
        """Detect language from configuration files (90% confidence)."""
        evidence = []
        project_path = Path(project_path)
        
        for lang, config in self.config["languages"].items():
            config_files = config.get("config_files", [])
            
            for config_file in config_files:
                config_file_path = project_path / config_file
                if config_file_path.exists():
                    evidence.append(LanguageEvidence(
                        language=lang,
                        confidence=0.9,
                        evidence_type='config',
                        evidence=f"Found {config_file}"
                    ))
                    
        return evidence
        
    def detect_from_source_files(self, project_path: str) -> List[LanguageEvidence]:
        """Detect language from source files (70% confidence)."""
        evidence = []
        project_path = Path(project_path)
        
        # Count file extensions
        extension_counts = Counter()
        
        for root, dirs, files in os.walk(project_path):
            # Limit scan depth
            depth = len(Path(root).relative_to(project_path).parts)
            if depth > self.file_scan_depth:
                continue
                
            # Skip common directories to ignore
            dirs[:] = [d for d in dirs if d not in {'.git', '.vscode', 'node_modules', '__pycache__', 'target', 'dist', 'build'}]
            
            for file in files:
                file_path = Path(root) / file
                ext = file_path.suffix.lower()
                if ext:
                    extension_counts[ext] += 1
                    
        # Analyze extension counts
        for lang, config in self.config["languages"].items():
            extensions = config.get("file_extensions", [])
            total_files = sum(extension_counts[ext] for ext in extensions)
            
            if total_files > 0:
                # Calculate confidence based on file count
                confidence = min(0.7, 0.5 + (total_files * 0.02))
                evidence.append(LanguageEvidence(
                    language=lang,
                    confidence=confidence,
                    evidence_type='source',
                    evidence=f"Found {total_files} {lang} source files"
                ))
                
        return evidence
        
    def detect_from_patterns(self, project_path: str) -> List[LanguageEvidence]:
        """Detect language from code patterns (50% confidence)."""
        evidence = []
        project_path = Path(project_path)
        
        # Sample files to check for patterns
        sample_files = []
        for root, dirs, files in os.walk(project_path):
            depth = len(Path(root).relative_to(project_path).parts)
            if depth > self.file_scan_depth:
                continue
                
            dirs[:] = [d for d in dirs if d not in {'.git', '.vscode', 'node_modules', '__pycache__', 'target', 'dist', 'build'}]
            
            for file in files:
                if any(file.endswith(ext) for exts in 
                      [config.get("file_extensions", []) for config in self.config["languages"].values()]
                      for ext in exts):
                    sample_files.append(Path(root) / file)
                    if len(sample_files) >= 10:  # Limit sampling
                        break
                        
        # Check patterns in sampled files
        for lang, config in self.config["languages"].items():
            patterns = config.get("patterns", [])
            pattern_matches = 0
            total_checks = 0
            
            for file_path in sample_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        total_checks += 1
                        
                    for pattern in patterns:
                        if pattern in content:
                            pattern_matches += 1
                            break  # One match per file is enough
                            
                except (IOError, UnicodeDecodeError):
                    continue
                    
            if pattern_matches > 0 and total_checks > 0:
                confidence = min(0.5, 0.2 + (pattern_matches / total_checks * 0.3))
                evidence.append(LanguageEvidence(
                    language=lang,
                    confidence=confidence,
                    evidence_type='pattern',
                    evidence=f"Found {lang} patterns in {pattern_matches}/{total_checks} files"
                ))
                
        return evidence
        
    def analyze_project(self, project_path: str = ".") -> LanguageDetectionResult:
        """
        Analyze project to detect programming language.
        
        Args:
            project_path: Path to project directory
            
        Returns:
            LanguageDetectionResult with detection results
        """
        all_evidence = []
        
        # Gather evidence from different sources
        all_evidence.extend(self.detect_from_config_files(project_path))
        all_evidence.extend(self.detect_from_source_files(project_path))
        all_evidence.extend(self.detect_from_patterns(project_path))
        
        if not all_evidence:
            return LanguageDetectionResult(
                detected_language=None,
                confidence=0.0,
                all_evidence=[],
                recommendation="No language evidence found. Consider specifying language explicitly."
            )
            
        # Calculate combined confidence per language
        language_scores = {}
        for evidence in all_evidence:
            if evidence.language not in language_scores:
                language_scores[evidence.language] = []
            language_scores[evidence.language].append(evidence.confidence)
            
        # Compute weighted average confidence per language
        language_confidence = {}
        for lang, scores in language_scores.items():
            # Use weighted average favoring higher confidence evidence
            weighted_scores = [score * score for score in scores]  # Square to emphasize high confidence
            language_confidence[lang] = sum(weighted_scores) / len(weighted_scores)
            
        # Find highest confidence language
        if language_confidence:
            best_language = max(language_confidence.items(), key=lambda x: x[1])
            detected_language, confidence = best_language
            
            if confidence >= self.confidence_threshold:
                recommendation = f"Detected {detected_language} with {confidence:.1%} confidence"
            else:
                recommendation = f"Low confidence detection of {detected_language} ({confidence:.1%}). Consider specifying language explicitly."
        else:
            detected_language = None
            confidence = 0.0
            recommendation = "No clear language detected. Please specify language explicitly."
            
        return LanguageDetectionResult(
            detected_language=detected_language if confidence >= self.confidence_threshold else None,
            confidence=confidence,
            all_evidence=all_evidence,
            recommendation=recommendation
        )
        
    def get_language_agents(self, language: str) -> Optional[Dict[str, str]]:
        """Get architect and developer agents for a language."""
        lang_config = self.config["languages"].get(language.lower())
        if lang_config:
            return {
                "architect": lang_config.get("architect"),
                "developer": lang_config.get("developer")
            }
        return None
        
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.config["languages"].keys())


def main():
    """Test language detection."""
    detector = LanguageDetector()
    
    # Test current directory
    result = detector.analyze_project(".")
    print(f"Detection Result:")
    print(f"  Language: {result.detected_language}")
    print(f"  Confidence: {result.confidence:.1%}")
    print(f"  Recommendation: {result.recommendation}")
    print(f"\nEvidence:")
    for evidence in result.all_evidence:
        print(f"  {evidence.language}: {evidence.confidence:.1%} ({evidence.evidence_type}) - {evidence.evidence}")
        
    # Test agent mapping
    if result.detected_language:
        agents = detector.get_language_agents(result.detected_language)
        print(f"\nAgents for {result.detected_language}:")
        print(f"  Architect: {agents['architect']}")
        print(f"  Developer: {agents['developer']}")


if __name__ == "__main__":
    main()