#!/bin/bash

# auto-task-workflow.sh
# A script to automate the task workflow with Claude

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root directory
cd "$PROJECT_ROOT"

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

# Mark the current task as completed
if [ -n "$SUB_TASK" ]; then
  python3 scripts/task-tracker.py --complete --template "$TEMPLATE" --sub-task "$SUB_TASK"
else
  python3 scripts/task-tracker.py --complete --template "$TEMPLATE"
fi

# Generate the next task prompt
./scripts/generate-next-task-prompt.sh --template "$TEMPLATE"

# Display the next task prompt in a format ready for Claude
./scripts/next-task-for-claude.sh

# Show the current task status
echo ""
echo "Current task status:"
python3 scripts/task-tracker.py --status
