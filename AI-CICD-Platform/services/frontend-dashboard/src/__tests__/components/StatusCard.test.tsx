import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, test, expect } from 'vitest';
import StatusCard from '../../pages/dashboard/components/StatusCard';

describe('StatusCard Component', () => {
  test('renders with title and value', () => {
    render(
      <StatusCard 
        title="Test Title" 
        value={100} 
        change={5}
        unit="%" 
      />
    );
    
    expect(screen.getByText('Test Title')).toBeDefined();
    expect(screen.getByText('100')).toBeDefined();
    expect(screen.getByText('+5%')).toBeDefined();
  });

  test('renders negative change correctly', () => {
    render(
      <StatusCard 
        title="Test Title" 
        value={100} 
        change={-10}
        subtitle="vs last month" 
      />
    );
    
    expect(screen.getByText('Test Title')).toBeDefined();
    expect(screen.getByText('100')).toBeDefined();
    expect(screen.getByText('-10%')).toBeDefined();
    expect(screen.getByText('vs last month')).toBeDefined();
  });
});
