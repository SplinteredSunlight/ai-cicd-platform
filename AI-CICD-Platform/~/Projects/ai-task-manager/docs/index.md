# AI Task Manager Documentation

Welcome to the AI Task Manager documentation. This index provides an overview of the available documentation and resources for the project.

## Overview

AI Task Manager is a lightweight, command-line task management system designed to work with Claude AI for efficient development workflows. It helps you organize your development tasks and integrate with Claude AI for AI-assisted development.

## Components

- **Task Tracker**: Core component for tracking tasks and their completion status
- **Context Manager**: Manages context between tasks for better continuity
- **Task Templates**: Customizable templates for different types of tasks
- **Claude Integration**: Tools for integrating with Claude AI

## Documentation

- [Templates](templates/README.md) - Documentation for the task prompt template system
- [Template Definitions](templates/task-prompt-templates.json) - JSON definitions of available templates

## Scripts

The AI Task Manager includes several scripts for managing tasks:

- `task.sh` - Main entry point for all task operations
- `task-tracker.py` - Core script for tracking task progress
- `context-manager.py` - Manages the context cache
- `generate-next-task-prompt.sh` - Generates prompts for the next task
- `complete-current-task.sh` - Marks tasks as completed
- `auto-complete-task.sh` - Automates the task completion workflow
- `next-task-for-claude.sh` - Formats task prompts for Claude
- `auto-task-workflow.sh` - Automates the entire task workflow
- `install.sh` - Installs the AI Task Manager in a project

## Usage

See the [README.md](../README.md) for detailed usage instructions.

## Customization

The AI Task Manager can be customized in several ways:

- **Templates**: Edit the templates in `docs/templates/task-prompt-templates.json`
- **Context Management**: Configure context management in `context-manager.py`
- **Task Tracking**: Customize task tracking in `task-tracker.py`

## Integration with Other Projects

The AI Task Manager is designed to be easily integrated with other projects. Use the `install.sh` script to install it in any project.
