#!/usr/bin/env python3

"""
Task Tracker for AI CI/CD Platform Project

This script helps track progress through the project plan and generates prompts
for the next task after each task is completed. It uses the context cache for
efficient prompt generation and supports hierarchical task structures.
"""

import os
import re
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Path to the project plan
PROJECT_PLAN_PATH = "docs/project-plan.md"
# Path to the task tracking data
TASK_TRACKING_PATH = "docs/task-tracking.json"
# Path to the context cache
CONTEXT_CACHE_PATH = "docs/context-cache.json"
# Path to the task prompt templates
PROMPT_TEMPLATES_PATH = "docs/templates/task-prompt-templates.json"

def ensure_directory_exists(file_path: str) -> None:
    """Ensure the directory for a file exists."""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

def load_project_plan() -> str:
    """Load the project plan from the markdown file."""
    with open(PROJECT_PLAN_PATH, 'r') as f:
        return f.read()

def load_task_tracking() -> Dict[str, Any]:
    """Load the task tracking data from the JSON file."""
    if os.path.exists(TASK_TRACKING_PATH):
        with open(TASK_TRACKING_PATH, 'r') as f:
            return json.load(f)
    else:
        # Initialize with default values
        return {
            "current_phase": "Self-Healing Debugger Enhancements",
            "current_task": "Improved Error Pattern Recognition",
            "parent_task": None,  # For hierarchical tasks
            "sub_tasks": [],      # For hierarchical tasks
            "completed_tasks": [],
            "last_updated": datetime.now().isoformat()
        }

def load_context_cache() -> Dict[str, Any]:
    """Load the context cache from the JSON file."""
    if os.path.exists(CONTEXT_CACHE_PATH):
        with open(CONTEXT_CACHE_PATH, 'r') as f:
            return json.load(f)
    else:
        # Initialize with default values
        return {
            "version": 1,
            "last_updated": datetime.now().isoformat(),
            "file_hashes": {},
            "project_structure": {},
            "architecture_summary": "",
            "completed_tasks_summary": [],
            "task_references": {}
        }

def load_prompt_templates() -> Dict[str, Any]:
    """Load the task prompt templates from the JSON file."""
    if os.path.exists(PROMPT_TEMPLATES_PATH):
        with open(PROMPT_TEMPLATES_PATH, 'r') as f:
            return json.load(f)
    else:
        # Create default templates
        templates = {
            "default": {
                "title": "# Next Task: {task_name} in {phase_name}\n\n",
                "description": "## Task Description\nThis task involves implementing the {task_name} feature for the {phase_name} component of the AI CI/CD Platform.\n\n",
                "steps": "## Steps to Complete\n{steps}\n\n",
                "testing": "## Testing Requirements\n- Ensure all tests pass\n- Add new tests for the implemented functionality\n- Verify integration with existing components\n\n",
                "documentation": "## Documentation\n- Update relevant README files\n- Update architecture diagrams if necessary\n- Update API documentation if applicable\n\n",
                "footer": "After completing this task, run the task-tracker.py script to mark it as completed and get the prompt for the next task.\n"
            },
            "concise": {
                "title": "# Task: {task_name}\n\n",
                "description": "Implement {task_name} for {phase_name}.\n\n",
                "steps": "## Steps\n{steps}\n\n",
                "testing": "## Testing\n- Write tests\n- Ensure integration\n\n",
                "documentation": "## Docs\n- Update as needed\n\n",
                "footer": "Run task-tracker.py when done.\n"
            },
            "detailed": {
                "title": "# Detailed Task: {task_name} in {phase_name}\n\n",
                "description": "## Task Description\nThis task involves implementing the {task_name} feature for the {phase_name} component of the AI CI/CD Platform.\n\n## Context\n{architecture_summary}\n\n## Recent Completed Tasks\n{recent_tasks}\n\n",
                "steps": "## Implementation Steps\n{steps}\n\n",
                "testing": "## Testing Requirements\n- Ensure all tests pass\n- Add new tests for the implemented functionality\n- Verify integration with existing components\n- Run regression tests\n\n",
                "documentation": "## Documentation Requirements\n- Update relevant README files\n- Update architecture diagrams if necessary\n- Update API documentation if applicable\n- Update user guides\n\n",
                "footer": "After completing this task, run the task-tracker.py script to mark it as completed and get the prompt for the next task.\n"
            }
        }
        
        # Create the directory if it doesn't exist
        ensure_directory_exists(PROMPT_TEMPLATES_PATH)
        
        # Save the default templates
        with open(PROMPT_TEMPLATES_PATH, 'w') as f:
            json.dump(templates, f, indent=2)
        
        return templates

