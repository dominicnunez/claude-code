#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dateutil",
# ]
# ///

"""
Archive completed tasks from todo.md to timestamped files on commit.

This hook runs before commits to:
1. Find completed tasks in todo.md (searching for "Completed" sections)
2. Archive them to appropriate .docs/change-log/YYYY-MM-DD_HH-MM.md
3. Update todo.md to remove completed tasks
4. Stage the changes for commit
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
import subprocess
import re


def find_todo_file():
    """Find todo.md in back/.docs or front/.docs."""
    current = Path.cwd()
    
    # Navigate up to find project root (where .git exists)
    project_root = current
    while project_root != Path("/") and project_root != Path.home():
        if (project_root / ".git").exists():
            break
        project_root = project_root.parent
    
    # Check back and front .docs folders only
    possible_locations = [
        project_root / "back" / ".docs" / "todo.md",  # Backend .docs
        project_root / "front" / ".docs" / "todo.md", # Frontend .docs
    ]
    
    for location in possible_locations:
        if location.exists():
            return location
    
    return None


def parse_todo_file(file_path):
    """Parse todo.md to extract pending and completed tasks."""
    pending_tasks = []
    completed_tasks = []
    other_content = []
    
    if not file_path.exists():
        return pending_tasks, completed_tasks, other_content
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    current_section = None
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Detect sections - look for "Completed" anywhere in a header
        if line.strip().startswith("#") and "completed" in line.lower():
            current_section = "completed"
            other_content.append(line)  # Keep the header for reference
        elif line.strip().startswith("#"):
            # Any other header ends the completed section
            current_section = None
            other_content.append(line)
        elif current_section == "completed":
            # In completed section - collect task lines
            if line.strip().startswith("- ") or line.strip().startswith("* ") or line.strip().startswith("+ "):
                completed_tasks.append(line)
            elif line.strip():  # Non-empty, non-task line
                other_content.append(line)
        else:
            # Everything else is kept as-is (including pending tasks)
            if not (line.strip().startswith("- ") and any(comp in line for comp in completed_tasks)):
                pending_tasks.append(line)
        
        i += 1
    
    return pending_tasks, completed_tasks, other_content


def detect_changed_area():
    """Detect if changes are in /back or /front based on git diff."""
    try:
        # Get list of staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, check=True
        )
        changed_files = result.stdout.strip().split('\n')
        
        has_back = any('/back/' in f or f.startswith('back/') for f in changed_files)
        has_front = any('/front/' in f or f.startswith('front/') for f in changed_files)
        
        # Return the area with changes, defaulting to 'back' if both or neither
        if has_front and not has_back:
            return 'front'
        else:
            return 'back'  # Default to back for backend-heavy projects
            
    except:
        return 'back'  # Default fallback


def get_archive_directory(todo_file):
    """Archive to the same area's change-log directory where todo.md is located."""
    todo_path = str(todo_file)
    
    # Simply archive to the same area where todo.md exists
    if "/back/.docs/" in todo_path:
        # todo.md is in backend .docs -> archive to backend change-log
        return todo_file.parent / "change-log"
    elif "/front/.docs/" in todo_path:
        # todo.md is in frontend .docs -> archive to frontend change-log
        return todo_file.parent / "change-log"
    
    # Should not happen based on find_todo_file logic
    return None


def get_git_changes():
    """Get summary of changes being committed."""
    try:
        # Get staged changes
        staged = subprocess.run(
            ["git", "diff", "--cached", "--stat"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
        
        # Get list of changed files with more detail
        files_changed = subprocess.run(
            ["git", "diff", "--cached", "--name-status"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
        
        # Get commit message if available
        commit_msg = ""
        if os.path.exists(".git/COMMIT_EDITMSG"):
            with open(".git/COMMIT_EDITMSG", 'r') as f:
                commit_msg = f.read().strip()
        
        return staged, files_changed, commit_msg
    except:
        return "", "", ""


def archive_completed_tasks(todo_file, completed_tasks):
    """Archive completed tasks to timestamped file in appropriate change-log directory."""
    if not completed_tasks:
        return None
    
    # Determine archive directory based on project structure
    archive_dir = get_archive_directory(todo_file)
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    archive_file = archive_dir / f"{timestamp}.md"
    
    # Get git changes for context
    staged_changes, files_changed, commit_msg = get_git_changes()
    
    # Detect which area this is for
    area = "Backend" if "/back/" in str(archive_dir) else "Frontend" if "/front/" in str(archive_dir) else "General"
    
    # Write archive file
    with open(archive_file, 'w') as f:
        f.write(f"# Change Log - {area}\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Project:** {todo_file.parent.name}\n")
        f.write(f"**Area:** {area}\n\n")
        
        if commit_msg:
            f.write(f"## Commit Message\n```\n{commit_msg}\n```\n\n")
        
        if files_changed:
            f.write(f"## Files Changed\n```\n{files_changed}\n```\n\n")
        
        if staged_changes:
            f.write(f"## Changes Summary\n```\n{staged_changes}\n```\n\n")
        
        f.write(f"## Completed Tasks\n\n")
        for task in completed_tasks:
            f.write(task)
        
        f.write(f"\n---\n")
        f.write(f"*Archived automatically by Claude Code task archiver*\n")
    
    return archive_file


def update_todo_file(todo_file, pending_content):
    """Update todo.md to remove completed tasks while preserving structure."""
    with open(todo_file, 'w') as f:
        for line in pending_content:
            f.write(line)


def main():
    # Find todo.md
    todo_file = find_todo_file()
    if not todo_file:
        # No todo.md, nothing to archive
        sys.exit(0)
    
    # Parse tasks
    pending_content, completed_tasks, other_content = parse_todo_file(todo_file)
    
    if not completed_tasks:
        # No completed tasks to archive
        sys.exit(0)
    
    try:
        # Archive completed tasks
        archive_file = archive_completed_tasks(todo_file, completed_tasks)
        
        if archive_file:
            # Update todo.md to remove completed tasks
            # Keep pending content and non-completed sections
            update_todo_file(todo_file, pending_content)
            
            # Stage the changes
            subprocess.run(["git", "add", str(todo_file)], check=True)
            subprocess.run(["git", "add", str(archive_file)], check=True)
            
            area = "Backend" if "/back/" in str(archive_file) else "Frontend" if "/front/" in str(archive_file) else "Project"
            print(f"✓ Archived {len(completed_tasks)} completed tasks to {area} change log: {archive_file.name}")
        
    except Exception as e:
        print(f"Warning: Could not archive completed tasks: {e}", file=sys.stderr)
        # Don't block the commit
        sys.exit(0)


if __name__ == "__main__":
    main()