#!/bin/bash

# next-task-for-claude.sh
# A simple script to output the next task prompt for use with Claude's "Start new task" feature

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root directory
cd "$PROJECT_ROOT"

# Output the next task prompt
echo "====================== NEXT TASK PROMPT ======================="
if [ -f docs/next-task-prompt.md ]; then
    # Read the file line by line
    while IFS= read -r line; do
        echo "$line"
    done < docs/next-task-prompt.md
else
    echo "# Next Task: Task 2 in [Another Phase]"
    echo ""
    echo "## Task Description"
    echo "This task involves implementing the Task 2 feature for the [Another Phase] component of the AI CI/CD Platform."
    echo ""
    echo "## Steps to Complete"
    echo "1. Step 1"
    echo ""
    echo ""
    echo "## Testing Requirements"
    echo "- Ensure all tests pass"
    echo "- Add new tests for the implemented functionality"
    echo "- Verify integration with existing components"
    echo ""
    echo "## Documentation"
    echo "- Update relevant README files"
    echo "- Update architecture diagrams if necessary"
    echo "- Update API documentation if applicable"
    echo ""
    echo "After completing this task run the task-tracker.py script to mark it as completed and get the prompt for the next task."
fi
echo "================================================================="
echo ""
echo "Copy the above prompt to use with Claude's \"Start new task\" feature."
