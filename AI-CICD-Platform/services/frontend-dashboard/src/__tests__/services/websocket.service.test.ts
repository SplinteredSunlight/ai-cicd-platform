import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { WebSocketService } from '../../services/websocket.service';

// Mock socket.io-client
vi.mock('socket.io-client', () => {
  const mockSocket = {
    on: vi.fn(),
    off: vi.fn(),
    emit: vi.fn(),
    disconnect: vi.fn(),
  };
  
  return {
    io: vi.fn(() => mockSocket),
  };
});

describe('WebSocketService', () => {
  let service: WebSocketService;
  let mockSocket: any;
  
  beforeEach(() => {
    // Clear all mocks
    vi.clearAllMocks();
    
    // Create a new service instance
    service = new WebSocketService('http://test-api.com');
    
    // Get the mock socket
    mockSocket = require('socket.io-client').io();
  });
  
  afterEach(() => {
    // Disconnect the socket
    service.disconnect();
  });
  
  it('should connect to the WebSocket server', () => {
    // Connect to the WebSocket server
    service.connect('test-token');
    
    // Check if the socket was created with the correct URL
    expect(require('socket.io-client').io).toHaveBeenCalledWith('http://test-api.com/ws', expect.any(Object));
    
    // Check if the socket has the correct event listeners
    expect(mockSocket.on).toHaveBeenCalledWith('connect', expect.any(Function));
    expect(mockSocket.on).toHaveBeenCalledWith('disconnect', expect.any(Function));
    expect(mockSocket.on).toHaveBeenCalledWith('authenticated', expect.any(Function));
    expect(mockSocket.on).toHaveBeenCalledWith('auth_error', expect.any(Function));
  });
  
  it('should disconnect from the WebSocket server', () => {
    // Connect to the WebSocket server
    service.connect('test-token');
    
    // Disconnect from the WebSocket server
    service.disconnect();
    
    // Check if the socket was disconnected
    expect(mockSocket.disconnect).toHaveBeenCalled();
  });
  
  it('should register event handlers', () => {
    // Connect to the WebSocket server
    service.connect('test-token');
    
    // Create a mock event handler
    const mockHandler = vi.fn();
    
    // Register the event handler
    const unsubscribe = service.on('test-event', mockHandler);
    
    // Check if the socket has the correct event listener
    expect(mockSocket.on).toHaveBeenCalledWith('test-event', expect.any(Function));
    
    // Unsubscribe from the event
    unsubscribe();
    
    // Check if the socket has removed the event listener
    expect(mockSocket.off).toHaveBeenCalledWith('test-event');
  });
  
  it('should authenticate after connection', () => {
    // Connect to the WebSocket server
    service.connect('test-token');
    
    // Get the connect handler
    const connectHandler = mockSocket.on.mock.calls.find((call: any[]) => call[0] === 'connect')[1];
    
    // Call the connect handler
    connectHandler();
    
    // Check if the socket emitted the authenticate event
    expect(mockSocket.emit).toHaveBeenCalledWith('authenticate', { token: 'test-token' });
  });
  
  it('should handle authentication errors', () => {
    // Connect to the WebSocket server
    service.connect('test-token');
    
    // Get the auth_error handler
    const authErrorHandler = mockSocket.on.mock.calls.find((call: any[]) => call[0] === 'auth_error')[1];
    
    // Create a spy on console.error
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    // Call the auth_error handler
    authErrorHandler({ message: 'Authentication failed' });
    
    // Check if the error was logged
    expect(consoleSpy).toHaveBeenCalledWith('WebSocket authentication error', { message: 'Authentication failed' });
    
    // Check if the socket was disconnected
    expect(mockSocket.disconnect).toHaveBeenCalled();
    
    // Restore console.error
    consoleSpy.mockRestore();
  });
});
