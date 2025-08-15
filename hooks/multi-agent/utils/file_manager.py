#!/usr/bin/env python3
"""
File manager utility for multi-agent orchestration system.
Handles file operations, temporary file management, and cleanup.
"""

import os
import shutil
import tempfile
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from contextlib import contextmanager
import logging
import time


class FileManager:
    """Manages file operations and cleanup for multi-agent orchestration."""
    
    def __init__(self, base_temp_dir: Optional[str] = None):
        """Initialize file manager."""
        self.base_temp_dir = base_temp_dir or tempfile.gettempdir()
        self.temp_dirs: Set[Path] = set()
        self.temp_files: Set[Path] = set()
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for file manager."""
        logger = logging.getLogger('file_manager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    @contextmanager
    def temp_directory(self, prefix: str = "claude_multi_agent_"):
        """
        Context manager for temporary directory creation and cleanup.
        
        Args:
            prefix: Prefix for temporary directory name
            
        Yields:
            Path to temporary directory
        """
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=self.base_temp_dir))
        self.temp_dirs.add(temp_dir)
        
        try:
            self.logger.debug(f"Created temporary directory: {temp_dir}")
            yield temp_dir
        finally:
            self.cleanup_directory(temp_dir)
            self.temp_dirs.discard(temp_dir)
            
    @contextmanager
    def temp_file(self, suffix: str = "", prefix: str = "claude_", 
                  content: Optional[str] = None, mode: str = 'w'):
        """
        Context manager for temporary file creation and cleanup.
        
        Args:
            suffix: File suffix/extension
            prefix: File name prefix
            content: Initial file content
            mode: File open mode
            
        Yields:
            Path to temporary file
        """
        with tempfile.NamedTemporaryFile(
            mode=mode, suffix=suffix, prefix=prefix, 
            dir=self.base_temp_dir, delete=False
        ) as temp_file:
            if content:
                temp_file.write(content)
                temp_file.flush()
                
            temp_path = Path(temp_file.name)
            self.temp_files.add(temp_path)
            
        try:
            self.logger.debug(f"Created temporary file: {temp_path}")
            yield temp_path
        finally:
            self.cleanup_file(temp_path)
            self.temp_files.discard(temp_path)
            
    def create_agent_workspace(self, agent_name: str, task_id: str, 
                              input_files: Optional[Dict[str, str]] = None) -> Path:
        """
        Create isolated workspace for an agent task.
        
        Args:
            agent_name: Name of the agent
            task_id: Unique task identifier
            input_files: Dictionary of filename -> content
            
        Returns:
            Path to agent workspace directory
        """
        workspace_name = f"agent_{agent_name}_{task_id}_{int(time.time())}"
        workspace_dir = Path(self.base_temp_dir) / workspace_name
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        self.temp_dirs.add(workspace_dir)
        
        # Create input files if provided
        if input_files:
            for filename, content in input_files.items():
                file_path = workspace_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    file_path.write_text(content, encoding='utf-8')
                except UnicodeEncodeError:
                    # Handle binary content
                    file_path.write_bytes(content.encode('utf-8', errors='replace'))
                    
        self.logger.info(f"Created agent workspace: {workspace_dir}")
        return workspace_dir
        
    def collect_output_files(self, workspace_dir: Path, 
                           exclude_patterns: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Collect output files from agent workspace.
        
        Args:
            workspace_dir: Path to workspace directory
            exclude_patterns: List of patterns to exclude
            
        Returns:
            Dictionary of relative_path -> content
        """
        output_files = {}
        exclude_patterns = exclude_patterns or [
            '*.pyc', '__pycache__', '.git', '.DS_Store', 'node_modules'
        ]
        
        if not workspace_dir.exists():
            return output_files
            
        for file_path in workspace_dir.rglob('*'):
            if file_path.is_file():
                # Check exclusion patterns
                should_exclude = False
                for pattern in exclude_patterns:
                    if file_path.match(pattern) or pattern in str(file_path):
                        should_exclude = True
                        break
                        
                if should_exclude:
                    continue
                    
                try:
                    rel_path = file_path.relative_to(workspace_dir)
                    content = file_path.read_text(encoding='utf-8')
                    output_files[str(rel_path)] = content
                except (UnicodeDecodeError, PermissionError):
                    # Skip files we can't read as text
                    self.logger.debug(f"Skipping binary/unreadable file: {rel_path}")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error reading file {rel_path}: {e}")
                    continue
                    
        self.logger.info(f"Collected {len(output_files)} output files from {workspace_dir}")
        return output_files
        
    def save_files_to_directory(self, files: Dict[str, str], target_dir: Path) -> List[Path]:
        """
        Save files from dictionary to target directory.
        
        Args:
            files: Dictionary of relative_path -> content
            target_dir: Target directory
            
        Returns:
            List of created file paths
        """
        created_files = []
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for rel_path, content in files.items():
            file_path = target_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                file_path.write_text(content, encoding='utf-8')
                created_files.append(file_path)
            except UnicodeEncodeError:
                # Handle binary content
                file_path.write_bytes(content.encode('utf-8', errors='replace'))
                created_files.append(file_path)
            except Exception as e:
                self.logger.error(f"Failed to save file {rel_path}: {e}")
                
        self.logger.info(f"Saved {len(created_files)} files to {target_dir}")
        return created_files
        
    def copy_directory(self, source: Path, destination: Path, 
                      exclude_patterns: Optional[List[str]] = None) -> bool:
        """
        Copy directory with optional exclusion patterns.
        
        Args:
            source: Source directory
            destination: Destination directory
            exclude_patterns: Patterns to exclude
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if destination.exists():
                shutil.rmtree(destination)
                
            # Use shutil.copytree with ignore patterns
            def ignore_patterns(directory, contents):
                ignored = []
                if exclude_patterns:
                    for item in contents:
                        for pattern in exclude_patterns:
                            if item == pattern or item.endswith(pattern):
                                ignored.append(item)
                                break
                return ignored
                
            shutil.copytree(source, destination, ignore=ignore_patterns)
            self.logger.info(f"Copied directory from {source} to {destination}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy directory: {e}")
            return False
            
    def calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """
        Calculate SHA-256 hash of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex digest of SHA-256 hash, or None if error
        """
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return None
            
    def calculate_content_hash(self, content: str) -> str:
        """
        Calculate SHA-256 hash of content string.
        
        Args:
            content: Content to hash
            
        Returns:
            Hex digest of SHA-256 hash
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
        
    def find_duplicate_files(self, directory: Path) -> Dict[str, List[Path]]:
        """
        Find duplicate files in directory by content hash.
        
        Args:
            directory: Directory to search
            
        Returns:
            Dictionary of hash -> list of duplicate file paths
        """
        hash_to_files = {}
        
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                file_hash = self.calculate_file_hash(file_path)
                if file_hash:
                    if file_hash not in hash_to_files:
                        hash_to_files[file_hash] = []
                    hash_to_files[file_hash].append(file_path)
                    
        # Return only hashes with multiple files
        duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
        
        if duplicates:
            self.logger.info(f"Found {len(duplicates)} sets of duplicate files")
            
        return duplicates
        
    def get_directory_size(self, directory: Path) -> int:
        """
        Calculate total size of directory in bytes.
        
        Args:
            directory: Directory to measure
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, FileNotFoundError):
                        pass
        except Exception as e:
            self.logger.error(f"Error calculating directory size: {e}")
            
        return total_size
        
    def cleanup_file(self, file_path: Path) -> bool:
        """
        Clean up a single file.
        
        Args:
            file_path: Path to file to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if file_path.exists():
                file_path.unlink()
                self.logger.debug(f"Cleaned up file: {file_path}")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to cleanup file {file_path}: {e}")
            return False
            
    def cleanup_directory(self, directory: Path) -> bool:
        """
        Clean up a directory and all its contents.
        
        Args:
            directory: Path to directory to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if directory.exists() and directory.is_dir():
                shutil.rmtree(directory)
                self.logger.debug(f"Cleaned up directory: {directory}")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to cleanup directory {directory}: {e}")
            return False
            
    def cleanup_all(self) -> None:
        """Clean up all tracked temporary files and directories."""
        cleaned_files = 0
        cleaned_dirs = 0
        
        # Clean up temporary files
        for file_path in list(self.temp_files):
            if self.cleanup_file(file_path):
                cleaned_files += 1
            self.temp_files.discard(file_path)
            
        # Clean up temporary directories
        for dir_path in list(self.temp_dirs):
            if self.cleanup_directory(dir_path):
                cleaned_dirs += 1
            self.temp_dirs.discard(dir_path)
            
        if cleaned_files > 0 or cleaned_dirs > 0:
            self.logger.info(f"Cleaned up {cleaned_files} files and {cleaned_dirs} directories")
            
    def get_temp_usage_stats(self) -> Dict[str, Any]:
        """Get statistics about temporary file usage."""
        total_files = len(self.temp_files)
        total_dirs = len(self.temp_dirs)
        
        total_size = 0
        for file_path in self.temp_files:
            if file_path.exists():
                try:
                    total_size += file_path.stat().st_size
                except (OSError, FileNotFoundError):
                    pass
                    
        for dir_path in self.temp_dirs:
            total_size += self.get_directory_size(dir_path)
            
        return {
            'temp_files': total_files,
            'temp_directories': total_dirs,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024)
        }
        
    def __del__(self):
        """Cleanup on destruction."""
        self.cleanup_all()


# Global file manager instance
_global_file_manager = None


def get_file_manager() -> FileManager:
    """Get global file manager instance."""
    global _global_file_manager
    if _global_file_manager is None:
        _global_file_manager = FileManager()
    return _global_file_manager


def cleanup_global_file_manager():
    """Cleanup global file manager."""
    global _global_file_manager
    if _global_file_manager is not None:
        _global_file_manager.cleanup_all()
        _global_file_manager = None


def main():
    """Test file manager functionality."""
    fm = FileManager()
    
    print("Testing file manager...")
    
    # Test temporary directory
    with fm.temp_directory("test_") as temp_dir:
        print(f"Created temp directory: {temp_dir}")
        
        # Create some test files
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, world!")
        
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("Nested content")
        
        # Collect files
        files = fm.collect_output_files(temp_dir)
        print(f"Collected files: {list(files.keys())}")
        
        # Test directory size
        size = fm.get_directory_size(temp_dir)
        print(f"Directory size: {size} bytes")
        
    # Test agent workspace
    workspace = fm.create_agent_workspace(
        "test_agent", 
        "task_123",
        {"input.txt": "Input content", "config.json": '{"test": true}'}
    )
    
    try:
        print(f"Created agent workspace: {workspace}")
        
        # Simulate some output
        (workspace / "output.txt").write_text("Generated output")
        
        # Collect output
        output_files = fm.collect_output_files(workspace)
        print(f"Agent output files: {list(output_files.keys())}")
        
    finally:
        fm.cleanup_directory(workspace)
        
    # Show usage stats
    stats = fm.get_temp_usage_stats()
    print(f"Temp usage stats: {stats}")
    
    # Cleanup
    fm.cleanup_all()
    print("File manager test completed")


if __name__ == "__main__":
    main()