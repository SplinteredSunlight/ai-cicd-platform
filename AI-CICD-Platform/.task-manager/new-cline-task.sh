#!/bin/bash

# Script to complete the current task and generate a new task prompt file for Cline
# Usage: ./new-cline-task.sh [options]

# Set up colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Determine script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"

# Parse options
TEMPLATE="default"
SUB_TASK=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --template)
      TEMPLATE="$2"
      shift 2
      ;;
    --sub-task)
      SUB_TASK="$2"
      shift 2
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

# Complete the current task
echo -e "${BLUE}=== Completing Current Task ===${NC}"
if [ -n "$SUB_TASK" ]; then
  "$SCRIPT_DIR/task-tracker.py" --complete --sub-task "$SUB_TASK"
else
  "$SCRIPT_DIR/task-tracker.py" --complete
fi

# Update the context cache
echo -e "${BLUE}=== Updating Context Cache ===${NC}"
"$SCRIPT_DIR/context-manager.py" --update

# Generate the next task prompt
echo -e "${YELLOW}=== Generating Next Task Prompt ===${NC}"
if [ -n "$SUB_TASK" ]; then
  "$SCRIPT_DIR/task-tracker.py" --next --template "$TEMPLATE" --sub-task "$SUB_TASK"
else
  "$SCRIPT_DIR/task-tracker.py" --next --template "$TEMPLATE"
fi

# Get current timestamp for the filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TASK_DATA=$("$SCRIPT_DIR/task-tracker.py" --status 2>&1)
CURRENT_TASK=$(echo "$TASK_DATA" | grep "Current Task:" | sed 's/Current Task: //')
SANITIZED_TASK=$(echo "$CURRENT_TASK" | tr ' ' '_' | tr -d '[:punct:]')

# Create a new markdown file for the task
NEXT_TASK_PROMPT_FILE="$PROJECT_ROOT/docs/next-task-prompt.md"
NEW_TASK_FILE="$PROJECT_ROOT/tasks/task_${TIMESTAMP}_${SANITIZED_TASK}.md"

# Create tasks directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/tasks"

# Copy the next task prompt to the new file
if [ -f "$NEXT_TASK_PROMPT_FILE" ]; then
  # Add a header with instructions
  echo "# New Cline Task - $(date)" > "$NEW_TASK_FILE"
  echo "" >> "$NEW_TASK_FILE"
  echo "## Instructions" >> "$NEW_TASK_FILE"
  echo "1. Copy the entire content below this section" >> "$NEW_TASK_FILE"
  echo "2. Start a new Cline conversation" >> "$NEW_TASK_FILE"
  echo "3. Paste the content to begin the new task" >> "$NEW_TASK_FILE"
  echo "" >> "$NEW_TASK_FILE"
  echo "---" >> "$NEW_TASK_FILE"
  echo "" >> "$NEW_TASK_FILE"
  cat "$NEXT_TASK_PROMPT_FILE" >> "$NEW_TASK_FILE"
  
  echo -e "${GREEN}=== Task Prompt Created ===${NC}"
  echo -e "New task prompt file created at: ${BLUE}$NEW_TASK_FILE${NC}"
  echo -e "To start a new Cline conversation:"
  echo -e "1. ${YELLOW}Open the file${NC}"
  echo -e "2. ${YELLOW}Copy the entire content below the instructions${NC}"
  echo -e "3. ${YELLOW}Start a new Cline conversation and paste the content${NC}"
  
  # Open the file in VS Code
  if command -v code &> /dev/null; then
    code "$NEW_TASK_FILE"
    echo -e "${GREEN}File opened in VS Code${NC}"
  else
    echo -e "${YELLOW}VS Code command not found. Please open the file manually.${NC}"
  fi
else
  echo -e "${RED}Error: Next task prompt file not found.${NC}"
  exit 1
fi

echo -e "${GREEN}Task workflow completed!${NC}"
