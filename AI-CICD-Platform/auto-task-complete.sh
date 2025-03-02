#!/bin/bash

# Script to automatically detect task completion based on code changes and run task-complete.sh
# Usage: ./auto-task-complete.sh [commit_message]

# Configuration
TASK_TRACKING_FILE="docs/task-tracking.json"
TASK_COMPLETE_SCRIPT="./task-complete.sh"

# Get current task
CURRENT_TASK=$(jq -r '.current_task' "$TASK_TRACKING_FILE")
echo "Current task: $CURRENT_TASK"

# Check if a commit message was provided
if [ $# -eq 0 ]; then
    # No commit message provided, prompt for one
    echo "Enter commit message (include 'Completed task: $CURRENT_TASK' to trigger task completion):"
    read -r COMMIT_MESSAGE
else
    # Use provided commit message
    COMMIT_MESSAGE="$1"
fi

# Add all changes to git
git add .

# Commit changes
git commit -m "$COMMIT_MESSAGE"

# Check if commit message indicates task completion
if [[ "$COMMIT_MESSAGE" == *"Completed task"* || "$COMMIT_MESSAGE" == *"completed task"* || "$COMMIT_MESSAGE" == *"Task completed"* || "$COMMIT_MESSAGE" == *"task completed"* ]]; then
    echo "Task completion detected in commit message."
    echo "Running task-complete.sh to generate the next task..."
    
    # Run task-complete.sh
    $TASK_COMPLETE_SCRIPT
    
    # Add the newly generated task file and updated task tracking file
    git add "$TASK_TRACKING_FILE" tasks/
    
    # Commit the task completion
    git commit -m "Generated next task: $(jq -r '.current_task' "$TASK_TRACKING_FILE")"
    
    echo "Task transition complete. New task is ready to work on."
else
    echo "Task completion not detected in commit message."
    echo "If you've completed the task, please run ./task-complete.sh manually."
fi

# Automatically push changes to remote repository
git push
echo "Changes automatically pushed to remote repository."
