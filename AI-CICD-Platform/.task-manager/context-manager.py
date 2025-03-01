#!/usr/bin/env python3

"""
Context Manager for AI CI/CD Platform Project

This script manages the context cache for the project, storing persistent information
about the project structure, architecture, and completed tasks. It provides an efficient
way to access this information without having to include it directly in task prompts.
"""

import argparse
import json
import os
import sys
import hashlib
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Constants
CONTEXT_CACHE_FILE = "docs/context-cache.json"
PROJECT_PLAN_FILE = "docs/project-plan.md"
TASK_TRACKING_FILE = "docs/task-tracking.json"
ARCHITECTURE_FILE = "docs/architecture.md"
CACHE_VERSION = 2  # Increment when making structural changes to the cache

def ensure_directory_exists(file_path: str) -> None:
    """Ensure the directory for a file exists."""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

def md5_hash_file(file_path: str) -> Optional[str]:
    """Generate MD5 hash for a file."""
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def get_project_structure(root_dir: str = '.', max_depth: Optional[int] = None, current_depth: int = 0) -> Dict[str, Any]:
    """Recursively scan the project directory and count files."""
    result = {}
    
    try:
        for item in os.listdir(root_dir):
            # Skip hidden files and directories
            if item.startswith('.') and item != '.github':
                continue
                
            path = os.path.join(root_dir, item)
            
            if os.path.isdir(path):
                if max_depth is None or current_depth < max_depth:
                    result[item] = get_project_structure(path, max_depth, current_depth + 1)
                else:
                    # Just count files at max depth
                    file_count = sum(1 for _ in Path(path).glob('**/*') if _.is_file())
                    result[item] = {"_files": file_count}
            else:
                # Count this file in the parent directory
                if "_files" not in result:
                    result["_files"] = 0
                result["_files"] += 1
    except PermissionError:
        # Handle permission errors gracefully
        return {"_files": 0, "_error": "Permission denied"}
    except Exception as e:
        # Handle other errors
        return {"_files": 0, "_error": str(e)}
        
    return result

def extract_architecture_summary(file_path: str) -> str:
    """Extract architecture summary from architecture.md file."""
    if not os.path.exists(file_path):
        return "Architecture information not available."
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract the service descriptions section
    if "## Service Descriptions" in content:
        start = content.find("## Service Descriptions")
        end = content.find("##", start + 1)
        if end == -1:  # If there's no next section
            end = len(content)
        return content[start:end].strip()
    
    return "Service descriptions not found in architecture file."

