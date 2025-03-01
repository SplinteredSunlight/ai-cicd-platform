# Task Automation Server for Cline

This MCP server extends Cline with task automation features that automatically detect task completion, create new task files, and start new conversations.

## Features

1. **Task Completion Detection**
   - Automatically detects when a task is complete based on Claude's responses
   - Looks for completion phrases like "task is complete", "successfully implemented", etc.

2. **Task File Creation**
   - Creates new task files with proper naming conventions
   - Updates task tracking JSON if it exists

3. **Conversation Management**
   - Starts a new Cline conversation with the next task
   - Maintains context between conversations

## Installation

The server is already installed and configured for both VS Code Cline extension and Claude desktop app.

### VS Code Cline Extension
- Configuration file: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

### Claude Desktop App
- Configuration file: `~/Library/Application Support/Claude/claude_desktop_config.json`

## Usage

The server provides the following tools that can be used in Cline:

### 1. Detect Task Completion

Detects if the current task is complete based on Claude's response.

```json
{
  "conversationText": "The full text of the conversation with Claude"
}
```

### 2. Create Next Task File

Creates a new task file for the next task.

```json
{
  "taskName": "Name of the next task",
  "taskDescription": "Detailed description of the next task"
}
```

### 3. Start New Conversation

Starts a new Cline conversation with the next task.

```json
{
  "taskFilePath": "/path/to/task/file.md"
}
```

## Workflow Example

1. Complete a task with Claude
2. Use the `detect_task_completion` tool to check if the task is complete
3. If complete, use the `create_next_task_file` tool to create the next task file
4. Use the `start_new_conversation` tool to start a new conversation with the next task

## Configuration

The server can be configured using environment variables:

- `PROJECT_ROOT`: The root directory of the project (default: current working directory)
- `TASKS_DIR`: The directory where task files are stored (default: `${PROJECT_ROOT}/tasks`)
- `TASK_MANAGER_DIR`: The directory where task manager scripts are stored (default: `${PROJECT_ROOT}/.task-manager`)

## Development

To modify the server:

1. Edit the source code in `src/index.ts`
2. Build the server with `npm run build`
3. Restart Cline to load the updated server

## Troubleshooting

If the server is not working:

1. Check that the server is enabled in the MCP settings
2. Verify that the paths in the MCP settings are correct
3. Check the Cline logs for any errors
