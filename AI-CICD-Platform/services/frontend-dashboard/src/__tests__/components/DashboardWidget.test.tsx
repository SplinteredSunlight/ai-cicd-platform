import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import DashboardWidget from '../../components/dashboard/DashboardWidget';
import { WidgetConfig } from '../../stores/dashboard.store';

describe('DashboardWidget', () => {
  const mockWidget: WidgetConfig = {
    id: 'test-widget',
    type: 'metrics-summary',
    title: 'Test Widget',
    size: { w: 6, h: 4 },
    position: { x: 0, y: 0 },
    settings: {},
    realtime: true,
  };

  const mockHandlers = {
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    onSettings: vi.fn(),
    onRefresh: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the widget with title', () => {
    render(
      <DashboardWidget
        widget={mockWidget}
        isEditMode={false}
        {...mockHandlers}
      >
        <div>Widget Content</div>
      </DashboardWidget>
    );

    expect(screen.getByText('Test Widget')).toBeInTheDocument();
    expect(screen.getByText('Widget Content')).toBeInTheDocument();
  });

  it('shows loading state when isLoading is true', () => {
    render(
      <DashboardWidget
        widget={mockWidget}
        isEditMode={false}
        isLoading={true}
        {...mockHandlers}
      >
        <div>Widget Content</div>
      </DashboardWidget>
    );

    // The CircularProgress component doesn't have text, so we check for the role
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    
    // Widget content should not be visible when loading
    expect(screen.queryByText('Widget Content')).not.toBeInTheDocument();
  });

  it('shows edit outline when in edit mode', () => {
    const { container } = render(
      <DashboardWidget
        widget={mockWidget}
        isEditMode={true}
        {...mockHandlers}
      >
        <div>Widget Content</div>
      </DashboardWidget>
    );

    // Check for the outline style (this is a bit of an implementation detail, but it's a way to test for the visual indicator)
    const card = container.querySelector('.MuiCard-root');
    expect(card).toHaveStyle('outline: 2px dashed #1976d2');
  });

  it('calls the appropriate handler when menu items are clicked', () => {
    render(
      <DashboardWidget
        widget={mockWidget}
        isEditMode={true}
        {...mockHandlers}
      >
        <div>Widget Content</div>
      </DashboardWidget>
    );

    // Open the menu
    fireEvent.click(screen.getByLabelText('widget menu'));

    // Click the refresh menu item
    fireEvent.click(screen.getByText('Refresh'));
    expect(mockHandlers.onRefresh).toHaveBeenCalledWith(mockWidget.id);

    // Open the menu again (it closes after each selection)
    fireEvent.click(screen.getByLabelText('widget menu'));

    // Click the settings menu item
    fireEvent.click(screen.getByText('Widget Settings'));
    expect(mockHandlers.onSettings).toHaveBeenCalledWith(mockWidget.id);

    // Open the menu again
    fireEvent.click(screen.getByLabelText('widget menu'));

    // Click the edit menu item
    fireEvent.click(screen.getByText('Edit'));
    expect(mockHandlers.onEdit).toHaveBeenCalledWith(mockWidget.id);

    // Open the menu again
    fireEvent.click(screen.getByLabelText('widget menu'));

    // Click the remove menu item
    fireEvent.click(screen.getByText('Remove'));
    expect(mockHandlers.onDelete).toHaveBeenCalledWith(mockWidget.id);
  });

  it('disables edit and delete options when not in edit mode', () => {
    render(
      <DashboardWidget
        widget={mockWidget}
        isEditMode={false}
        {...mockHandlers}
      >
        <div>Widget Content</div>
      </DashboardWidget>
    );

    // Open the menu
    fireEvent.click(screen.getByLabelText('widget menu'));

    // Check that Edit and Remove menu items are disabled
    const editMenuItem = screen.getByText('Edit').closest('li');
    const removeMenuItem = screen.getByText('Remove').closest('li');
    
    expect(editMenuItem).toHaveAttribute('aria-disabled', 'true');
    expect(removeMenuItem).toHaveAttribute('aria-disabled', 'true');
  });
});
