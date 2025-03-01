import { io, Socket } from 'socket.io-client';

export enum EventPriority {
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low'
}

export enum EventCategory {
  PIPELINE = 'pipeline',
  SECURITY = 'security',
  DEBUG = 'debug',
  SYSTEM = 'system',
  ARCHITECTURE = 'architecture',
  USER = 'user'
}

export interface WebSocketEvent {
  event_type: string;
  data: Record<string, any>;
  priority?: EventPriority;
  category?: EventCategory;
  timestamp?: string;
}

export interface WebSocketOptions {
  autoReconnect?: boolean;
  reconnectionAttempts?: number;
  reconnectionDelay?: number;
  reconnectionDelayMax?: number;
  categories?: EventCategory[];
}

const DEFAULT_OPTIONS: WebSocketOptions = {
  autoReconnect: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  categories: Object.values(EventCategory)
};

export class WebSocketService {
  private socket: Socket | null = null;
  private eventHandlers: Map<string, Set<(data: any) => void>> = new Map();
  private categoryHandlers: Map<EventCategory, Set<(event: WebSocketEvent) => void>> = new Map();
  private connectionHandlers: Set<(connected: boolean) => void> = new Set();
  private isConnected = false;
  private reconnectTimer: number | null = null;
  private reconnectAttempts = 0;
  private token: string | null = null;
  private options: WebSocketOptions = DEFAULT_OPTIONS;
  private enabledCategories: Set<EventCategory> = new Set(DEFAULT_OPTIONS.categories);

  constructor(private baseUrl: string = import.meta.env.VITE_API_URL || 'http://localhost:8000') {
    // Remove trailing slash if present
    if (this.baseUrl.endsWith('/')) {
      this.baseUrl = this.baseUrl.slice(0, -1);
    }
  }

  /**
   * Connect to the WebSocket server
   * @param token Authentication token
   * @param options Connection options
   */
  connect(token: string, options: WebSocketOptions = {}): void {
    if (this.socket) {
      this.disconnect();
    }

    this.token = token;
    this.options = { ...DEFAULT_OPTIONS, ...options };
    this.reconnectAttempts = 0;
    
    // Set enabled categories
    this.enabledCategories = new Set(this.options.categories);
    
    const wsUrl = `${this.baseUrl}/ws`;

    this.socket = io(wsUrl, {
      transports: ['websocket'],
      autoConnect: true,
      reconnection: this.options.autoReconnect,
      reconnectionAttempts: this.options.reconnectionAttempts,
      reconnectionDelay: this.options.reconnectionDelay,
      reconnectionDelayMax: this.options.reconnectionDelayMax,
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
    
    this.reconnectAttempts = 0;
  }
  
  /**
   * Enable or disable event categories
   * @param categories Categories to enable or disable
   * @param enabled Whether to enable or disable the categories
   */
  setEventCategoriesEnabled(categories: EventCategory[], enabled: boolean): void {
    categories.forEach(category => {
      if (enabled) {
        this.enabledCategories.add(category);
      } else {
        this.enabledCategories.delete(category);
      }
    });
  }

  /**
   * Set up event listeners for the socket
   */
  private setupEventListeners(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.notifyConnectionHandlers();
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      this.isConnected = false;
      this.notifyConnectionHandlers();

      // Try to reconnect after a delay if auto-reconnect is enabled
      if (this.options.autoReconnect && !this.reconnectTimer && this.token) {
        if (this.reconnectAttempts < (this.options.reconnectionAttempts || 5)) {
          this.reconnectAttempts++;
          const delay = Math.min(
            (this.options.reconnectionDelay || 1000) * Math.pow(1.5, this.reconnectAttempts - 1),
            this.options.reconnectionDelayMax || 5000
          );
          
          console.log(`WebSocket reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
          
          this.reconnectTimer = window.setTimeout(() => {
            this.reconnectTimer = null;
            if (this.token) {
              this.connect(this.token, this.options);
            }
          }, delay);
        } else {
          console.error(`WebSocket reconnection failed after ${this.reconnectAttempts} attempts`);
        }
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
        // Create a WebSocketEvent object from the data
        const event: WebSocketEvent = {
          event_type: eventType,
          data,
          priority: data.priority as EventPriority,
          category: this.getCategoryFromEventType(eventType),
          timestamp: data.timestamp || new Date().toISOString()
        };
        
        // Only process events for enabled categories
        if (event.category && !this.enabledCategories.has(event.category)) {
          return;
        }
        
        // Call event-specific handlers
        handlers.forEach(handler => handler(data));
        
        // Call category handlers if applicable
        if (event.category && this.categoryHandlers.has(event.category)) {
          const categoryHandlers = this.categoryHandlers.get(event.category);
          categoryHandlers?.forEach(handler => handler(event));
        }
      });
    });
  }
  
  /**
   * Register a handler for events of a specific category
   * @param category Category to listen for
   * @param handler Handler function to call when an event of this category is received
   * @returns A function to unregister the handler
   */
  onCategory(category: EventCategory, handler: (event: WebSocketEvent) => void): () => void {
    if (!this.categoryHandlers.has(category)) {
      this.categoryHandlers.set(category, new Set());
    }
    
    const handlers = this.categoryHandlers.get(category)!;
    handlers.add(handler);
    
    // Return a function to remove the handler
    return () => {
      const handlers = this.categoryHandlers.get(category);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          this.categoryHandlers.delete(category);
        }
      }
    };
  }
  
  /**
   * Get the category for an event type based on naming conventions
   * @param eventType The event type string
   * @returns The category for the event type, or undefined if not recognized
   */
  private getCategoryFromEventType(eventType: string): EventCategory | undefined {
    if (eventType.startsWith('pipeline_')) {
      return EventCategory.PIPELINE;
    } else if (eventType.startsWith('security_')) {
      return EventCategory.SECURITY;
    } else if (eventType.startsWith('debug_')) {
      return EventCategory.DEBUG;
    } else if (eventType.startsWith('system_')) {
      return EventCategory.SYSTEM;
    } else if (eventType.startsWith('architecture_')) {
      return EventCategory.ARCHITECTURE;
    } else if (eventType.startsWith('user_')) {
      return EventCategory.USER;
    }
    return undefined;
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
