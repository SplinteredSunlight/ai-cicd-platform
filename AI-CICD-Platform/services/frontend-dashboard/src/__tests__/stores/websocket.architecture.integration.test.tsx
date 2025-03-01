import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import WebSocketService from '../../services/websocket.service';
import { useDashboardStore } from '../../stores/dashboard.store';
import ArchitectureDiagram from '../../components/visualizations/ArchitectureDiagram';

// Mock the WebSocketService
jest.mock('../../services/websocket.service', () => ({
  __esModule: true,
  default: {
    on: jest.fn(),
    isSocketConnected: jest.fn().mockReturnValue(true),
  },
}));

// Mock mermaid to avoid actual rendering in tests
jest.mock('mermaid', () => ({
  initialize: jest.fn(),
  run: jest.fn().mockImplementation(() => Promise.resolve()),
}));

describe('WebSocket Architecture Diagram Integration', () => {
  const mockWidgetId = 'architecture-diagram-1';
  
  // Sample architecture diagram data
  const mockDiagramData = {
    diagrams: [
      {
        id: 'system-diagram',
        name: 'System Overview',
        description: 'High-level system architecture',
        definition: 'graph TD; A-->B; B-->C; C-->D;',
        type: 'system',
        lastUpdated: new Date().toISOString(),
      }
    ],
    currentService: 'api-gateway',
    lastUpdated: new Date().toISOString(),
  };

  // Updated diagram data that would come from WebSocket
  const updatedDiagramData = {
    diagrams: [
      {
        id: 'system-diagram',
        name: 'System Overview',
        description: 'High-level system architecture',
        definition: 'graph TD; A-->B; B-->C; C-->D;',
        type: 'system',
        lastUpdated: new Date().toISOString(),
      },
      {
        id: 'service-diagram',
        name: 'Service Architecture',
        description: 'Detailed service architecture',
        definition: 'graph TD; X-->Y; Y-->Z;',
        type: 'service',
        lastUpdated: new Date().toISOString(),
      }
    ],
    currentService: 'api-gateway',
    lastUpdated: new Date().toISOString(),
  };

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Create a mock element for the SVG content
    const mockSvg = document.createElement('svg');
    mockSvg.setAttribute('width', '100%');
    mockSvg.setAttribute('height', '100%');
    
    // Mock the querySelector to return our mock SVG
    document.querySelector = jest.fn().mockImplementation(() => mockSvg);
    
    // Set up the initial state in the store
    act(() => {
      useDashboardStore.setState({
        widgetData: {
          [mockWidgetId]: {
            data: mockDiagramData,
            timestamp: new Date().toISOString(),
          },
        },
      });
    });
  });

  it('should update architecture diagram when receiving WebSocket event', async () => {
    // Set up the WebSocket event handler mock
    let websocketCallback: (data: any) => void;
    (WebSocketService.on as jest.Mock).mockImplementation((event, callback) => {
      if (event === 'architecture_diagram_update') {
        websocketCallback = callback;
      }
      return jest.fn(); // Return a cleanup function
    });

    // Render the component with the initial data
    const { rerender } = render(
      <ArchitectureDiagram 
        data={useDashboardStore.getState().widgetData[mockWidgetId]?.data || { diagrams: [] }} 
      />
    );

    // Verify initial state
    await waitFor(() => {
      expect(screen.getByText('System Overview')).toBeInTheDocument();
      expect(screen.queryByText('Service Architecture')).not.toBeInTheDocument();
    });

    // Simulate receiving a WebSocket event
    act(() => {
      websocketCallback({
        widgetId: mockWidgetId,
        data: updatedDiagramData,
      });
    });

    // Update the store with the new data
    act(() => {
      useDashboardStore.setState({
        widgetData: {
          [mockWidgetId]: {
            data: updatedDiagramData,
            timestamp: new Date().toISOString(),
          },
        },
      });
    });

    // Re-render with the updated data
    rerender(
      <ArchitectureDiagram 
        data={useDashboardStore.getState().widgetData[mockWidgetId]?.data || { diagrams: [] }} 
      />
    );

    // Verify the component updated with the new data
    await waitFor(() => {
      expect(screen.getByText('System Overview')).toBeInTheDocument();
      expect(screen.getByText('Service Architecture')).toBeInTheDocument();
    });
  });

  it('should handle WebSocket connection status changes', async () => {
    // Mock the connection status handler
    let connectionCallback: (connected: boolean) => void;
    WebSocketService.onConnectionChange = jest.fn().mockImplementation((callback) => {
      connectionCallback = callback;
      return jest.fn(); // Return a cleanup function
    });

    // Render the component
    render(
      <ArchitectureDiagram 
        data={useDashboardStore.getState().widgetData[mockWidgetId]?.data || { diagrams: [] }} 
      />
    );

    // Verify initial state
    await waitFor(() => {
      expect(screen.getByText('System Overview')).toBeInTheDocument();
    });

    // Simulate WebSocket disconnection
    act(() => {
      (WebSocketService.isSocketConnected as jest.Mock).mockReturnValue(false);
      if (connectionCallback) connectionCallback(false);
    });

    // Simulate WebSocket reconnection
    act(() => {
      (WebSocketService.isSocketConnected as jest.Mock).mockReturnValue(true);
      if (connectionCallback) connectionCallback(true);
    });

    // Component should still be functioning
    expect(screen.getByText('System Overview')).toBeInTheDocument();
  });
});
