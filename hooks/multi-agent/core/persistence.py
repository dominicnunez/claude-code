#!/usr/bin/env python3
"""
Persistence module for multi-agent orchestration system.
Manages state persistence, archiving, and file lifecycle management.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging


@dataclass
class ArchiveEntry:
    """Represents an archived result."""
    timestamp: str
    task_type: str  # 'design', 'feat', 'dev'
    agent_name: str
    success: bool
    metadata: Dict[str, Any]
    file_path: str


class PersistenceManager:
    """Manages file lifecycle, archiving, and state persistence."""
    
    def __init__(self, base_path: Optional[str] = None):
        """Initialize persistence manager."""
        if base_path is None:
            base_path = Path.cwd() / ".docs"
            
        self.base_path = Path(base_path)
        self.plan_path = self.base_path / "plan"
        self.archive_path = self.base_path / "archive"
        self.temp_path = self.base_path / "temp"
        
        self.logger = self._setup_logging()
        self._ensure_directories()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for persistence manager."""
        logger = logging.getLogger('persistence_manager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    def _ensure_directories(self):
        """Ensure required directories exist."""
        for path in [self.base_path, self.plan_path, self.archive_path, self.temp_path]:
            path.mkdir(parents=True, exist_ok=True)
            
    def save_design(self, content: str, metadata: Dict[str, Any]) -> Path:
        """
        Save selected design to plan directory.
        
        Args:
            content: Design content
            metadata: Design metadata
            
        Returns:
            Path to saved file
        """
        file_path = self.plan_path / "app.md"
        
        # Write content
        file_path.write_text(content, encoding='utf-8')
        
        # Save metadata
        metadata_path = self.plan_path / "app.metadata.json"
        self._save_metadata(metadata_path, metadata)
        
        self.logger.info(f"Saved design to {file_path}")
        return file_path
        
    def save_feature(self, section_id: str, content: str, 
                    metadata: Dict[str, Any]) -> Path:
        """
        Save selected feature specification to plan directory.
        
        Args:
            section_id: Section identifier
            content: Feature specification content
            metadata: Feature metadata
            
        Returns:
            Path to saved file
        """
        # Generate filename based on section
        if section_id.replace('.', '').isdigit():
            # Numeric section
            filename = f"feat_{section_id.replace('.', '_')}.md"
        else:
            # Named section
            safe_name = section_id.replace(' ', '_').replace('-', '_').lower()
            filename = f"feat_{safe_name}.md"
            
        file_path = self.plan_path / filename
        
        # Write content
        file_path.write_text(content, encoding='utf-8')
        
        # Save metadata
        metadata_path = self.plan_path / f"{filename}.metadata.json"
        self._save_metadata(metadata_path, metadata)
        
        self.logger.info(f"Saved feature specification to {file_path}")
        return file_path
        
    def save_code(self, feat_specs: List[str], output_files: Dict[str, str],
                 metadata: Dict[str, Any]) -> Path:
        """
        Save generated code to appropriate directory structure.
        
        Args:
            feat_specs: Feature specifications used
            output_files: Generated files (relative_path -> content)
            metadata: Code generation metadata
            
        Returns:
            Path to code directory
        """
        # Create code directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        code_dir = self.base_path / "src" / f"generated_{timestamp}"
        code_dir.mkdir(parents=True, exist_ok=True)
        
        # Save all output files
        for rel_path, content in output_files.items():
            file_path = code_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                file_path.write_text(content, encoding='utf-8')
            except UnicodeEncodeError:
                # Handle binary files
                file_path.write_bytes(content.encode('utf-8', errors='replace'))
                
        # Save metadata
        metadata_path = code_dir / "generation.metadata.json"
        metadata['feat_specs'] = feat_specs
        metadata['generated_files'] = list(output_files.keys())
        self._save_metadata(metadata_path, metadata)
        
        self.logger.info(f"Saved generated code to {code_dir}")
        return code_dir
        
    def archive_candidates(self, task_type: str, candidates: List[Dict[str, Any]]) -> List[Path]:
        """
        Archive non-selected candidates with timestamp.
        
        Args:
            task_type: Type of task ('design', 'feat', 'dev')
            candidates: List of candidate results to archive
            
        Returns:
            List of archive paths
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_dir = self.archive_path / task_type / timestamp
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        archived_paths = []
        
        for i, candidate in enumerate(candidates):
            # Determine filename
            agent_name = candidate.get('agent_name', f'agent_{i}')
            if task_type == 'design':
                filename = f"app_{agent_name}.md"
            elif task_type == 'feat':
                section_id = candidate.get('section_id', 'unknown')
                filename = f"feat_{section_id}_{agent_name}.md"
            else:  # dev
                filename = f"code_{agent_name}"
                
            # Save candidate content
            if task_type == 'dev' and 'output_files' in candidate:
                # Archive code as directory
                code_archive_dir = archive_dir / filename
                code_archive_dir.mkdir(exist_ok=True)
                
                for rel_path, content in candidate['output_files'].items():
                    file_path = code_archive_dir / rel_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        file_path.write_text(content, encoding='utf-8')
                    except UnicodeEncodeError:
                        file_path.write_bytes(content.encode('utf-8', errors='replace'))
                        
                archived_paths.append(code_archive_dir)
            else:
                # Archive text content
                content = candidate.get('output', candidate.get('content', ''))
                file_path = archive_dir / filename
                file_path.write_text(content, encoding='utf-8')
                archived_paths.append(file_path)
                
            # Save candidate metadata
            metadata_path = archive_dir / f"{filename}.metadata.json"
            self._save_metadata(metadata_path, candidate)
            
        # Create archive index
        index_data = {
            'timestamp': timestamp,
            'task_type': task_type,
            'candidate_count': len(candidates),
            'archived_files': [str(p.relative_to(archive_dir)) for p in archived_paths]
        }
        
        index_path = archive_dir / "archive_index.json"
        self._save_metadata(index_path, index_data)
        
        self.logger.info(f"Archived {len(candidates)} {task_type} candidates to {archive_dir}")
        return archived_paths
        
    def load_app_md(self) -> Optional[str]:
        """Load current app.md content."""
        app_path = self.plan_path / "app.md"
        if app_path.exists():
            return app_path.read_text(encoding='utf-8')
        return None
        
    def load_feature_spec(self, section_id: str) -> Optional[str]:
        """Load feature specification content."""
        # Try to find feature file
        if section_id.replace('.', '').isdigit():
            filename = f"feat_{section_id.replace('.', '_')}.md"
        else:
            safe_name = section_id.replace(' ', '_').replace('-', '_').lower()
            filename = f"feat_{safe_name}.md"
            
        feat_path = self.plan_path / filename
        if feat_path.exists():
            return feat_path.read_text(encoding='utf-8')
            
        # Try alternative naming patterns
        for file_path in self.plan_path.glob("feat_*.md"):
            if section_id.lower() in file_path.stem.lower():
                return file_path.read_text(encoding='utf-8')
                
        return None
        
    def list_feature_specs(self) -> List[str]:
        """List available feature specifications."""
        specs = []
        for file_path in self.plan_path.glob("feat_*.md"):
            # Extract section identifier from filename
            stem = file_path.stem
            if stem.startswith("feat_"):
                section_id = stem[5:]  # Remove "feat_" prefix
                specs.append(section_id)
                
        return sorted(specs)
        
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        if self.temp_path.exists():
            for file_path in self.temp_path.iterdir():
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                    
        self.logger.info("Cleaned up temporary files")
        
    def get_archive_history(self, task_type: Optional[str] = None) -> List[ArchiveEntry]:
        """
        Get archive history, optionally filtered by task type.
        
        Args:
            task_type: Optional task type filter
            
        Returns:
            List of archive entries
        """
        entries = []
        
        search_path = self.archive_path
        if task_type:
            search_path = search_path / task_type
            
        if not search_path.exists():
            return entries
            
        for timestamp_dir in search_path.iterdir():
            if not timestamp_dir.is_dir():
                continue
                
            index_path = timestamp_dir / "archive_index.json"
            if index_path.exists():
                try:
                    index_data = json.loads(index_path.read_text())
                    
                    entry = ArchiveEntry(
                        timestamp=index_data['timestamp'],
                        task_type=index_data['task_type'],
                        agent_name='multiple',  # Archive contains multiple agents
                        success=True,  # Assume archived results were generated
                        metadata=index_data,
                        file_path=str(timestamp_dir)
                    )
                    entries.append(entry)
                    
                except (json.JSONDecodeError, KeyError):
                    continue
                    
        return sorted(entries, key=lambda x: x.timestamp, reverse=True)
        
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        def get_dir_size(path: Path) -> int:
            """Get total size of directory."""
            total = 0
            if path.exists():
                for file_path in path.rglob('*'):
                    if file_path.is_file():
                        try:
                            total += file_path.stat().st_size
                        except (OSError, FileNotFoundError):
                            pass
            return total
            
        return {
            'base_path': str(self.base_path),
            'total_size_bytes': get_dir_size(self.base_path),
            'plan_size_bytes': get_dir_size(self.plan_path),
            'archive_size_bytes': get_dir_size(self.archive_path),
            'plan_files': len(list(self.plan_path.glob('*'))) if self.plan_path.exists() else 0,
            'archive_entries': len(self.get_archive_history()),
            'has_app_md': (self.plan_path / "app.md").exists(),
            'feature_specs': len(self.list_feature_specs())
        }
        
    def _save_metadata(self, path: Path, metadata: Dict[str, Any]):
        """Save metadata to JSON file."""
        # Add timestamp if not present
        if 'timestamp' not in metadata:
            metadata['timestamp'] = datetime.now().isoformat()
            
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)


def main():
    """Test persistence manager functionality."""
    pm = PersistenceManager()
    
    print("Storage stats:")
    stats = pm.get_storage_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
        
    print(f"\nAvailable feature specs: {pm.list_feature_specs()}")
    
    print(f"\nArchive history:")
    history = pm.get_archive_history()
    for entry in history[:5]:  # Show last 5
        print(f"  {entry.timestamp}: {entry.task_type} ({entry.file_path})")


if __name__ == "__main__":
    main()