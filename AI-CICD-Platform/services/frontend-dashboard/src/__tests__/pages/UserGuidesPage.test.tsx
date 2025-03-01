import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import UserGuidesPage from '../../pages/user-guides/UserGuidesPage';

// Mock the setTimeout function
vi.useFakeTimers();

describe('UserGuidesPage', () => {
  it('renders loading state initially', () => {
    render(<UserGuidesPage />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders user guides content after loading', async () => {
    render(<UserGuidesPage />);
    
    // Fast-forward through the loading timeout
    vi.runAllTimers();
    
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });
    
    // Check for the main heading
    expect(screen.getByRole('heading', { name: /user guides/i, level: 4 })).toBeInTheDocument();
    
    // Check for the tabs
    expect(screen.getByRole('tab', { name: /getting started/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /pipelines/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /security/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /debugger/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /settings/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /api documentation/i })).toBeInTheDocument();
    
    // Check for the Getting Started content (default tab)
    expect(screen.getByText(/platform overview/i)).toBeInTheDocument();
    expect(screen.getByText(/key features/i)).toBeInTheDocument();
    expect(screen.getByText(/first steps/i)).toBeInTheDocument();
  });

  it('handles error state', async () => {
    // Mock useState to simulate an error
    const originalUseState = React.useState;
    const mockUseState = vi.spyOn(React, 'useState');
    
    // Mock the error state
    mockUseState.mockImplementationOnce(() => [false, vi.fn()]);  // loading state
    mockUseState.mockImplementationOnce(() => ['Test error', vi.fn()]);  // error state
    mockUseState.mockImplementationOnce(originalUseState);  // value state
    
    render(<UserGuidesPage />);
    
    // Check for the error message
    expect(screen.getByText('Test error')).toBeInTheDocument();
    
    // Restore the original useState
    mockUseState.mockRestore();
  });
});