def save_task_tracking(data: Dict[str, Any]) -> None:
    """Save the task tracking data to the JSON file."""
    with open(TASK_TRACKING_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def extract_tasks_from_plan(plan_text: str) -> Dict[str, Any]:
    """Extract all tasks from the project plan with support for hierarchical tasks."""
    phases = {}
    current_phase = None
    
    # Regular expression to match phase headers (### 1. Phase Name)
    phase_pattern = re.compile(r'###\s+\d+\.\s+(.*?)\s*$')
    
    # Regular expression to match task items (- **Task Name**: Description)
    task_pattern = re.compile(r'-\s+\*\*(.*?)\*\*:')
    
    # Regular expression to match task status (✅, 🔄, 📅)
    status_pattern = re.compile(r'\*\*Status:\s+(.*?)\*\*')
    
    # Regular expression to match sub-task items (  - **Sub-Task Name**: Description)
    subtask_pattern = re.compile(r'\s{2,}-\s+\*\*(.*?)\*\*:')
    
    lines = plan_text.split('\n')
    next_steps_section = False
    current_task = None
    
    for line in lines:
        # Check if this line is a phase header
        phase_match = phase_pattern.search(line)
        if phase_match:
            current_phase = phase_match.group(1)
            phases[current_phase] = {"tasks": [], "next_steps": []}
            next_steps_section = False  # Reset when entering a new phase
            current_task = None
            continue
        
        # Check if this line is a task item
        if current_phase:
            task_match = task_pattern.search(line)
            subtask_match = subtask_pattern.search(line)
            
            if task_match and not subtask_match:  # Main task
                task_name = task_match.group(1)
                # Check if the task has a status indicator
                status = "📅 Planned"  # Default status
                status_match = status_pattern.search(line)
                if status_match:
                    status = status_match.group(1)
                
                task_data = {
                    "name": task_name,
                    "status": status,
                    "line": line,
                    "sub_tasks": []
                }
                
                phases[current_phase]["tasks"].append(task_data)
                current_task = task_data
            
            elif subtask_match and current_task:  # Sub-task
                subtask_name = subtask_match.group(1)
                # Check if the subtask has a status indicator
                status = "📅 Planned"  # Default status
                status_match = status_pattern.search(line)
                if status_match:
                    status = status_match.group(1)
                
                current_task["sub_tasks"].append({
                    "name": subtask_name,
                    "status": status,
                    "line": line
                })
            
            # Check if this line is in the "Next Steps" section
            if "**Next Steps:**" in line or "Next Steps:" in line:
                next_steps_section = True
                continue
            
            if next_steps_section and line.strip().startswith(("1.", "- ")):
                # Extract the next step
                next_step = line.strip()
                if next_step.startswith("1.") or next_step.startswith("- "):
                    next_step = next_step[2:].strip()
                phases[current_phase]["next_steps"].append(next_step)
    
    return phases

def get_next_task(tracking_data: Dict[str, Any], phases: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], str]:
    """Determine the next task based on the current task and phase, supporting hierarchical tasks."""
    current_phase = tracking_data["current_phase"]
    current_task = tracking_data["current_task"]
    parent_task = tracking_data.get("parent_task")
    sub_tasks = tracking_data.get("sub_tasks", [])
    
    # If there are uncompleted sub-tasks, move to the next sub-task
    if sub_tasks and not all(sub_task.get("completed", False) for sub_task in sub_tasks):
        for i, sub_task in enumerate(sub_tasks):
            if not sub_task.get("completed", False):
                return current_phase, current_task, sub_task["name"], f"Next sub-task for {current_task}"
    
    # If the current phase doesn't exist in the phases, use the first phase
    if current_phase not in phases:
        current_phase = list(phases.keys())[0]
    
    # Get the tasks for the current phase
    phase_tasks = phases[current_phase]["tasks"]
    
    # Find the index of the current task
    current_task_index = -1
    for i, task in enumerate(phase_tasks):
        if task["name"] == current_task:
            current_task_index = i
            
            # Check if this task has sub-tasks that haven't been started yet
            if task.get("sub_tasks") and not parent_task:
                first_subtask = task["sub_tasks"][0]["name"]
                return current_phase, current_task, first_subtask, f"Starting sub-tasks for {current_task}"
            
            break
    
    # If the current task is not found or is the last task in the phase,
    # move to the next phase
    if current_task_index == -1 or current_task_index == len(phase_tasks) - 1:
        # Find the index of the current phase
        phase_keys = list(phases.keys())
        current_phase_index = phase_keys.index(current_phase)
        
        # If this is the last phase, we're done
        if current_phase_index == len(phase_keys) - 1:
            return None, None, None, "All tasks completed!"
        
        # Move to the next phase
        next_phase = phase_keys[current_phase_index + 1]
        next_task = phases[next_phase]["tasks"][0]["name"]
        
        # Check if the next task has sub-tasks
        next_task_data = phases[next_phase]["tasks"][0]
        if next_task_data.get("sub_tasks"):
            first_subtask = next_task_data["sub_tasks"][0]["name"]
            return next_phase, next_task, first_subtask, f"Moving to next phase: {next_phase}, starting with sub-tasks for {next_task}"
        
        return next_phase, next_task, None, f"Moving to next phase: {next_phase}"
    
    # Move to the next task in the current phase
    next_task = phase_tasks[current_task_index + 1]["name"]
    
    # Check if the next task has sub-tasks
    next_task_data = phase_tasks[current_task_index + 1]
    if next_task_data.get("sub_tasks"):
        first_subtask = next_task_data["sub_tasks"][0]["name"]
        return current_phase, next_task, first_subtask, f"Next task in {current_phase}, starting with sub-tasks for {next_task}"
    
    return current_phase, next_task, None, f"Next task in {current_phase}"

