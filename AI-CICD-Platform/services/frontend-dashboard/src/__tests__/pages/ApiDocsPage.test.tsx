import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import ApiDocsPage from '../../pages/api-docs/ApiDocsPage';

// Mock the SwaggerUI component since it's complex and not necessary to test its internals
vi.mock('swagger-ui-react', () => ({
  default: () => <div data-testid="swagger-ui">Swagger UI Component</div>,
}));

// Mock the CSS import
vi.mock('swagger-ui-react/swagger-ui.css', () => ({}));

describe('ApiDocsPage', () => {
  beforeEach(() => {
    // Mock setTimeout to execute immediately
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders loading state initially', () => {
    render(<ApiDocsPage />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders API documentation after loading', async () => {
    render(<ApiDocsPage />);
    
    // Fast-forward timers to skip loading state
    vi.runAllTimers();
    
    await waitFor(() => {
      expect(screen.getByText('API Documentation')).toBeInTheDocument();
    });
    
    // Check that tabs are rendered
    expect(screen.getByText('REST API')).toBeInTheDocument();
    expect(screen.getByText('WebSocket Events')).toBeInTheDocument();
    expect(screen.getByText('Authentication')).toBeInTheDocument();
    
    // Initially, the REST API tab should be active and show Swagger UI
    expect(screen.getByTestId('swagger-ui')).toBeInTheDocument();
  });

  it('displays WebSocket events documentation when tab is clicked', async () => {
    render(<ApiDocsPage />);
    
    // Fast-forward timers to skip loading state
    vi.runAllTimers();
    
    await waitFor(() => {
      expect(screen.getByText('API Documentation')).toBeInTheDocument();
    });
    
    // Click on the WebSocket Events tab
    const websocketTab = screen.getByText('WebSocket Events');
    websocketTab.click();
    
    // Check that WebSocket events documentation is displayed
    expect(screen.getByText('WebSocket Events', { selector: 'h5' })).toBeInTheDocument();
    expect(screen.getByText('The AI CI/CD Platform uses WebSockets for real-time updates.')).toBeInTheDocument();
    
    // Check that at least one event is displayed
    expect(screen.getByText('debug_session_created')).toBeInTheDocument();
  });

  it('displays Authentication documentation when tab is clicked', async () => {
    render(<ApiDocsPage />);
    
    // Fast-forward timers to skip loading state
    vi.runAllTimers();
    
    await waitFor(() => {
      expect(screen.getByText('API Documentation')).toBeInTheDocument();
    });
    
    // Click on the Authentication tab
    const authTab = screen.getByText('Authentication');
    authTab.click();
    
    // Check that Authentication documentation is displayed
    expect(screen.getByText('Authentication', { selector: 'h5' })).toBeInTheDocument();
    expect(screen.getByText('The AI CI/CD Platform uses JWT (JSON Web Tokens) for authentication.')).toBeInTheDocument();
    
    // Check that authentication sections are displayed
    expect(screen.getByText('Obtaining a Token')).toBeInTheDocument();
    expect(screen.getByText('Using the Token')).toBeInTheDocument();
    expect(screen.getByText('Token Expiration')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
    expect(screen.getByText('Example Authentication Flow')).toBeInTheDocument();
  });
});
