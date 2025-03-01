#!/bin/bash

# Cline Workflow Script
# This script streamlines the workflow for using Cline in VS Code
# Usage: ./task cline [--template TEMPLATE] [--sub-task "Sub-Task Name"]

# Set up colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments
TEMPLATE="default"
SUB_TASK=""

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --template)
      TEMPLATE="$2"
      shift
      ;;
    --sub-task)
      SUB_TASK="$2"
      shift
      ;;
    *)
      echo -e "${RED}Unknown parameter: $1${NC}"
      exit 1
      ;;
  esac
  shift
done

# Step 1: Complete the current task
echo -e "${BLUE}Step 1: Completing current task...${NC}"
if [ -n "$SUB_TASK" ]; then
  "$SCRIPT_DIR/complete-current-task.sh" --sub-task "$SUB_TASK"
else
  "$SCRIPT_DIR/complete-current-task.sh"
fi

# Step 2: Generate the next task prompt
echo -e "${BLUE}Step 2: Generating next task prompt...${NC}"
"$SCRIPT_DIR/generate-next-task-prompt.sh" --template "$TEMPLATE"

# Step 3: Get task information
TASK_INFO=$(python3 "$SCRIPT_DIR/task-tracker.py" --status --json)
TASK_NAME=$(echo "$TASK_INFO" | grep -o '"current_task": "[^"]*"' | cut -d'"' -f4)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TASK_FILENAME="task_${TIMESTAMP}_$(echo $TASK_NAME | sed 's/ //g').md"

# Step 4: Create a markdown file in the tasks directory
echo -e "${BLUE}Step 3: Creating task file in tasks directory...${NC}"
mkdir -p "$PROJECT_ROOT/tasks"

cat > "$PROJECT_ROOT/tasks/$TASK_FILENAME" << EOF
# New Cline Task - $(date)

## Instructions
1. Copy the entire content below this section
2. Start a new Cline conversation
3. Paste the content to begin the new task

---

$(cat "$PROJECT_ROOT/docs/next-task-prompt.md")
EOF

echo -e "${GREEN}Created task file: tasks/$TASK_FILENAME${NC}"

# Step 5: Open the file in VS Code
echo -e "${BLUE}Step 4: Opening task file in VS Code...${NC}"
if command -v code &> /dev/null; then
  code "$PROJECT_ROOT/tasks/$TASK_FILENAME"
  echo -e "${GREEN}File opened in VS Code${NC}"
else
  echo -e "${YELLOW}VS Code command not found. Please open the file manually:${NC}"
  echo -e "${YELLOW}$PROJECT_ROOT/tasks/$TASK_FILENAME${NC}"
fi

echo -e "${GREEN}Workflow complete!${NC}"
echo -e "To use this task with Cline:"
echo -e "1. ${BLUE}Copy the content below the instructions section${NC}"
echo -e "2. ${BLUE}Start a new Cline conversation${NC}"
echo -e "3. ${BLUE}Paste the content to begin the new task${NC}"