def mark_task_completed(tracking_data: Dict[str, Any], plan_text: str) -> str:
    """Mark the current task as completed in the project plan, supporting hierarchical tasks."""
    current_phase = tracking_data["current_phase"]
    current_task = tracking_data["current_task"]
    sub_task = tracking_data.get("sub_task")
    
    completion_time = datetime.now().isoformat()
    
    if sub_task:
        # Mark the sub-task as completed
        for i, st in enumerate(tracking_data.get("sub_tasks", [])):
            if st["name"] == sub_task:
                tracking_data["sub_tasks"][i]["completed"] = True
                tracking_data["sub_tasks"][i]["completed_at"] = completion_time
                break
        
        # Check if all sub-tasks are completed
        all_completed = all(st.get("completed", False) for st in tracking_data.get("sub_tasks", []))
        
        if all_completed:
            # Add the completed task to the list
            tracking_data["completed_tasks"].append({
                "phase": current_phase,
                "task": current_task,
                "sub_tasks": tracking_data.get("sub_tasks", []),
                "completed_at": completion_time
            })
            
            # Reset sub-tasks
            tracking_data["sub_tasks"] = []
            tracking_data["sub_task"] = None
        else:
            # Don't mark the main task as completed yet
            return plan_text
    else:
        # Add the completed task to the list
        tracking_data["completed_tasks"].append({
            "phase": current_phase,
            "task": current_task,
            "completed_at": completion_time
        })
    
    # Update the status in the project plan
    lines = plan_text.split('\n')
    for i, line in enumerate(lines):
        task_match = f"**{current_task}**:" in line
        subtask_match = sub_task and f"**{sub_task}**:" in line
        
        if (task_match or subtask_match) and current_phase in plan_text[:plan_text.find(line)]:
            # Replace the status indicator
            if "📅 Planned" in line:
                lines[i] = line.replace("📅 Planned", "✅ Completed")
            elif "🔄 In Progress" in line:
                lines[i] = line.replace("🔄 In Progress", "✅ Completed")
            else:
                # If no status indicator, add one
                lines[i] = line + " **Status: ✅ Completed**"
            
            # Only break if we found the right task/subtask
            if (task_match and not sub_task) or (subtask_match and sub_task):
                break
    
    updated_plan = '\n'.join(lines)
    
    # Save the updated project plan
    with open(PROJECT_PLAN_PATH, 'w') as f:
        f.write(updated_plan)
    
    # Update the context cache with the completed task
    update_context_cache(tracking_data)
    
    return updated_plan

def update_context_cache(tracking_data: Dict[str, Any]) -> None:
    """Update the context cache with the latest completed task information."""
    try:
        # Import the context manager module
        import sys
        sys.path.append('scripts')
        from context_manager import update_context_cache as update_cache
        
        # Update the cache
        update_cache()
    except ImportError:
        # If the context manager module is not available, update the cache manually
        cache = load_context_cache()
        
        # Update the completed tasks summary
        completed_tasks = tracking_data.get("completed_tasks", [])
        if completed_tasks:
            cache["completed_tasks_summary"] = completed_tasks[-5:]  # Keep only the 5 most recent tasks
        
        # Update the last updated timestamp
        cache["last_updated"] = datetime.now().isoformat()
        
        # Save the updated cache
        with open(CONTEXT_CACHE_PATH, 'w') as f:
            json.dump(cache, f, indent=2)

