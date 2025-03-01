#!/bin/bash

# AI Task Manager Installation Script
# This script installs the AI Task Manager in a project

# Set up colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}AI Task Manager - Installation${NC}"

# Get target directory
if [ -z "$1" ]; then
  read -p "Enter target project directory (or press Enter for current directory): " TARGET_DIR
  TARGET_DIR=${TARGET_DIR:-$(pwd)}
else
  TARGET_DIR=$1
fi

# Create task manager directory
TASK_DIR="$TARGET_DIR/.task-manager"
mkdir -p "$TASK_DIR"
echo -e "${GREEN}Created task manager directory: $TASK_DIR${NC}"

# Get source directory (where this script is located)
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SOURCE_DIR")"

# Copy scripts
cp -r "$SOURCE_DIR"/* "$TASK_DIR/"
chmod +x "$TASK_DIR/"*.sh
echo -e "${GREEN}Copied task management scripts${NC}"

# Create docs directory
mkdir -p "$TARGET_DIR/docs/templates"
if [ -d "$REPO_ROOT/docs/templates" ]; then
  cp -r "$REPO_ROOT/docs/templates"/* "$TARGET_DIR/docs/templates/"
  echo -e "${GREEN}Copied task templates${NC}"
else
  echo -e "${YELLOW}Warning: Templates directory not found. Creating default templates.${NC}"
  # Create default templates if they don't exist
  mkdir -p "$TARGET_DIR/docs/templates"
  echo '{
  "default": {
    "title": "# Next Task: {task_name} in {phase_name}\n\n",
    "description": "## Task Description\nThis task involves implementing the {task_name} feature for the {phase_name} component.\n\n",
    "steps": "## Steps to Complete\n{steps}\n\n",
    "testing": "## Testing Requirements\n- Ensure all tests pass\n- Add new tests for the implemented functionality\n- Verify integration with existing components\n\n",
    "documentation": "## Documentation\n- Update relevant README files\n- Update architecture diagrams if necessary\n- Update API documentation if applicable\n\n",
    "footer": "After completing this task, run the task command to mark it as completed and get the prompt for the next task.\n"
  },
  "concise": {
    "title": "# Task: {task_name}\n\n",
    "description": "Implement {task_name} for {phase_name}.\n\n",
    "steps": "## Steps\n{steps}\n\n",
    "testing": "## Testing\n- Write tests\n- Ensure integration\n\n",
    "documentation": "## Docs\n- Update as needed\n\n",
    "footer": "Run task command when done.\n"
  },
  "detailed": {
    "title": "# Detailed Task: {task_name} in {phase_name}\n\n",
    "description": "## Task Description\nThis task involves implementing the {task_name} feature for the {phase_name} component.\n\n## Context\n{architecture_summary}\n\n## Recent Completed Tasks\n{recent_tasks}\n\n",
    "steps": "## Implementation Steps\n{steps}\n\n",
    "testing": "## Testing Requirements\n- Ensure all tests pass\n- Add new tests for the implemented functionality\n- Verify integration with existing components\n- Run regression tests\n\n",
    "documentation": "## Documentation Requirements\n- Update relevant README files\n- Update architecture diagrams if necessary\n- Update API documentation if applicable\n- Update user guides\n\n",
    "footer": "After completing this task, run the task command to mark it as completed and get the prompt for the next task.\n"
  }
}' > "$TARGET_DIR/docs/templates/task-prompt-templates.json"
fi

# Create symlink to main script
ln -sf "$TASK_DIR/task.sh" "$TARGET_DIR/task"
chmod +x "$TARGET_DIR/task"
echo -e "${GREEN}Created 'task' command in project root${NC}"

# Create initial task tracking file
if [ ! -f "$TARGET_DIR/docs/task-tracking.json" ]; then
  echo '{
  "current_phase": "Project Setup",
  "current_task": "Initial Setup",
  "completed_tasks": [],
  "last_updated": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
}' > "$TARGET_DIR/docs/task-tracking.json"
  echo -e "${GREEN}Created initial task tracking file${NC}"
fi

# Create .vscode directory and tasks.json if it doesn't exist
mkdir -p "$TARGET_DIR/.vscode"
if [ ! -f "$TARGET_DIR/.vscode/tasks.json" ]; then
  echo '{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Task: Show Status",
      "type": "shell",
      "command": "./task status",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    },
    {
      "label": "Task: Complete Current",
      "type": "shell",
      "command": "./task complete",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    },
    {
      "label": "Task: Generate Next",
      "type": "shell",
      "command": "./task next",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    },
    {
      "label": "Task: Start with Claude",
      "type": "shell",
      "command": "./task start --browser",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    }
  ]
}' > "$TARGET_DIR/.vscode/tasks.json"
  echo -e "${GREEN}Created VS Code tasks configuration${NC}"
fi

echo -e "${BLUE}Installation complete!${NC}"
echo -e "Run ${YELLOW}./task help${NC} to get started"