def get_completed_tasks(file_path: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get the most recent completed tasks from task-tracking.json."""
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    completed_tasks = []
    
    if "completed_tasks" in data:
        for task in data["completed_tasks"]:
            # Store only essential information to keep the cache concise
            completed_tasks.append({
                "phase": task["phase"],
                "task": task["task"],
                "completed_at": task["completed_at"]
            })
    
    # Sort by completion date (newest first) and limit
    completed_tasks.sort(key=lambda x: x["completed_at"], reverse=True)
    return completed_tasks[:limit]

def load_existing_cache() -> Dict[str, Any]:
    """Load the existing context cache if available."""
    if os.path.exists(CONTEXT_CACHE_FILE):
        try:
            with open(CONTEXT_CACHE_FILE, 'r') as f:
                cache = json.load(f)
                
                # Check if the cache version matches
                if cache.get("version") != CACHE_VERSION:
                    # Version mismatch, return a new cache
                    return {
                        "version": CACHE_VERSION,
                        "last_updated": datetime.datetime.now().isoformat(),
                        "file_hashes": {},
                        "project_structure": {},
                        "architecture_summary": "",
                        "completed_tasks_summary": [],
                        "task_references": {}
                    }
                
                return cache
        except (json.JSONDecodeError, IOError):
            # If there's an error reading the cache, return a new one
            pass
    
    # Return a new cache if the file doesn't exist or there was an error
    return {
        "version": CACHE_VERSION,
        "last_updated": datetime.datetime.now().isoformat(),
        "file_hashes": {},
        "project_structure": {},
        "architecture_summary": "",
        "completed_tasks_summary": [],
        "task_references": {}
    }

def update_context_cache(debug: bool = False) -> Dict[str, Any]:
    """Update the context cache with the latest project information."""
    # Load the existing cache
    cache = load_existing_cache()
    
    # Check if the tracked files have changed
    files_changed = False
    for file_path in [PROJECT_PLAN_FILE, TASK_TRACKING_FILE, ARCHITECTURE_FILE]:
        hash_value = md5_hash_file(file_path)
        if hash_value:
            if file_path not in cache["file_hashes"] or cache["file_hashes"][file_path] != hash_value:
                cache["file_hashes"][file_path] = hash_value
                files_changed = True
    
    # Only update the cache if files have changed or it's a new cache
    if files_changed or not cache.get("project_structure"):
        # Get project structure (limit depth for performance)
        cache["project_structure"] = get_project_structure(max_depth=10)
        
        # Extract architecture summary
        cache["architecture_summary"] = extract_architecture_summary(ARCHITECTURE_FILE)
        
        # Get completed tasks
        cache["completed_tasks_summary"] = get_completed_tasks(TASK_TRACKING_FILE)
        
        # Add task references
        if os.path.exists(TASK_TRACKING_FILE):
            with open(TASK_TRACKING_FILE, 'r') as f:
                task_data = json.load(f)
                if "tasks" in task_data:
                    cache["task_references"] = task_data["tasks"]
        
        # Update the last updated timestamp
        cache["last_updated"] = datetime.datetime.now().isoformat()
        
        # Ensure the directory exists
        ensure_directory_exists(CONTEXT_CACHE_FILE)
        
        # Write to cache file
        with open(CONTEXT_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
        
        if debug:
            print(f"Context cache updated with:")
            print(f"- {len(cache['file_hashes'])} tracked files")
            print(f"- Project structure with {sum(1 for _ in Path('.').glob('**/*') if _.is_file())} files")
            print(f"- Architecture summary ({len(cache['architecture_summary'])} chars)")
            print(f"- {len(cache['completed_tasks_summary'])} recent completed tasks")
        else:
            print(f"Context cache updated at {cache['last_updated']}")
    else:
        if debug:
            print("No changes detected in tracked files, using existing cache.")
        else:
            print(f"Context cache is up to date (last updated: {cache['last_updated']})")
    
    return cache

def get_task_context(task_name: Optional[str] = None, phase_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get context for a specific task."""
    if not os.path.exists(CONTEXT_CACHE_FILE):
        print("Context cache not found. Run with --update first.")
        return None
    
    with open(CONTEXT_CACHE_FILE, 'r') as f:
        cache = json.load(f)
    
    # If no task specified, get current task from task-tracking.json
    if not task_name or not phase_name:
        if os.path.exists(TASK_TRACKING_FILE):
            with open(TASK_TRACKING_FILE, 'r') as f:
                task_data = json.load(f)
                task_name = task_data.get("current_task")
                phase_name = task_data.get("current_phase")
        else:
            print("Task tracking file not found and no task specified.")
            return None
    
    # Get task-specific context
    context = {
        "task_name": task_name,
        "phase_name": phase_name,
        "architecture_summary": cache.get("architecture_summary", ""),
        "recent_tasks": "\n".join([
            f"{i+1}. {task['task']} in {task['phase']}"
            for i, task in enumerate(cache.get("completed_tasks_summary", []))
        ]),
    }
    
    # Add task-specific information if available
    if "task_references" in cache and task_name in cache["task_references"]:
        task_info = cache["task_references"][task_name]
        context.update(task_info)
    
    return context

def main():
    parser = argparse.ArgumentParser(description="Manage context cache for AI CI/CD Platform")
    parser.add_argument("--update", action="store_true", help="Update the context cache")
    parser.add_argument("--get-task-context", action="store_true", help="Get context for a task")
    parser.add_argument("--task", help="Task name for context retrieval")
    parser.add_argument("--phase", help="Phase name for context retrieval")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--force", action="store_true", help="Force update even if no changes detected")
    
    args = parser.parse_args()
    
    if args.update:
        update_context_cache(debug=args.debug)
    elif args.get_task_context:
        context = get_task_context(args.task, args.phase)
        if context:
            print(json.dumps(context, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
