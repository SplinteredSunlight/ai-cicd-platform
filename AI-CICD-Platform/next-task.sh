#!/bin/bash

# Script to generate the next task and open it in VSCode
# Usage: ./next-task.sh

# Get the current task from task tracking file
CURRENT_TASK=$(jq -r '.current_task' "docs/task-tracking.json")
echo "Current task: $CURRENT_TASK"

# Run task-complete.sh to generate the next task
echo "Running task-complete.sh to generate the next task..."
./task-complete.sh

# Get the new current task
NEW_TASK=$(jq -r '.current_task' "docs/task-tracking.json")
echo "New task: $NEW_TASK"

# Convert task name to filename
TASK_FILE_NAME=$(echo "$NEW_TASK" | sed 's/[^a-zA-Z0-9]/-/g')
TASK_FILE_PATH="tasks/${TASK_FILE_NAME}.md"

# Add the newly generated task file and updated task tracking file
git add docs/task-tracking.json tasks/

# Commit the task completion
git commit -m "Generated next task: $NEW_TASK"

echo "Task transition complete. New task is ready to work on."

# Open the new task file in VSCode
# Try using 'code' command first
if command -v code &> /dev/null; then
    code "$TASK_FILE_PATH"
    echo "Opened new task file with 'code' command: $TASK_FILE_PATH"
else
    # If 'code' command is not available, try using 'open' on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open -a "Visual Studio Code" "$TASK_FILE_PATH"
        echo "Opened new task file with 'open' command: $TASK_FILE_PATH"
    else
        # On Linux, try xdg-open
        if command -v xdg-open &> /dev/null; then
            xdg-open "$TASK_FILE_PATH"
            echo "Opened new task file with 'xdg-open' command: $TASK_FILE_PATH"
        else
            echo "Could not open task file automatically. Please open it manually: $TASK_FILE_PATH"
        fi
    fi
fi

# Print the task file content to the console for easy copy/paste
echo ""
echo "================ NEW TASK CONTENT ================"
cat "$TASK_FILE_PATH"
echo "=================================================="
echo ""
