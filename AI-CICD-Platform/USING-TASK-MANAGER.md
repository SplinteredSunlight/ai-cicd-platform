# Using the AI Task Manager with AI CICD Platform

This guide explains how to use the AI Task Manager to help develop the AI CICD Platform. The task management system has been set up to streamline your workflow with Cline in VS Code.

## Quick Start

The fastest way to get started is to use the Cline workflow:

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
2. Type "Tasks: Run Task"
3. Select "Task: Cline Workflow"

This will:
- Complete the current task
- Generate a new task prompt
- Create a markdown file in the `tasks` directory
- Open the file in VS Code

You can then copy the content from the markdown file and paste it into a new Cline conversation in VS Code.

## Task Templates

The task management system includes several specialized templates for different types of tasks:

- **Backend Service**: For implementing features in Python-based backend services
- **Frontend Feature**: For implementing features in the React/TypeScript frontend
- **Integration Task**: For tasks that span multiple services
- **Bug Fix**: For fixing issues in the platform
- **Documentation**: For creating or updating documentation

To use a specific template:

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
2. Type "Tasks: Run Task"
3. Select one of the specialized workflow tasks:
   - "Task: Cline Workflow (Backend Service)"
   - "Task: Cline Workflow (Frontend Feature)"
   - "Task: Cline Workflow (Integration Task)"
   - "Task: Cline Workflow (Bug Fix)"
   - "Task: Cline Workflow (Documentation)"

## Command Line Usage

You can also use the task management system from the command line:

```bash
# Show current task status
./task status

# Complete the current task
./task complete

# Generate the next task prompt
./task next

# Run the Cline workflow
./task cline

# Run the Cline workflow with a specific template
./task cline --template backend-service

# Update the context cache
./task context --update
```

## Working with Sub-Tasks

For complex tasks, you can use sub-tasks:

```bash
# Complete a specific sub-task
./task complete --sub-task "Sub-Task Name"

# Generate prompt for a specific sub-task
./task next --sub-task "Sub-Task Name"

# Run the Cline workflow for a specific sub-task
./task cline --sub-task "Sub-Task Name"
```

## Updating the Context Cache

The context cache stores information about your project to provide better context for task prompts. If you make significant changes to the project structure or documentation, you should update the context cache:

```bash
./task context --update
```

Or use the VS Code task:

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
2. Type "Tasks: Run Task"
3. Select "Task: Update Context Cache"

## Recommended Workflow

Here's a recommended workflow for using the AI Task Manager with the AI CICD Platform:

1. **Start your day** by checking the current task status:
   ```bash
   ./task status
   ```

2. **Update the context cache** if needed:
   ```bash
   ./task context --update
   ```

3. **Generate a task prompt** using the appropriate template:
   ```bash
   ./task cline --template backend-service
   ```

4. **Copy the prompt** from the opened markdown file and paste it into a new Cline conversation in VS Code.

5. **Implement the task** with Cline's assistance.

6. **Test your changes** to ensure they work correctly.

7. **Complete the task** and start the next one:
   ```bash
   ./task cline
   ```

## Tips for Effective Use

- **Use the right template** for each task to get the most relevant context and guidance.
- **Keep the project plan updated** to ensure tasks are properly tracked.
- **Update the context cache** when you make significant changes to the project.
- **Break down complex tasks** into sub-tasks for easier management.
- **Start a new Cline conversation** for each task to avoid token limits and keep conversations focused.
