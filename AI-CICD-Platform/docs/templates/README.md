# Task Prompt Templates

This directory contains templates for generating task prompts in the AI CI/CD Platform project. Templates provide a way to control the format and content of task prompts, allowing for different levels of detail based on the needs of the task.

## Available Templates

The system comes with three built-in templates:

1. **default** - A balanced template with moderate detail
2. **concise** - A minimal template with just the essential information
3. **detailed** - A comprehensive template with full context and detailed instructions

## Template Structure

Each template consists of several sections that are combined to create the final prompt:

- **title** - The main heading for the task
- **description** - An overview of what the task involves
- **steps** - Specific steps to complete the task
- **testing** - Requirements for testing the implementation
- **documentation** - Guidelines for updating documentation
- **footer** - Closing instructions

## Template Variables

Templates can include the following variables that will be replaced with actual values:

- `{task_name}` - The name of the current task or sub-task
- `{phase_name}` - The name of the current project phase
- `{steps}` - The formatted steps for completing the task
- `{architecture_summary}` - A summary of the project architecture (only included in detailed template)
- `{recent_tasks}` - A list of recently completed tasks (only included in detailed template)

## Creating Custom Templates

To create a custom template, add a new entry to the `task-prompt-templates.json` file with your desired sections. For example:

```json
"my_custom_template": {
  "title": "# Custom Task: {task_name}\n\n",
  "description": "This is a custom template for {task_name} in {phase_name}.\n\n",
  "steps": "## Custom Steps\n{steps}\n\n",
  "testing": "## Testing\n- Custom testing instructions\n\n",
  "documentation": "## Documentation\n- Custom documentation instructions\n\n",
  "footer": "Custom footer text.\n"
}
```

## Using Templates

To use a specific template when generating a task prompt, use the `--template` option with the template name:

```bash
# Generate a prompt using the concise template
./scripts/generate-next-task-prompt.sh --template concise

# Complete a task and generate the next prompt using the detailed template
./scripts/complete-current-task.sh --template detailed

# Auto-complete a task and use a custom template
./scripts/auto-complete-task.sh --template my_custom_template
```

## Context Optimization

The system optimizes context usage based on the template:

- The **concise** template excludes architecture summaries and completed tasks
- The **default** template includes moderate context
- The **detailed** template includes full context with architecture details and completed tasks

This optimization helps manage prompt length while ensuring that the necessary information is available when needed.
