import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import DeveloperGuidesPage from '../../pages/developer-guides/DeveloperGuidesPage';

// Mock the setTimeout function
vi.useFakeTimers();

describe('DeveloperGuidesPage', () => {
  it('renders loading state initially', () => {
    render(<DeveloperGuidesPage />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders developer guides content after loading', async () => {
    render(<DeveloperGuidesPage />);
    
    // Fast-forward through the loading timeout
    vi.runAllTimers();
    
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });
    
    // Check for the main heading
    expect(screen.getByRole('heading', { name: /developer guides/i, level: 4 })).toBeInTheDocument();
    
    // Check for the tabs
    expect(screen.getByRole('tab', { name: /getting started/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /frontend development/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /backend development/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /database integration/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /testing/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /ci\/cd pipeline/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /cli tools/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /architecture/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /contributing/i })).toBeInTheDocument();
    
    // Check for the Getting Started content (default tab)
    expect(screen.getByText(/development environment setup/i)).toBeInTheDocument();
    expect(screen.getByText(/project structure/i)).toBeInTheDocument();
    expect(screen.getByText(/development workflow/i)).toBeInTheDocument();
  });

  it('handles error state', async () => {
    // Mock useState to simulate an error
    const originalUseState = React.useState;
    const mockUseState = vi.spyOn(React, 'useState');
    
    // Mock the error state
    mockUseState.mockImplementationOnce(() => [false, vi.fn()]);  // loading state
    mockUseState.mockImplementationOnce(() => ['Test error', vi.fn()]);  // error state
    mockUseState.mockImplementationOnce(originalUseState);  // value state
    
    render(<DeveloperGuidesPage />);
    
    // Check for the error message
    expect(screen.getByText('Test error')).toBeInTheDocument();
    
    // Restore the original useState
    mockUseState.mockRestore();
  });
});
