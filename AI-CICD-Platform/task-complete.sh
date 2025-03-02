#!/bin/bash

# Script to be called at the end of each task to generate the next task
# Usage: ./task-complete.sh

echo "Task completed! Generating next task..."

# Run the generate-next-task-prompt.sh script
./generate-next-task-prompt.sh

echo "Next task has been generated and is ready to work on."
echo "You can find the task details in the tasks directory."
