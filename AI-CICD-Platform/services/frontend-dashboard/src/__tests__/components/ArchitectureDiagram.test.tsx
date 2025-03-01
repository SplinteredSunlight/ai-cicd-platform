import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import ArchitectureDiagram, { DiagramData } from '../../components/visualizations/ArchitectureDiagram';
import '@testing-library/jest-dom';

// Mock mermaid to avoid actual rendering in tests
jest.mock('mermaid', () => ({
  initialize: jest.fn(),
  run: jest.fn().mockImplementation(() => Promise.resolve()),
}));

describe('ArchitectureDiagram Component', () => {
  const mockDiagrams: DiagramData[] = [
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
    },
  ];

  const mockData = {
    diagrams: mockDiagrams,
    currentService: 'api-gateway',
    lastUpdated: new Date().toISOString(),
  };

  beforeEach(() => {
    // Create a mock element for the SVG content
    const mockSvg = document.createElement('svg');
    mockSvg.setAttribute('width', '100%');
    mockSvg.setAttribute('height', '100%');
    
    // Mock the querySelector to return our mock SVG
    document.querySelector = jest.fn().mockImplementation(() => mockSvg);
  });

  it('renders loading state correctly', () => {
    render(<ArchitectureDiagram data={mockData} isLoading={true} />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders empty state when no diagrams are available', () => {
    render(<ArchitectureDiagram data={{ diagrams: [] }} />);
    expect(screen.getByText(/No architecture diagrams available/i)).toBeInTheDocument();
  });

  it('renders tabs when multiple diagrams are available', async () => {
    render(<ArchitectureDiagram data={mockData} />);
    
    await waitFor(() => {
      expect(screen.getByText('System Overview')).toBeInTheDocument();
      expect(screen.getByText('Service Architecture')).toBeInTheDocument();
    });
  });

  it('renders diagram description when available', async () => {
    render(<ArchitectureDiagram data={mockData} />);
    
    await waitFor(() => {
      expect(screen.getByText('High-level system architecture')).toBeInTheDocument();
    });
  });

  it('renders last updated timestamp when available', async () => {
    render(<ArchitectureDiagram data={mockData} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
    });
  });

  it('handles error state correctly', async () => {
    // Mock an error during rendering
    jest.spyOn(console, 'error').mockImplementation(() => {});
    document.body.appendChild = jest.fn().mockImplementation(() => {
      throw new Error('Mermaid rendering error');
    });

    render(<ArchitectureDiagram data={mockData} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Error rendering diagram/)).toBeInTheDocument();
    });

    // Restore console.error
    (console.error as jest.Mock).mockRestore();
  });
});