def generate_next_task_prompt(tracking_data: Dict[str, Any], phases: Dict[str, Any], template_name: str = "default", specific_sub_task: Optional[str] = None) -> str:
    """Generate a prompt for the next task using the specified template and context cache.
    
    This optimized version creates more concise prompts with only task-relevant information
    and leverages the context cache for persistent project information.
    
    Args:
        tracking_data: The task tracking data
        phases: The phases extracted from the project plan
        template_name: The name of the template to use
        specific_sub_task: If provided, generate a prompt for this specific sub-task
    """
    current_phase = tracking_data["current_phase"]
    current_task = tracking_data["current_task"]
    sub_task = specific_sub_task if specific_sub_task else tracking_data.get("sub_task")
    
    # Load the prompt templates
    templates = load_prompt_templates()
    
    # Use the specified template or fall back to default
    template = templates.get(template_name, templates["default"])
    
    # Get the task name (use sub-task if available)
    task_name = sub_task if sub_task else current_task
    
    # Get the next steps for the current phase
    if current_phase in phases and "next_steps" in phases[current_phase]:
        next_steps = phases[current_phase]["next_steps"]
    else:
        next_steps = []
    
    # Format the steps
    steps_text = ""
    if next_steps:
        for i, step in enumerate(next_steps):
            steps_text += f"{i+1}. {step}\n"
    else:
        steps_text += "1. Review the project plan for detailed steps\n"
        steps_text += "2. Implement the necessary changes\n"
        steps_text += "3. Write tests for the new functionality\n"
        steps_text += "4. Update documentation\n"
    
    # Load the context cache for additional information
    cache = load_context_cache()
    
    # Get the architecture summary from the cache - only include if using detailed template
    architecture_summary = ""
    if template_name == "detailed":
        architecture_summary = cache.get("architecture_summary", "")
    
    # Get the recent completed tasks from the cache - only include if using detailed template
    recent_tasks = ""
    if template_name == "detailed":
        recent_tasks_list = cache.get("completed_tasks_summary", [])
        for i, task in enumerate(recent_tasks_list):
            recent_tasks += f"{i+1}. {task.get('task')} in {task.get('phase')}\n"
    
    # Build the prompt using the template
    prompt = ""
    prompt += template["title"].format(task_name=task_name, phase_name=current_phase)
    prompt += template["description"].format(
        task_name=task_name, 
        phase_name=current_phase,
        architecture_summary=architecture_summary,
        recent_tasks=recent_tasks
    )
    prompt += template["steps"].format(steps=steps_text)
    prompt += template["testing"]
    prompt += template["documentation"]
    prompt += template["footer"]
    
    return prompt

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Task Tracker for AI CI/CD Platform Project")
    parser.add_argument('--complete', action='store_true', help="Mark the current task as completed")
    parser.add_argument('--next', action='store_true', help="Get the prompt for the next task")
    parser.add_argument('--status', action='store_true', help="Show the current task status")
    parser.add_argument('--template', type=str, default="default", help="Template to use for task prompt (default, concise, detailed)")
    parser.add_argument('--sub-task', type=str, help="Specify a sub-task name when completing a task")
    args = parser.parse_args()
    
    # Load the project plan and task tracking data
    plan_text = load_project_plan()
    tracking_data = load_task_tracking()
    
    # Extract tasks from the project plan
    phases = extract_tasks_from_plan(plan_text)
    
    if args.complete:
        # If a sub-task is specified, update the tracking data
        if args.sub_task:
            tracking_data["sub_task"] = args.sub_task
        
        # Mark the current task as completed
        updated_plan = mark_task_completed(tracking_data, plan_text)
        
        # Determine the next task
        next_phase, next_task, next_subtask, message = get_next_task(tracking_data, phases)
        
        if next_phase and next_task:
            # Update the tracking data
            tracking_data["current_phase"] = next_phase
            tracking_data["current_task"] = next_task
            tracking_data["sub_task"] = next_subtask
            tracking_data["last_updated"] = datetime.now().isoformat()
            
            # Save the updated tracking data
            save_task_tracking(tracking_data)
            
            print(f"Task '{tracking_data['current_task']}' marked as completed.")
            print(message)
            
            if next_subtask:
                print(f"Next task: {next_task} in {next_phase}, sub-task: {next_subtask}")
            else:
                print(f"Next task: {next_task} in {next_phase}")
        else:
            print("All tasks completed!")
    
    elif args.next:
        # Generate the prompt for the next task
        prompt = generate_next_task_prompt(tracking_data, phases, args.template, args.sub_task)
        print(prompt)
    
    elif args.status:
        # Show the current task status
        print(f"Current Phase: {tracking_data['current_phase']}")
        print(f"Current Task: {tracking_data['current_task']}")
        if tracking_data.get("sub_task"):
            print(f"Current Sub-Task: {tracking_data['sub_task']}")
        print(f"Last Updated: {tracking_data['last_updated']}")
        print(f"Completed Tasks: {len(tracking_data['completed_tasks'])}")
    
    else:
        # Show usage
        parser.print_help()

if __name__ == "__main__":
    main()
