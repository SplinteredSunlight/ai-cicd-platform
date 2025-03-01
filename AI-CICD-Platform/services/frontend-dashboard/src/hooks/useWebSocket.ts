import { useEffect, useState, useCallback, useMemo } from 'react';
import websocketService, { 
  WebSocketEvent, 
  EventCategory, 
  EventPriority,
  WebSocketOptions
} from '../services/websocket.service';

/**
 * Hook for managing WebSocket connection
 * @param token Authentication token
 * @param options WebSocket connection options
 * @returns Connection state and methods
 */
export function useWebSocketConnection(
  token: string | null, 
  options: WebSocketOptions = {}
) {
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    if (!token) return;
    
    // Connect to WebSocket server
    websocketService.connect(token, options);
    
    // Set up connection state handler
    const unsubscribe = websocketService.onConnectionChange(setIsConnected);
    
    // Clean up on unmount
    return () => {
      unsubscribe();
      websocketService.disconnect();
    };
  }, [token, options]);
  
  const setEventCategoriesEnabled = useCallback(
    (categories: EventCategory[], enabled: boolean) => {
      websocketService.setEventCategoriesEnabled(categories, enabled);
    },
    []
  );
  
  return {
    isConnected,
    setEventCategoriesEnabled
  };
}

/**
 * Hook for subscribing to a specific WebSocket event
 * @param eventType Event type to subscribe to
 * @returns Latest event data and loading state
 */
export function useWebSocketEvent<T = any>(eventType: string) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  
  useEffect(() => {
    setIsLoading(true);
    setError(null);
    
    // Subscribe to the event
    const unsubscribe = websocketService.on(eventType, (eventData) => {
      try {
        setData(eventData as T);
        setLastUpdated(new Date());
        setIsLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
        setIsLoading(false);
      }
    });
    
    // Clean up on unmount or when eventType changes
    return unsubscribe;
  }, [eventType]);
  
  return {
    data,
    isLoading,
    error,
    lastUpdated
  };
}

/**
 * Hook for subscribing to events of a specific category
 * @param category Event category to subscribe to
 * @returns Array of events and methods
 */
export function useWebSocketCategory(category: EventCategory) {
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const [maxEvents, setMaxEvents] = useState(50);
  
  // Add a new event to the list, maintaining the max length
  const addEvent = useCallback((event: WebSocketEvent) => {
    setEvents(prevEvents => {
      const newEvents = [event, ...prevEvents];
      if (newEvents.length > maxEvents) {
        return newEvents.slice(0, maxEvents);
      }
      return newEvents;
    });
  }, [maxEvents]);
  
  // Clear all events
  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);
  
  // Set the maximum number of events to keep
  const setMaxEventCount = useCallback((count: number) => {
    setMaxEvents(count);
    setEvents(prevEvents => prevEvents.slice(0, count));
  }, []);
  
  // Subscribe to events of the specified category
  useEffect(() => {
    const unsubscribe = websocketService.onCategory(category, addEvent);
    
    return unsubscribe;
  }, [category, addEvent]);
  
  // Filter events by priority
  const getEventsByPriority = useCallback((priority: EventPriority) => {
    return events.filter(event => event.priority === priority);
  }, [events]);
  
  return {
    events,
    highPriorityEvents: useMemo(() => getEventsByPriority(EventPriority.HIGH), [getEventsByPriority]),
    mediumPriorityEvents: useMemo(() => getEventsByPriority(EventPriority.MEDIUM), [getEventsByPriority]),
    lowPriorityEvents: useMemo(() => getEventsByPriority(EventPriority.LOW), [getEventsByPriority]),
    clearEvents,
    setMaxEventCount
  };
}

/**
 * Hook for subscribing to all WebSocket events
 * @param options Options for filtering and managing events
 * @returns Events grouped by category and methods
 */
export function useWebSocketEvents(options: {
  maxEvents?: number;
  categories?: EventCategory[];
} = {}) {
  const { maxEvents = 100, categories = Object.values(EventCategory) } = options;
  
  // State for all events
  const [allEvents, setAllEvents] = useState<WebSocketEvent[]>([]);
  
  // Add a new event to the list, maintaining the max length
  const addEvent = useCallback((event: WebSocketEvent) => {
    setAllEvents(prevEvents => {
      const newEvents = [event, ...prevEvents];
      if (newEvents.length > maxEvents) {
        return newEvents.slice(0, maxEvents);
      }
      return newEvents;
    });
  }, [maxEvents]);
  
  // Clear all events
  const clearEvents = useCallback(() => {
    setAllEvents([]);
  }, []);
  
  // Subscribe to events of all specified categories
  useEffect(() => {
    const unsubscribes = categories.map(category => 
      websocketService.onCategory(category, addEvent)
    );
    
    return () => {
      unsubscribes.forEach(unsubscribe => unsubscribe());
    };
  }, [categories, addEvent]);
  
  // Group events by category
  const eventsByCategory = useMemo(() => {
    const grouped: Record<EventCategory, WebSocketEvent[]> = {} as Record<EventCategory, WebSocketEvent[]>;
    
    // Initialize empty arrays for all categories
    categories.forEach(category => {
      grouped[category] = [];
    });
    
    // Group events by category
    allEvents.forEach(event => {
      if (event.category && categories.includes(event.category)) {
        grouped[event.category].push(event);
      }
    });
    
    return grouped;
  }, [allEvents, categories]);
  
  return {
    allEvents,
    eventsByCategory,
    clearEvents
  };
}
