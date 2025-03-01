# AI Task Manager Scripts

This directory contains scripts for managing tasks in the AI Task Manager.

## Key Scripts

### Main Interface

- `task.sh`: Main entry point for all task operations. This script provides a unified command interface for all task management operations.

### Task Tracking

- `task-tracker.py`: Core script for tracking tasks and generating prompts
- `context-manager.py`: Manages the context cache for efficient prompt generation

### Task Workflow

- `complete-current-task.sh`: Marks the current task as completed
- `generate-next-task-prompt.sh`: Generates a prompt for the next task
- `next-task-for-claude.sh`: Formats task prompts for Claude
- `auto-complete-task.sh`: Completes the current task and displays the next task prompt
- `auto-task-workflow.sh`: Automates the entire task workflow with Claude

### Installation

- `install.sh`: Installs the AI Task Manager in a project

## Using the Scripts

### Basic Usage

```bash
# Show current task status
./task.sh status

# Complete the current task
./task.sh complete

# Generate the next task prompt
./task.sh next

# Prepare task for Claude (copies to clipboard)
./task.sh start

# Open Claude in browser with the task prompt
./task.sh start --browser

# Show help
./task.sh help
```

### Using Templates

```bash
# Use a specific template
./task.sh next --template detailed

# Available templates: default, concise, detailed
```

### Working with Sub-Tasks

```bash
# Complete a specific sub-task
./task.sh complete --sub-task "Sub-Task Name"

# Generate prompt for a specific sub-task
./task.sh next --sub-task "Sub-Task Name"
```

### Automating the Workflow

```bash
# Complete the current task and get the next task prompt
./auto-task-workflow.sh

# Use a different template
./auto-task-workflow.sh --template detailed

# Complete a specific sub-task
./auto-task-workflow.sh --sub-task "Sub-Task Name"
```

## Script Dependencies

- `task.sh` depends on all other scripts
- `complete-current-task.sh` depends on `task-tracker.py` and `context-manager.py`
- `generate-next-task-prompt.sh` depends on `task-tracker.py` and `context-manager.py`
- `auto-complete-task.sh` depends on `complete-current-task.sh` and `generate-next-task-prompt.sh`
- `auto-task-workflow.sh` depends on `task-tracker.py`, `generate-next-task-prompt.sh`, and `next-task-for-claude.sh`

## Customization

The scripts can be customized to fit your workflow:

- Edit `task.sh` to add new commands or modify existing ones
- Modify `task-tracker.py` to change how tasks are tracked
- Update `context-manager.py` to change how context is managed
- Edit `generate-next-task-prompt.sh` to change how prompts are generated
