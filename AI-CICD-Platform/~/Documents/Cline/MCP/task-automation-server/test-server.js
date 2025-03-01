#!/usr/bin/env node

import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

// Path to the server
const serverPath = path.join(process.cwd(), 'build', 'index.js');

// Sample request to detect task completion
const detectTaskCompletionRequest = {
  jsonrpc: '2.0',
  id: 1,
  method: 'callTool',
  params: {
    name: 'detect_task_completion',
    arguments: {
      conversationText: "Human: Please implement a simple todo app.\n\nAssistant: I've implemented the todo app. The task is complete."
    }
  }
};

// Sample request to create next task file
const createNextTaskFileRequest = {
  jsonrpc: '2.0',
  id: 2,
  method: 'callTool',
  params: {
    name: 'create_next_task_file',
    arguments: {
      taskName: "Implement User Authentication",
      taskDescription: "Add user authentication to the application with login, registration, and password reset functionality."
    }
  }
};

// Start the server process
console.log('Starting server...');
const server = spawn('node', [serverPath], {
  stdio: ['pipe', 'pipe', process.stderr]
});

// Send the detect task completion request
console.log('Sending detect task completion request...');
server.stdin.write(JSON.stringify(detectTaskCompletionRequest) + '\n');

// Listen for the response
let responseData = '';
server.stdout.on('data', (data) => {
  responseData += data.toString();
  
  try {
    // Try to parse the response
    const response = JSON.parse(responseData);
    console.log('Response:', JSON.stringify(response, null, 2));
    
    // If we got a response, send the next request
    if (response.id === 1) {
      console.log('Sending create next task file request...');
      server.stdin.write(JSON.stringify(createNextTaskFileRequest) + '\n');
      responseData = '';
    } else if (response.id === 2) {
      // If we got a response to the second request, exit
      console.log('Test complete!');
      server.kill();
      process.exit(0);
    }
  } catch (e) {
    // If we can't parse the response yet, wait for more data
  }
});

// Handle server exit
server.on('close', (code) => {
  console.log(`Server exited with code ${code}`);
});

// Handle errors
server.on('error', (err) => {
  console.error('Error:', err);
  process.exit(1);
});

// Exit after 10 seconds if we don't get a response
setTimeout(() => {
  console.error('Timeout waiting for response');
  server.kill();
  process.exit(1);
}, 10000);
