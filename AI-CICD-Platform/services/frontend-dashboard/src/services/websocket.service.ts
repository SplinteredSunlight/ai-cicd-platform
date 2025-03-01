import { io, Socket } from 'socket.io-client';

export interface WebSocketEvent {
  event_type: string;
  data: Record<string, any>;
}

export class WebSocketService {
  private socket: Socket | null = null;
  private eventHandlers: Map<string, Set<(data: any) => void>> = new Map();
  private connectionHandlers: Set<(connected: boolean) => void> = new Set();
  private isConnected = false;
  private reconnectTimer: number | null = null;
  private token: string | null = null;

  constructor(private baseUrl: string = import.meta.env.VITE_API_URL || 'http://localhost:8000') {
    // Remove trailing slash if present
    if (this.baseUrl.endsWith('/')) {
      this.baseUrl = this.baseUrl.slice(0, -1);
    }
  }

  /**
   * Connect to the WebSocket server
   * @param token Authentication token
   */
  connect(token: string): void {
    if (this.socket) {
      this.disconnect();
    }

    this.token = token;
    const wsUrl = `${this.baseUrl}/ws`;

    this.socket = io(wsUrl, {
      transports: ['websocket'],
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });

    this.setupEventListeners();

    // Authenticate after connection
    this.socket.on('connect', () => {
      this.socket?.emit('authenticate', { token });
    });
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
      this.notifyConnectionHandlers();
    }

    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Set up event listeners for the socket
   */
  private setupEventListeners(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.isConnected = true;
      this.notifyConnectionHandlers();
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      this.isConnected = false;
      this.notifyConnectionHandlers();

      // Try to reconnect after a delay
      if (!this.reconnectTimer && this.token) {
        this.reconnectTimer = window.setTimeout(() => {
          this.reconnectTimer = null;
          this.connect(this.token!);
        }, 5000);
      }
    });

    this.socket.on('authenticated', (data) => {
      console.log('WebSocket authenticated', data);
    });

    this.socket.on('auth_error', (error) => {
      console.error('WebSocket authentication error', error);
      this.disconnect();
    });

    // Set up handlers for registered events
    this.eventHandlers.forEach((handlers, eventType) => {
      this.socket?.on(eventType, (data) => {
        handlers.forEach(handler => handler(data));
      });
    });
  }

  /**
   * Register a handler for a specific event type
   * @param eventType Event type to listen for
   * @param handler Handler function to call when the event is received
   * @returns A function to unregister the handler
   */
  on(eventType: string, handler: (data: any) => void): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());

      // If we're already connected, set up the listener
      if (this.socket) {
        this.socket.on(eventType, (data) => {
          const handlers = this.eventHandlers.get(eventType);
          if (handlers) {
            handlers.forEach(h => h(data));
          }
        });
      }
    }

    const handlers = this.eventHandlers.get(eventType)!;
    handlers.add(handler);

    // Return a function to remove the handler
    return () => {
      const handlers = this.eventHandlers.get(eventType);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          this.eventHandlers.delete(eventType);
          this.socket?.off(eventType);
        }
      }
    };
  }

  /**
   * Register a handler for connection state changes
   * @param handler Handler function to call when the connection state changes
   * @returns A function to unregister the handler
   */
  onConnectionChange(handler: (connected: boolean) => void): () => void {
    this.connectionHandlers.add(handler);
    
    // Call the handler immediately with the current state
    handler(this.isConnected);
    
    // Return a function to remove the handler
    return () => {
      this.connectionHandlers.delete(handler);
    };
  }

  /**
   * Notify all connection handlers of the current connection state
   */
  private notifyConnectionHandlers(): void {
    this.connectionHandlers.forEach(handler => {
      handler(this.isConnected);
    });
  }

  /**
   * Check if the WebSocket is connected
   */
  isSocketConnected(): boolean {
    return this.isConnected;
  }
}

// Create a singleton instance
const websocketService = new WebSocketService();
export default websocketService;
