#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk';
import { StdioServerTransport } from '@modelcontextprotocol/sdk';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk';
import * as fs from 'fs-extra';
import * as path from 'path';
import { execa } from 'execa';

// Define the task automation server
class TaskAutomationServer {
  private server: Server;
  private projectRoot: string;
  private tasksDir: string;
  private taskManagerDir: string;

  constructor() {
    this.server = new Server(
      {
        name: 'task-automation-server',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Set default paths - these can be overridden via environment variables
    this.projectRoot = process.env.PROJECT_ROOT || process.cwd();
    this.tasksDir = process.env.TASKS_DIR || path.join(this.projectRoot, 'tasks');
    this.taskManagerDir = process.env.TASK_MANAGER_DIR || path.join(this.projectRoot, '.task-manager');

    this.setupToolHandlers();
    
    // Error handling
    this.server.onerror = (error: any) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'detect_task_completion',
          description: 'Detects if the current task is complete based on Claude\'s response',
          inputSchema: {
            type: 'object',
            properties: {
              conversationText: {
                type: 'string',
                description: 'The text of the current conversation with Claude',
              },
            },
            required: ['conversationText'],
          },
        },
        {
          name: 'create_next_task_file',
          description: 'Creates a new task file for the next task',
          inputSchema: {
            type: 'object',
            properties: {
              taskName: {
                type: 'string',
                description: 'The name of the next task',
              },
              taskDescription: {
                type: 'string',
                description: 'The description of the next task',
              },
            },
            required: ['taskName', 'taskDescription'],
          },
        },
        {
          name: 'start_new_conversation',
          description: 'Starts a new Cline conversation with the next task',
          inputSchema: {
            type: 'object',
            properties: {
              taskFilePath: {
                type: 'string',
                description: 'The path to the task file to use for the new conversation',
              },
            },
            required: ['taskFilePath'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request: any) => {
      switch (request.params.name) {
        case 'detect_task_completion':
          return this.handleDetectTaskCompletion(request.params.arguments);
        case 'create_next_task_file':
          return this.handleCreateNextTaskFile(request.params.arguments);
        case 'start_new_conversation':
          return this.handleStartNewConversation(request.params.arguments);
        default:
          throw new McpError(
            ErrorCode.MethodNotFound,
            `Unknown tool: ${request.params.name}`
          );
      }
    });
  }

  private async handleDetectTaskCompletion(args: any) {
    if (typeof args !== 'object' || args === null || typeof args.conversationText !== 'string') {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Invalid arguments for detect_task_completion'
      );
    }

    const conversationText = args.conversationText;
    
    // Check for explicit completion statements from Claude
    const completionPhrases = [
      'task is complete',
      'task has been completed',
      'successfully completed the task',
      'task is now complete',
      'completed the requested task',
      'finished implementing',
      'implementation is complete',
      'successfully implemented',
    ];

    const isComplete = completionPhrases.some(phrase => 
      conversationText.toLowerCase().includes(phrase.toLowerCase())
    );

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            isComplete,
            reason: isComplete ? 'Detected completion statement in conversation' : 'No completion statement detected',
          }, null, 2),
        },
      ],
    };
  }

  private async handleCreateNextTaskFile(args: any) {
    if (
      typeof args !== 'object' || 
      args === null || 
      typeof args.taskName !== 'string' || 
      typeof args.taskDescription !== 'string'
    ) {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Invalid arguments for create_next_task_file'
      );
    }

    const { taskName, taskDescription } = args;
    
    // Ensure tasks directory exists
    await fs.ensureDir(this.tasksDir);
    
    // Generate timestamp for the task file
    const timestamp = new Date().toISOString().replace(/[-:]/g, '').split('.')[0];
    const sanitizedTaskName = taskName.replace(/[^a-zA-Z0-9]/g, '');
    const taskFileName = `task_${timestamp}_${sanitizedTaskName}.md`;
    const taskFilePath = path.join(this.tasksDir, taskFileName);
    
    // Create task file content
    const taskContent = `# ${taskName}\n\n${taskDescription}`;
    
    try {
      await fs.writeFile(taskFilePath, taskContent);
      
      // Update task tracking JSON if it exists
      const taskTrackingPath = path.join(this.projectRoot, 'docs', 'task-tracking.json');
      if (await fs.pathExists(taskTrackingPath)) {
        const taskTracking = await fs.readJson(taskTrackingPath);
        
        if (Array.isArray(taskTracking.tasks)) {
          taskTracking.tasks.push({
            id: taskFileName,
            name: taskName,
            status: 'pending',
            createdAt: new Date().toISOString(),
          });
          
          await fs.writeJson(taskTrackingPath, taskTracking, { spaces: 2 });
        }
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              taskFilePath,
              message: `Created new task file: ${taskFilePath}`,
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      console.error('Error creating task file:', error);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: String(error),
            }, null, 2),
          },
        ],
        isError: true,
      };
    }
  }

  private async handleStartNewConversation(args: any) {
    if (
      typeof args !== 'object' || 
      args === null || 
      typeof args.taskFilePath !== 'string'
    ) {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Invalid arguments for start_new_conversation'
      );
    }

    const { taskFilePath } = args;
    
    try {
      // Check if the task file exists
      if (!await fs.pathExists(taskFilePath)) {
        throw new Error(`Task file does not exist: ${taskFilePath}`);
      }
      
      // Check if the task manager scripts exist
      const newClineTaskScript = path.join(this.taskManagerDir, 'new-cline-task.sh');
      if (!await fs.pathExists(newClineTaskScript)) {
        throw new Error(`Task manager script does not exist: ${newClineTaskScript}`);
      }
      
      // Make the script executable
      await fs.chmod(newClineTaskScript, 0o755);
      
      // Execute the script to start a new conversation
      const result = await execa('bash', [newClineTaskScript, taskFilePath], {
        cwd: this.projectRoot,
        stdio: 'pipe',
      });
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              message: `Started new conversation with task: ${taskFilePath}`,
              output: result.stdout,
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      console.error('Error starting new conversation:', error);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: String(error),
            }, null, 2),
          },
        ],
        isError: true,
      };
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Task Automation MCP server running on stdio');
  }
}

const server = new TaskAutomationServer();
server.run().catch(console.error);
