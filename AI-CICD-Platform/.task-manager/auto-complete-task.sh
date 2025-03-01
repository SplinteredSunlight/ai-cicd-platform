#!/bin/bash

# Script to automatically complete the current task and display the next task prompt
# Supports hierarchical tasks (parent tasks with child sub-tasks)

# Ensure we're in the project root directory
cd "$(dirname "$0")/.."

# Parse command line arguments
TEMPLATE="default"
SUB_TASK=""

# Process command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --template)
      TEMPLATE="$2"
      shift 2
      ;;
    --sub-task)
      SUB_TASK="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--template <template_name>] [--sub-task <sub_task_name>]"
      echo "Available templates: default, concise, detailed"
      echo "Options:"
      echo "  --template <name>    Use the specified template for the next task prompt"
      echo "  --sub-task <name>    Mark a specific sub-task as completed"
      echo "  --help               Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--template <template_name>] [--sub-task <sub_task_name>]"
      echo "Use --help for more information"
      exit 1
      ;;
  esac
done

# Run the complete-current-task.sh script to mark the current task as completed
if [ -n "$SUB_TASK" ]; then
  ./scripts/complete-current-task.sh --template "$TEMPLATE" --sub-task "$SUB_TASK"
else
  ./scripts/complete-current-task.sh --template "$TEMPLATE"
fi

# Extract the next task prompt from docs/next-task-prompt.md
NEXT_TASK_PROMPT=$(cat docs/next-task-prompt.md)

# Display a message indicating that the task has been completed
echo ""
echo "==============================================================="
echo "Task completed! The next task prompt is shown above."
echo "You can use this prompt for your next task."
echo "Available templates: default, concise, detailed (use --template option)"
echo "For hierarchical tasks, use --sub-task to mark sub-tasks as completed"
echo "==============================================================="

# Show the current task status
echo ""
echo "Current task status:"
python3 scripts/task-tracker.py --status
