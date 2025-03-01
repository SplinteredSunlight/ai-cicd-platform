# AI Task Manager

A lightweight, command-line task management system designed to work with Claude AI for efficient development workflows.

## Overview

AI Task Manager helps you organize your development tasks and integrate with Claude AI for AI-assisted development. It provides:

- Task tracking and management
- Task prompt generation with customizable templates
- Clipboard integration for easy copying of task prompts
- Direct browser integration with Claude
- VS Code integration through tasks

## Features

- 📋 **Task Tracking**: Keep track of your tasks and their completion status
- 🤖 **Claude AI Integration**: Easily prepare and send task prompts to Claude
- 📝 **Customizable Templates**: Use different templates for different types of tasks
- 🔄 **Hierarchical Tasks**: Support for parent tasks and sub-tasks
- 📊 **Context Management**: Maintain context between tasks for better continuity
- 🖥️ **VS Code Integration**: Run task commands directly from VS Code

## Installation

### Option 1: Install in a Project

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-task-manager.git
cd ai-task-manager

# Install in your project
./scripts/install.sh /path/to/your/project
```

### Option 2: Use Directly

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-task-manager.git
cd ai-task-manager

# Make scripts executable
chmod +x scripts/*.sh

# Create symlink to task.sh
ln -sf "$(pwd)/scripts/task.sh" /usr/local/bin/task
```

## Usage

### Basic Commands

```bash
# Show current task status
./task status

# Complete the current task
./task complete

# Generate the next task prompt
./task next

# Prepare task for Claude (copies to clipboard)
./task start

# Open Claude in browser with the task prompt
./task start --browser

# Show help
./task help
```

### Using Templates

```bash
# Use a specific template
./task next --template detailed

# Available templates: default, concise, detailed
```

### Working with Sub-Tasks

```bash
# Complete a specific sub-task
./task complete --sub-task "Sub-Task Name"

# Generate prompt for a specific sub-task
./task next --sub-task "Sub-Task Name"
```

## VS Code Integration

After installation, the following VS Code tasks are available:

- **Task: Show Status**: Display the current task status
- **Task: Complete Current**: Mark the current task as completed
- **Task: Generate Next**: Generate the next task prompt
- **Task: Start with Claude**: Prepare the task for Claude and open in browser

Access these tasks through the Command Palette (Ctrl+Shift+P) and type "Tasks: Run Task".

## Customization

### Templates

Templates are stored in `docs/templates/task-prompt-templates.json`. You can edit this file to customize the templates or add new ones.

### Task Tracking

Task tracking data is stored in `docs/task-tracking.json`. This file is updated automatically when you complete tasks.

## Separating from AI CI/CD Platform

This task management system was originally part of the AI CI/CD Platform but has been separated to make it more reusable and focused. It can now be used with any project, not just the AI CI/CD Platform.

## License

MIT
